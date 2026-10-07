"""storelib: the store client behind `kit-games store ...`.

A "store" here is a signed catalog snapshot (catalog/v1) that a publisher puts somewhere (a folder, a web
address). The kit downloads it, checks it against a publisher key YOU pinned, lists what is in it and, for the
free games it offers, downloads them into the library. Commercial games appear only as guide entries: where to
dump or buy your own copy, never a file.

Trust model (nothing here is trust-on-first-use):
  * ~/.config/omarchy-kit/store-publisher.pem is the publisher's ECDSA P-256 public key, put there by you.
    Without it, `refresh` refuses to run.
  * A snapshot is `version.json` + `catalog.sqlite.zst`. The catalog's SHA-256 must match `version.json`, the
    ECDSA signature over the catalog bytes must verify with the pinned key (openssl dgst -sha256 -verify),
    and the signed catalog's own meta table must agree with `version.json` (version.json itself is not signed).
  * Versions only go forward. An entry leaves a snapshot only through a tombstone; a snapshot that silently
    drops entries is refused unless you pass --accept-drops.
  * Every downloaded file is checked against the snapshot's size, SHA-256 and SHA-1; a mismatch deletes it.
  * Network use: the configured snapshot source, and the artifact addresses inside a verified snapshot.
    Nothing else, no telemetry, nothing is uploaded.
  * Your own backups (personallib): folders you register are scanned and recognised on this device only. A
    commercial game you hold a recognised backup of shows "In your backups" and installs from that folder with no
    network use at all. Locations and personal.sqlite are never exported, shared or sent anywhere.

Standard library only; signatures are checked with the `openssl` command line tool.
"""
import base64, calendar, hashlib, json, os, re, shutil, sqlite3, subprocess, tempfile, time, tomllib, urllib.error, urllib.parse, urllib.request, zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from compression import zstd

import personallib as pl

CLIENT_VERSION = "0.1.0"          # this client's version; a snapshot's minClient may not exceed it
SCHEMA = 1
MAX_VERSION_BYTES = 64 * 1024
MAX_CATALOG_BYTES = 512 * 1024 * 1024
MAX_DECOMPRESSED = 512 * 1024 * 1024
MAX_EXTRACTED = 8 * 1024 ** 3
STALE_DAYS = 30
KEEP_NAMES = {"mame", "arcade"}   # arcade sets only work under their exact file names
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
MODES = ("host", "link", "guide")
KINDS = ("homebrew", "freeware", "demo", "commercial", "tool")
GB = 1e9


class StoreError(Exception):
    """A problem worth showing to the user as it is."""


class DroppedEntries(StoreError):
    def __init__(self, dropped, message):
        super().__init__(message)
        self.dropped = dropped


def human(b):
    return f"{b / GB:.1f} GB" if b >= GB else f"{b / 1e6:.0f} MB" if b >= 1e6 else f"{b / 1e3:.0f} KB" if b >= 1e3 else f"{b} B"


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def semver(s):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(s))
    if not m:
        raise StoreError(f"not a version number: {s!r}")
    return tuple(int(x) for x in m.groups())


def safe_name(title):
    """File-system safe name; same replacements as kit-games' thumb_name, plus control characters."""
    s = re.sub(r'[&*/:`<>?\\|"\x00-\x1f]', "_", title)
    return s.strip(" .")[:150] or "untitled"


# ---------------------------------------------------------------- network / sources
def allowed_url(url):
    p = urllib.parse.urlparse(url)
    return p.scheme == "https" or (p.scheme == "http" and (p.hostname or "") in LOOPBACK)


class _NoDowngrade(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl):
            raise StoreError(f"refusing a redirect to {newurl} (only https is accepted)")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_url(url, timeout=60):
    if not allowed_url(url):
        raise StoreError(f"refusing {url}: only https addresses are used (plain http only for localhost)")
    opener = urllib.request.build_opener(_NoDowngrade)
    try:
        return opener.open(urllib.request.Request(url, headers={"User-Agent": "omarchy-kit"}), timeout=timeout)
    except urllib.error.HTTPError as e:
        raise StoreError(f"{url} answered {e.code}") from None
    except urllib.error.URLError as e:
        raise StoreError(f"could not reach {url}: {e.reason}") from None
    except OSError as e:
        raise StoreError(f"could not reach {url}: {e}") from None


def _stream(src, dest, max_bytes, hashers=()):
    """Copy a readable to `dest`, refusing more than max_bytes. Returns the byte count."""
    total = 0
    with open(dest, "wb") as out:
        while True:
            chunk = src.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise StoreError(f"download is larger than the expected {human(max_bytes)}")
            for h in hashers:
                h.update(chunk)
            out.write(chunk)
    return total


def _local_path(source, name):
    s = source[len("file://"):] if source.startswith("file://") else source
    p = Path(os.path.expanduser(s))
    if p.is_file():
        p = p.parent
    return p / name


def read_source_file(source, name, dest=None, max_bytes=MAX_VERSION_BYTES):
    """Fetch `name` ('version.json' or 'catalog.sqlite.zst') from a folder, a file:// path or a web address.
    Returns the bytes, or, with `dest`, writes there and returns the byte count."""
    if re.match(r"https?://", source):
        resp = _open_url(source.rstrip("/") + "/" + name)
        with resp:
            if dest is not None:
                return _stream(resp, dest, max_bytes)
            data = resp.read(max_bytes + 1)
    else:
        p = _local_path(source, name)
        try:
            if dest is not None:
                with open(p, "rb") as f:
                    return _stream(f, dest, max_bytes)
            data = p.read_bytes()[: max_bytes + 1]
        except FileNotFoundError:
            raise StoreError(f"{p} does not exist") from None
        except OSError as e:
            raise StoreError(f"could not read {p}: {e}") from None
    if len(data) > max_bytes:
        raise StoreError(f"{name} is larger than {human(max_bytes)}")
    return data


# ---------------------------------------------------------------- publisher key and signatures
def _openssl(*args, timeout=30):
    try:
        return subprocess.run(["openssl", *args], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise StoreError("the `openssl` command is needed to verify signatures and was not found") from None


def check_publisher_key(key_path):
    key_path = Path(key_path)
    if not key_path.exists():
        raise StoreError(f"no publisher key at {key_path}.\n"
                         "  The store trusts only a publisher key you put there yourself (a public key, PEM). "
                         "Ask the publisher for it and check it with them before saving it.")
    try:
        text = key_path.read_text(errors="replace")
    except OSError as e:
        raise StoreError(f"could not read {key_path}: {e}") from None
    if "PRIVATE KEY" in text:
        raise StoreError(f"{key_path} contains a private key. The store only needs the publisher's PUBLIC key: "
                         "remove the private half from this machine and save the public key instead")
    r = _openssl("pkey", "-pubin", "-in", str(key_path), "-noout", "-text")
    if r.returncode != 0:
        raise StoreError(f"{key_path} is not a public key in PEM form")
    if not re.search(r"prime256v1|P-256", r.stdout):
        raise StoreError(f"{key_path} must be an ECDSA P-256 public key")


def verify_signature(file_path, signature_b64, key_path):
    try:
        sig = base64.b64decode(signature_b64, validate=True)
    except Exception:
        raise StoreError("the signature in version.json is not valid base64") from None
    with tempfile.TemporaryDirectory() as d:
        sf = Path(d) / "sig.bin"
        sf.write_bytes(sig)
        r = _openssl("dgst", "-sha256", "-verify", str(key_path), "-signature", str(sf), str(file_path))
    if r.returncode != 0 or "Verified OK" not in r.stdout:
        raise StoreError("the signature does not verify with your pinned publisher key: refusing this snapshot "
                         "(wrong key, or the file was changed)")


# ---------------------------------------------------------------- snapshot
VERSION_FIELDS = ("schema", "version", "createdAt", "entries", "tombstones", "sha256", "signature", "minClient")


def parse_version(data):
    try:
        v = json.loads(data)
    except Exception:
        raise StoreError("version.json is not valid JSON") from None
    if not isinstance(v, dict):
        raise StoreError("version.json is not an object")
    missing = [k for k in VERSION_FIELDS if k not in v]
    if missing:
        raise StoreError(f"version.json lacks: {', '.join(missing)}")
    if v["schema"] != SCHEMA:
        raise StoreError(f"catalog schema {v['schema']!r} is not supported by this client (it reads schema {SCHEMA})")
    if not (isinstance(v["version"], str) and re.fullmatch(r"\d{10}", v["version"])):
        raise StoreError("version.json: version must be 10 digits (YYYYMMDDNN)")
    if not (isinstance(v["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", v["sha256"])):
        raise StoreError("version.json: sha256 is not a SHA-256 digest")
    for k in ("entries", "tombstones"):
        if not (isinstance(v[k], int) and not isinstance(v[k], bool) and v[k] >= 0):
            raise StoreError(f"version.json: {k} must be a non-negative integer")
    if not (isinstance(v["signature"], str) and v["signature"]):
        raise StoreError("version.json: signature is missing")
    if not (isinstance(v["createdAt"], str) and v["createdAt"]):
        raise StoreError("version.json: createdAt is missing")
    semver(v["minClient"])
    return v


def validate_entry(e):
    """The rules the publisher's own schema enforces, checked again here: a signed snapshot that breaks
    them is refused as a whole."""
    def bad(msg):
        raise StoreError(f"the snapshot is malformed: entry {e.get('id', '?') if isinstance(e, dict) else '?'}: {msg}")
    if not isinstance(e, dict):
        bad("not an object")
    for k in ("id", "slug", "title", "platformKey"):
        if not (isinstance(e.get(k), str) and e[k]):
            bad(f"{k} is missing")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", e["slug"]):
        bad("bad slug")
    if e.get("kind") not in KINDS:
        bad(f"unknown kind {e.get('kind')!r}")
    if e.get("mode") not in MODES:
        bad(f"unknown mode {e.get('mode')!r}")
    if not isinstance(e.get("credits", []), list) or not isinstance(e.get("routes", []), list):
        bad("credits/routes must be lists")
    if e["mode"] == "guide":
        if e.get("artifact"):
            bad("guide entries never carry a file")
        for r in e.get("routes", []):
            if not (isinstance(r, dict) and r.get("kind") in ("dump", "buy") and isinstance(r.get("url"), str)):
                bad("bad route")
        return
    if e["kind"] == "commercial":
        bad("commercial games are guide-only")
    lic, art = e.get("license"), e.get("artifact")
    if not isinstance(lic, dict) or not lic.get("attribution") or not lic.get("evidenceUrl"):
        bad("host/link entries need license evidence")
    if not isinstance(art, dict):
        bad("host/link entries need an artifact")
    if not (isinstance(art.get("size"), int) and not isinstance(art.get("size"), bool) and art["size"] > 0):
        bad("artifact size must be a positive integer")
    if not (isinstance(art.get("sha1"), str) and re.fullmatch(r"[0-9a-f]{40}", art["sha1"])):
        bad("artifact sha1 is not a SHA-1 digest")
    if not (isinstance(art.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", art["sha256"])):
        bad("artifact sha256 is not a SHA-256 digest")
    fn = art.get("filename")
    if not (isinstance(fn, str) and fn and "/" not in fn and "\\" not in fn and not fn.startswith(".") and "\x00" not in fn):
        bad("artifact filename is not a plain file name")
    if not (isinstance(art.get("format"), str) and art["format"]):
        bad("artifact format is missing")
    if not (isinstance(art.get("url"), str) and allowed_url(art["url"])):
        bad("artifact address is not https")


@dataclass
class Snapshot:
    version: dict
    entries: list
    tombstones: list
    by_id: dict = field(default_factory=dict)
    tomb_ids: set = field(default_factory=set)

    def __post_init__(self):
        self.by_id = {e["id"]: e for e in self.entries}
        self.tomb_ids = {t["id"] for t in self.tombstones}


def load_snapshot(version_bytes, catalog_path, key_path, client_version=CLIENT_VERSION):
    """Verify and open a snapshot. Raises StoreError, naming the first check that failed."""
    v = parse_version(version_bytes)
    check_publisher_key(key_path)
    catalog_path = Path(catalog_path)
    h = hashlib.sha256()
    with open(catalog_path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    if h.hexdigest() != v["sha256"]:
        raise StoreError("sha256 mismatch: the catalog file does not match version.json (corrupted or tampered): refusing it")
    verify_signature(catalog_path, v["signature"], key_path)
    if semver(v["minClient"]) > semver(client_version):
        raise StoreError(f"this snapshot needs store client {v['minClient']} or newer (this is {client_version})")
    try:
        dec = zstd.ZstdDecompressor()
        raw = dec.decompress(catalog_path.read_bytes(), max_length=MAX_DECOMPRESSED + 1)
    except Exception as e:
        raise StoreError(f"the catalog is not valid zstd data ({e})") from None
    if len(raw) > MAX_DECOMPRESSED:
        raise StoreError(f"the catalog expands to more than {human(MAX_DECOMPRESSED)}: refusing it")
    if not dec.eof:
        raise StoreError("the catalog is truncated (incomplete zstd data)")
    con = sqlite3.connect(":memory:")
    try:
        con.deserialize(raw)
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        rows = con.execute("SELECT id, json FROM entries ORDER BY id").fetchall()
        tombs = con.execute("SELECT id, removed_at, reason FROM tombstones ORDER BY id").fetchall()
    except sqlite3.Error as e:
        raise StoreError(f"the catalog is not a valid catalog database ({e})") from None
    finally:
        con.close()
    # version.json is not signed; the signed catalog says what it is, and the two must agree.
    for key, want in (("schema", str(SCHEMA)), ("version", v["version"]), ("createdAt", v["createdAt"])):
        if meta.get(key) != want:
            raise StoreError(f"version.json says {key} {want!r} but the signed catalog says {meta.get(key)!r}: refusing it")
    if len(rows) != v["entries"] or len(tombs) != v["tombstones"]:
        raise StoreError(f"row counts differ from version.json (entries {len(rows)}/{v['entries']}, tombstones {len(tombs)}/{v['tombstones']})")
    entries = []
    for rid, js in rows:
        try:
            e = json.loads(js)
        except Exception:
            raise StoreError(f"the snapshot is malformed: entry {rid} is not JSON") from None
        validate_entry(e)
        if e["id"] != rid:
            raise StoreError(f"the snapshot is malformed: entry key {rid} differs from its id {e['id']}")
        entries.append(e)
    tombstones = [{"id": a, "removedAt": b, "reason": c} for a, b, c in tombs]
    return Snapshot(v, entries, tombstones)


class SnapshotCache:
    """snapshots/<version>/ directories with `current` and `previous` symlinks; swapping a symlink is atomic."""

    def __init__(self, root):
        self.root = Path(root)

    def _target(self, name):
        link = self.root / name
        try:
            t = (self.root / os.readlink(link)).resolve()
        except OSError:
            return None
        return t if (t / "version.json").exists() and (t / "catalog.sqlite.zst").exists() else None

    def current_dir(self):
        return self._target("current")

    def current_version(self):
        d = self.current_dir()
        if not d:
            return None
        try:
            return json.loads((d / "version.json").read_text()).get("version")
        except Exception:
            return None

    def _point(self, name, target_name):
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.root / f".{name}.{os.getpid()}.tmp"
        tmp.unlink(missing_ok=True)
        os.symlink(target_name, tmp)
        os.replace(tmp, self.root / name)

    def install(self, version_bytes, catalog_path, version):
        snaps = self.root / "snapshots"
        snaps.mkdir(parents=True, exist_ok=True)
        dest = snaps / version
        stage = snaps / f".{version}.{os.getpid()}.new"
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir()
        (stage / "version.json").write_bytes(version_bytes)
        shutil.copyfile(catalog_path, stage / "catalog.sqlite.zst")
        old = self.current_dir()
        shutil.rmtree(dest, ignore_errors=True)
        os.replace(stage, dest)
        if old and old.resolve() != dest.resolve():
            self._point("previous", f"snapshots/{old.name}")
        self._point("current", f"snapshots/{version}")
        keep = {version, old.name if old else None}
        for d in snaps.iterdir():
            if d.is_dir() and d.name not in keep and not d.name.startswith("."):
                shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- the store
class Store:
    def __init__(self, *, games, roms, key_path, config_path, systems, budget_check=None, budget_info=None,
                 free_bytes=None, after_change=None, log=print, client_version=CLIENT_VERSION, now=time.time,
                 locations_path=None, rdb_dir=None, mounts=None):
        """systems: {libretro db name: {"folder": ..., "exts": [...]}}.
        budget_check(extra_bytes) -> None when the library still fits, else a sentence.
        after_change(folders) runs the kit's scan/ES-DE steps; it is not called by the single-item methods."""
        self.games, self.roms = Path(games), Path(roms)
        self.key_path, self.config_path = Path(key_path), Path(config_path)
        self.systems = systems
        self.budget_check = budget_check or (lambda extra: None)
        self.budget_info = budget_info or (lambda: None)
        self.free_bytes = free_bytes or (lambda: shutil.disk_usage(self.games).free)
        self.after_change = after_change or (lambda folders: None)
        self.log, self.client_version, self.now = log, client_version, now
        self.cache = SnapshotCache(self.games / ".cache" / "store")
        self.manifest_path = self.games / ".kit-store.json"
        # your own backups: local configuration and a local database, nothing else
        self.locations_path = Path(locations_path) if locations_path else self.config_path.with_name("store-locations.json")
        self.personal_path = self.cache.root / "personal.sqlite"
        self.rdb_dir = Path(rdb_dir) if rdb_dir else pl.DEFAULT_RDB_DIR
        self.mounts = mounts

    # ---- configuration and the cached snapshot
    def source(self, override=None):
        if override:
            return override
        try:
            src = tomllib.loads(self.config_path.read_text()).get("store", {}).get("source")
        except FileNotFoundError:
            src = None
        except Exception as e:
            raise StoreError(f"could not read {self.config_path}: {e}") from None
        if not src:
            raise StoreError(f"no snapshot source: pass --from <folder or https address>, or set\n"
                             f"  [store]\n  source = \"https://…\"\nin {self.config_path}")
        return src

    def current(self):
        """The cached snapshot, verified again on every load; None before the first refresh."""
        d = self.cache.current_dir()
        if not d:
            return None
        return load_snapshot((d / "version.json").read_bytes(), d / "catalog.sqlite.zst", self.key_path, self.client_version)

    def require(self):
        snap = self.current()
        if snap is None:
            raise StoreError("no catalog snapshot yet: run `kit-games store refresh --from <source>`")
        return snap

    # ---- manifest of what this store installed
    def manifest(self):
        try:
            return json.loads(self.manifest_path.read_text())
        except FileNotFoundError:
            return {}
        except Exception:
            raise StoreError(f"{self.manifest_path} is not valid JSON; fix or remove it") from None

    def _save_manifest(self, m):
        tmp = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        tmp.write_text(json.dumps(m, indent=1, ensure_ascii=False))
        os.replace(tmp, self.manifest_path)

    # ---- refresh
    def refresh(self, source=None, accept_drops=False):
        src = self.source(source)
        check_publisher_key(self.key_path)
        vbytes = read_source_file(src, "version.json")
        v = parse_version(vbytes)
        have = self.cache.current_version()
        if have:
            if v["version"] < have:
                raise StoreError(f"refusing to go backwards: the source offers {v['version']} but {have} is installed")
            if v["version"] == have:
                cur = json.loads((self.cache.current_dir() / "version.json").read_text())
                if cur.get("sha256") == v["sha256"]:
                    return {"status": "current", "version": have}
                raise StoreError(f"the source offers a different catalog under the same version number {have}: refusing it")
        old = None
        if have:
            try:
                old = self.current()
            except StoreError as e:
                self.log(f"WARNING: the cached snapshot no longer verifies ({e}); the check for dropped entries is skipped.")
        stage = Path(tempfile.mkdtemp(prefix="incoming-", dir=self._ensure(self.cache.root)))
        try:
            catalog = stage / "catalog.sqlite.zst"
            read_source_file(src, "catalog.sqlite.zst", dest=catalog, max_bytes=MAX_CATALOG_BYTES)
            new = load_snapshot(vbytes, catalog, self.key_path, self.client_version)
            dropped = []
            if old:
                dropped = sorted(set(old.by_id) - set(new.by_id) - new.tomb_ids)
            if dropped and not accept_drops:
                names = ", ".join(f"{old.by_id[i]['title']} ({i})" for i in dropped[:8]) + (" …" if len(dropped) > 8 else "")
                raise DroppedEntries(dropped, f"the new snapshot {new.version['version']} removes {len(dropped)} entries without a tombstone "
                                              f"({names}). Entries may only leave through tombstones. Keeping {have}; "
                                              "pass --accept-drops only if you trust this snapshot anyway.")
            self.cache.install(vbytes, catalog, v["version"])
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        if dropped:
            self.log(f"WARNING: accepted {len(dropped)} entries dropped without a tombstone (--accept-drops).")
        added = sorted(set(new.by_id) - set(old.by_id)) if old else sorted(new.by_id)
        return {"status": "updated", "version": v["version"], "previous": have, "entries": len(new.entries),
                "tombstones": len(new.tombstones), "added": len(added), "dropped": dropped}

    @staticmethod
    def _ensure(p):
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---- browsing
    def folder_of(self, platform_key):
        s = self.systems.get(platform_key)
        return s["folder"] if s else None

    def _platform_match(self, e, platform):
        if not platform:
            return True
        p, key = platform.lower(), e["platformKey"].lower()
        return p == key or p == (self.folder_of(e["platformKey"]) or "").lower() or p in key

    def list_entries(self, snap, platform=None, mode=None):
        out = [e for e in snap.entries if self._platform_match(e, platform) and (not mode or e["mode"] == mode)]
        return sorted(out, key=lambda e: (e["platformKey"], e["title"].lower()))

    def search(self, snap, query):
        q = query.lower().strip()
        def hit(e):
            hay = [e["title"], e["slug"], e["id"], *(c.get("name", "") for c in e.get("credits", []))]
            return any(q in h.lower() for h in hay)
        return sorted((e for e in snap.entries if hit(e)), key=lambda e: (e["platformKey"], e["title"].lower()))

    def resolve(self, snap, ref, platform=None):
        if ref in snap.by_id:
            return snap.by_id[ref]
        r = ref.lower()
        pool = [e for e in snap.entries if self._platform_match(e, platform)]
        found = [e for e in pool if e["slug"] == r] or [e for e in pool if e["title"].lower() == r]
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            opts = "; ".join(f"{e['id']} ({e['platformKey']})" for e in found[:6])
            raise StoreError(f"{ref!r} matches several entries: use an id, or --platform. {opts}")
        near = self.search(snap, ref)[:5]
        hint = ("  Did you mean: " + ", ".join(e["slug"] for e in near)) if near else ""
        raise StoreError(f"nothing named {ref!r} in this catalog.{hint}")

    def list_lines(self, entries, backup_ids=()):
        installed = self.manifest()
        lines = []
        for e in entries:
            mark = "✓" if e["id"] in installed else " "
            lic = (e.get("license") or {}).get("spdx") or ((e.get("license") or {}).get("kind") or "")
            if e["id"] in backup_ids:
                lic = "In your backups"
            lines.append(f"{mark} {e['slug']:<38.38} {e['mode']:<5} {e['platformKey']:<42.42} {lic}")
        return lines

    def info_lines(self, e, groups=()):
        out = [f"{e['title']}  [{e['id']}]", f"  slug       {e['slug']}", f"  platform   {e['platformKey']}   kind: {e['kind']}   mode: {e['mode']}"]
        art, lic = e.get("artifact"), e.get("license")
        if lic:
            out += [f"  license    {lic.get('spdx') or lic.get('kind')}  ({lic.get('kind')})",
                    f"  evidence   {lic['evidenceUrl']}", f"  credit     {lic['attribution']}"]
        for c in e.get("credits", []):
            out.append(f"  {c.get('role', 'credit'):<10} {c['name']}" + (f"  {c['url']}" if c.get("url") else ""))
        if art:
            out += [f"  file       {art['filename']}  ({art['format']}, {human(art['size'])})", f"  sha256     {art['sha256']}",
                    f"  sha1       {art['sha1']}", f"  source     {art['url']}"]
            if e["mode"] == "link":
                out.append("  note       link mode: the file comes from its source's own site, not from the store.")
        if e["mode"] == "guide" and groups:
            out.append("  In your backups: you hold a recognised copy of this game (it was not downloaded, and the store offers no file).")
            for i, g in enumerate(groups, 1):
                locs = sorted({r["location"] for r in g["items"]})
                out.append(f"  backup {i:<3}  {g['name']}  ({len(g['items'])} file{'s' if len(g['items']) != 1 else ''} in {', '.join(Path(x).name for x in locs)})")
            out.append(f"  install    kit-games store get {e['slug']}" + (" --which N" if len(groups) > 1 else "") + "   (copies it from your folder; --link makes a link instead)")
        elif e["mode"] == "guide":
            out.append("  No file is offered for this title: it is a commercial game. The store lists where to dump or buy your own copy.")
            for r in e.get("routes", []):
                out.append(f"  {r['kind']:<10} {r.get('label', '')}  {r['url']}")
        inst = self.manifest().get(e["id"])
        if inst:
            out.append(f"  installed  {inst['installedAt']}: {', '.join(inst['files'][:3])}{' …' if len(inst['files']) > 3 else ''}")
        return out

    # ---- get
    def get(self, ref, platform=None, which=None, link=False):
        snap = self.require()
        e = self.resolve(snap, ref, platform)
        if e["mode"] == "guide":
            groups = self.backup_groups(snap).get(e["id"])
            if groups:
                return self._install_personal(e, snap, groups, which, link)
            routes = "".join(f"\n  {r['kind']}: {r.get('label', '')} {r['url']}" for r in e.get("routes", []))
            raise StoreError(f"{e['title']} is a commercial game: the store never offers a file for it. "
                             f"It lists where to dump or buy your own copy.{routes}\n"
                             "  If you already own a backup of it, register its folder (`store locations add`) and run `store scan`.")
        art = e["artifact"]
        system = self.systems.get(e["platformKey"])
        if not system:
            raise StoreError(f"this library has no folder for {e['platformKey']} (see games/systems.toml), so {e['title']} cannot be installed")
        manifest = self.manifest()
        have = manifest.get(e["id"])
        if have and have["sha256"] == art["sha256"] and all((self.roms / f).exists() for f in have["files"]):
            return {"status": "already", "entry": e, "files": have["files"]}
        problem = self.budget_check(art["size"])
        if problem:
            raise StoreError(f"not downloading {e['title']}: {problem}")
        free = self.free_bytes()
        if free < art["size"] * 2 + 100 * 1024 * 1024:
            raise StoreError(f"not downloading {e['title']}: only {human(free)} of disk is free")
        part = self._ensure(self.cache.root / "downloads") / (hashlib.sha1(e["id"].encode()).hexdigest() + ".part")
        try:
            h1, h2 = hashlib.sha1(), hashlib.sha256()
            with _open_url(art["url"], timeout=120) as resp:
                n = _stream(resp, part, art["size"], (h1, h2))
            if n != art["size"]:
                raise StoreError(f"{e['title']}: downloaded {n} bytes, the catalog says {art['size']}: deleted")
            if h2.hexdigest() != art["sha256"] or h1.hexdigest() != art["sha1"]:
                raise StoreError(f"{e['title']}: the file does not match the catalog's checksums: deleted, nothing installed")
            files = self._place(e, system, part, manifest)
        except StoreError:
            raise
        except OSError as ex:
            raise StoreError(f"{e['title']}: {ex}") from None
        finally:
            part.unlink(missing_ok=True)
        if have:  # an update: drop files the new version no longer has
            for f in set(have["files"]) - set(files):
                (self.roms / f).unlink(missing_ok=True)
        lic = e["license"]
        manifest[e["id"]] = {
            "id": e["id"], "slug": e["slug"], "title": e["title"], "platformKey": e["platformKey"], "folder": system["folder"],
            "mode": e["mode"], "snapshot": snap.version["version"], "files": files, "size": art["size"], "sha1": art["sha1"],
            "sha256": art["sha256"], "sourceUrl": art["url"], "license": {"spdx": lic.get("spdx"), "kind": lic.get("kind"), "evidenceUrl": lic["evidenceUrl"]},
            "attribution": lic["attribution"], "credits": e.get("credits", []),
            "installedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(self.now())),
        }
        self._save_manifest(manifest)
        self._write_credits(system["folder"], manifest)
        return {"status": "installed", "entry": e, "files": files, "folder": system["folder"]}

    def _owned(self, rel, ident, manifest):
        return rel in manifest.get(ident, {}).get("files", [])

    def _place(self, e, system, part, manifest):
        art, folder, ident = e["artifact"], system["folder"], e["id"]
        dest_dir = self.roms / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        exts = {x.lower() for x in system["exts"]}
        fmt = art["format"].lower().lstrip(".")
        base = safe_name(e["title"])
        if fmt == "zip" and folder == "scummvm":
            return self._extract_scummvm(e, part, dest_dir, base, manifest)
        if fmt == "zip" and "zip" not in exts:
            return self._extract_matching(e, part, dest_dir, base, exts, manifest)
        if fmt not in exts:
            raise StoreError(f"{e['title']}: this system does not open .{fmt} files (it opens: {', '.join(sorted(exts))})")
        name = safe_name(Path(art["filename"]).name) if folder in KEEP_NAMES else f"{base}.{fmt}"
        out = dest_dir / name
        if out.exists() and not self._owned(f"{folder}/{out.name}", ident, manifest):
            if folder in KEEP_NAMES:
                raise StoreError(f"{folder}/{out.name} already exists and was not installed by the store; not overwriting it")
            out = dest_dir / f"{base} [{e['slug']}].{fmt}"
            if out.exists() and not self._owned(f"{folder}/{out.name}", ident, manifest):
                raise StoreError(f"{folder}/{out.name} already exists and was not installed by the store; not overwriting it")
        tmp = out.with_name("." + out.name + ".part")
        shutil.move(str(part), tmp)
        os.replace(tmp, out)
        return [f"{folder}/{out.name}"]

    def _zip_members(self, zf):
        infos = [i for i in zf.infolist() if not i.is_dir()]
        for i in infos:
            p = PurePosixPath(i.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in i.filename or "\x00" in i.filename:
                raise StoreError(f"the archive contains an unsafe path ({i.filename!r}): nothing installed")
        total = sum(i.file_size for i in infos)
        if total > MAX_EXTRACTED:
            raise StoreError(f"the archive expands to {human(total)}: nothing installed")
        return infos, total

    def _extract_matching(self, e, part, dest_dir, base, exts, manifest):
        folder, ident, files = dest_dir.name, e["id"], []
        with zipfile.ZipFile(part) as zf:
            infos, total = self._zip_members(zf)
            infos = [i for i in infos if PurePosixPath(i.filename).suffix.lower().lstrip(".") in exts]
            if not infos:
                raise StoreError(f"{e['title']}: the archive has nothing this system opens ({', '.join(sorted(exts))})")
            extracted = sum(i.file_size for i in infos)
            problem = self.budget_check(extracted - e["artifact"]["size"]) if extracted > e["artifact"]["size"] else None
            if problem:
                raise StoreError(f"not installing {e['title']}: {problem}")
            for i in infos:
                name = safe_name(PurePosixPath(i.filename).name) if len(infos) > 1 else f"{base}{PurePosixPath(i.filename).suffix.lower()}"
                out = dest_dir / name
                if out.exists() and not self._owned(f"{folder}/{out.name}", ident, manifest):
                    raise StoreError(f"{folder}/{out.name} already exists and was not installed by the store; not overwriting it")
                tmp = out.with_name("." + out.name + ".part")
                with zf.open(i) as src, open(tmp, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.replace(tmp, out)
                files.append(f"{folder}/{out.name}")
        return files

    def _extract_scummvm(self, e, part, dest_dir, base, manifest):
        gid = e["id"].split(":", 1)[1] if ":" in e["id"] else ""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", gid):
            raise StoreError(f"{e['title']}: cannot tell which ScummVM game id this is (entry id {e['id']!r})")
        folder, ident = dest_dir.name, e["id"]
        root = dest_dir / base
        owned = any(f.startswith(f"{folder}/{base}/") for f in manifest.get(ident, {}).get("files", []))
        if root.exists() and not owned:
            root = dest_dir / f"{base} [{e['slug']}]"
            if root.exists() and not any(f.startswith(f"{folder}/{root.name}/") for f in manifest.get(ident, {}).get("files", [])):
                raise StoreError(f"{folder}/{root.name} already exists and was not installed by the store; not touching it")
        files, created = [], not root.exists()
        try:
            with zipfile.ZipFile(part) as zf:
                infos, total = self._zip_members(zf)
                if total > e["artifact"]["size"]:
                    problem = self.budget_check(total - e["artifact"]["size"])
                    if problem:
                        raise StoreError(f"not installing {e['title']}: {problem}")
                names = [PurePosixPath(i.filename).parts for i in infos]
                strip = 1 if names and all(len(p) > 1 for p in names) and len({p[0] for p in names}) == 1 else 0
                for i in infos:
                    rel = PurePosixPath(*PurePosixPath(i.filename).parts[strip:])
                    out = root / rel
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(i) as src, open(out, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    files.append(f"{folder}/{root.name}/{rel.as_posix()}")
            launcher = root / f"{gid}.scummvm"
            launcher.write_text(gid)
            files.append(f"{folder}/{root.name}/{gid}.scummvm")
        except BaseException:
            if created:
                shutil.rmtree(root, ignore_errors=True)
            raise
        return files

    # ---- remove / sync
    def remove(self, ref):
        manifest = self.manifest()
        key = ref if ref in manifest else next((k for k, m in manifest.items() if ref.lower() in (m["slug"], m["title"].lower())), None)
        if key is None:
            raise StoreError(f"{ref!r} was not installed by the store")
        return self._remove_key(key, manifest)

    def _remove_key(self, key, manifest):
        rec = manifest[key]
        roms = self.roms.resolve()
        for rel in rec["files"]:
            p = (self.roms / rel)
            real = p.parent.resolve() / p.name
            if roms not in real.parents:  # never touch anything outside the library
                continue
            p.unlink(missing_ok=True)
            parent = p.parent
            while parent != self.roms / rec["folder"] and (self.roms / rec["folder"]) in parent.parents:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        del manifest[key]
        self._save_manifest(manifest)
        self._write_credits(rec["folder"], manifest)
        return rec

    def sync(self):
        """Apply tombstones from the current snapshot to what is installed. Returns (removed records, notes)."""
        snap = self.require()
        manifest = self.manifest()
        removed, notes = [], []
        tomb = {t["id"]: t for t in snap.tombstones}
        for key in list(manifest):
            if key in tomb and manifest[key].get("source") == "personal":
                notes.append(f"{manifest[key]['title']} was withdrawn from the catalog, but you installed it from your own backup, so it stays.")
            elif key in tomb:
                rec = self._remove_key(key, manifest)
                removed.append((rec, tomb[key]["reason"]))
            elif key not in snap.by_id:
                notes.append(f"{manifest[key]['title']} ({key}) is no longer listed in the catalog and has no tombstone; left installed.")
            elif snap.by_id[key]["mode"] != "guide" and snap.by_id[key]["artifact"]["sha256"] != manifest[key]["sha256"]:
                notes.append(f"{manifest[key]['title']}: a newer file is available (kit-games store get {manifest[key]['slug']}).")
        return removed, notes

    def _write_credits(self, folder, manifest):
        path = self.roms / folder / "STORE-CREDITS.md"
        rows = sorted((m for m in manifest.values() if m["folder"] == folder and m.get("source") != "personal"), key=lambda m: m["title"].lower())
        if not rows:
            path.unlink(missing_ok=True)
            return
        lines = [f"# Store credits ({folder})", "", "Games installed from the catalog snapshot by `kit-games store`, with the license each was admitted under.", ""]
        for m in rows:
            people = ", ".join(c["name"] for c in m["credits"]) or "unknown"
            lic = m["license"].get("spdx") or m["license"].get("kind")
            lines.append(f"- **{m['title']}** by {people} · license: {lic} · {m['attribution']} · evidence: {m['license']['evidenceUrl']} · source: {m['sourceUrl']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n")

    # ---- batch helpers that run the kit's scan/ES-DE steps once
    def get_many(self, refs, platform=None, which=None, link=False):
        results, folders = [], set()
        for ref in refs:
            try:
                r = self.get(ref, platform, which, link)
                results.append((ref, r, None))
                if r["status"] == "installed":
                    folders.add(r["folder"])
            except StoreError as e:
                results.append((ref, None, str(e)))
        if folders:
            self.after_change(folders)
        return results

    def remove_many(self, refs):
        results, folders = [], set()
        for ref in refs:
            try:
                rec = self.remove(ref)
                results.append((ref, rec, None))
                folders.add(rec["folder"])
            except StoreError as e:
                results.append((ref, None, str(e)))
        if folders:
            self.after_change(folders)
        return results

    def sync_and_apply(self):
        removed, notes = self.sync()
        if removed:
            self.after_change({r["folder"] for r, _ in removed})
        return removed, notes

    # ---- your own backups (ADR 0006 on the client): local configuration, local scan, local database
    def locations(self):
        return pl.Locations(self.locations_path)

    def add_location(self, raw, label=None):
        try:
            return self.locations().add(raw, label, mounts=self.mounts, library_dirs=[self.roms, self.cache.root], now=self.now)
        except pl.PersonalError as e:
            raise StoreError(str(e)) from None

    def remove_location(self, raw):
        """Forget a location and every row recognised from it. The files themselves are never touched."""
        try:
            loc = self.locations().remove(raw)
            rows = pl.PersonalDB(self.personal_path).forget_location(loc["path"])
        except pl.PersonalError as e:
            raise StoreError(str(e)) from None
        return loc, rows

    def _guide_keys(self, snap):
        by_key, by_igdb = {}, {}
        for e in snap.entries:
            if e["mode"] != "guide":
                continue
            by_key.setdefault((e["platformKey"], pl.norm_title(e["title"])), []).append(e)
            if isinstance(e.get("igdbId"), int):
                by_igdb.setdefault((e["platformKey"], e["igdbId"]), []).append(e)
        return by_key, by_igdb

    def _igdb_lookup(self):
        """db, canonical name -> the IGDB id of the one catalog guide entry it matches, else None."""
        try:
            snap = self.current()
        except StoreError:
            snap = None
        if snap is None:
            return None
        by_key, _ = self._guide_keys(snap)
        def lookup(db, name):
            cands = by_key.get((db, pl.norm_title(name))) or []
            return cands[0]["igdbId"] if len(cands) == 1 and isinstance(cands[0].get("igdbId"), int) else None
        return lookup

    def personal_db(self):
        return pl.PersonalDB(self.personal_path)

    def scan_backups(self, only=None):
        """Recognise the files in your locations against the libretro databases on this machine. On demand only."""
        locs = self.locations().all()
        if not locs:
            raise StoreError("no locations yet: add the folder that holds your backups with `kit-games store locations add <folder>`")
        if only and not any(only in (x["path"], x.get("label")) for x in locs):
            raise StoreError(f"{only!r} is not one of your locations (see `store locations list`)")
        index = pl.RdbIndex(self.rdb_dir)
        exts_by_db = {db: {x.lower() for x in s["exts"]} for db, s in self.systems.items()}
        loaded = [db for db in exts_by_db if index.add_db(db)]
        if not loaded:
            raise StoreError(f"no libretro databases for this library's systems in {self.rdb_dir} (is libretro-database installed?)")
        exts_by_db = {db: exts_by_db[db] for db in loaded}
        try:
            return pl.scan_locations(self.personal_path, locs, index, exts_by_db, self._igdb_lookup(), log=self.log, now=self.now, only=only)
        except pl.PersonalError as e:
            raise StoreError(str(e)) from None

    def backup_groups(self, snap):
        """{guide entry id: [{"name", "platform", "items": [rows]}]} for commercial games you hold a recognised copy of.

        Matching is by IGDB id when the scan found one, else by platform plus the title without its dump tags.
        An entry or a title that is not unique is left unmatched: nothing is guessed."""
        try:
            rows = pl.PersonalDB(self.personal_path).identified()
        except pl.PersonalError:
            return {}
        if not rows:
            return {}
        by_key, by_igdb = self._guide_keys(snap)
        found = {}
        for r in rows:
            cands = by_igdb.get((r["platform_key"], r["igdb_id"])) if r["igdb_id"] else None
            if not cands or len(cands) != 1:
                cands = by_key.get((r["platform_key"], r["match_key"]))
            if not cands or len(cands) != 1:
                continue
            found.setdefault(cands[0]["id"], {}).setdefault(r["canonical_name"], []).append(r)
        return {eid: [{"name": n, "platform": rs[0]["platform_key"], "items": rs} for n, rs in sorted(g.items())] for eid, g in found.items()}

    def _verify_backup(self, row):
        """The file must still be the dump that was recognised: same size, same hashes. Otherwise rescan."""
        p = Path(row["path"])
        try:
            st = p.stat()
        except OSError:
            raise StoreError(f"{p} is gone or its drive is not mounted: mount it and run `store scan`") from None
        if row["member"]:
            one = pl.zip_single_member(p)
            if not one:
                raise StoreError(f"{p} changed since the last scan: run `store scan`")
            got = pl.zip_member_variants(p, one[0], one[1])
        else:
            got = pl.file_variants(p, p.suffix.lower().lstrip("."), st.st_size)
        if not any(v[1] == row["sha1"] for v in got):
            raise StoreError(f"{p} changed since the last scan (its checksum no longer matches): run `store scan`")

    def _pick_group(self, e, groups, which):
        if len(groups) == 1 and which is None:
            return groups[0]
        listing = "".join(f"\n  {i}. {g['name']}" for i, g in enumerate(groups, 1))
        if which is None:
            raise StoreError(f"{e['title']}: several different dumps are in your backups, and the store will not pick one for you:{listing}\n"
                             "  choose with --which N")
        if str(which).isdigit() and 1 <= int(which) <= len(groups):
            return groups[int(which) - 1]
        hit = [g for g in groups if str(which).lower() in g["name"].lower()]
        if len(hit) == 1:
            return hit[0]
        raise StoreError(f"--which {which!r} does not pick exactly one of:{listing}")

    def _group_files(self, group):
        items = group["items"]
        sheets = [r for r in items if Path(r["path"]).suffix.lower() in pl.SHEET_EXTS]
        if sheets:
            if len(sheets) > 1:
                raise StoreError(f"{group['name']}: more than one disc sheet matches it; not guessing which to install")
            sheet = Path(sheets[0]["path"])
            return [sheet, *pl.disc_members(sheet)]
        if len(items) == 1:
            return [Path(items[0]["path"])]
        raise StoreError(f"{group['name']}: {len(items)} files match it but none is a disc sheet (.cue/.gdi), so the store cannot tell what to install")

    def _install_personal(self, e, snap, groups, which, link):
        system = self.systems.get(e["platformKey"])
        if not system:
            raise StoreError(f"this library has no folder for {e['platformKey']} (see games/systems.toml), so {e['title']} cannot be installed")
        group = self._pick_group(e, groups, which)
        manifest = self.manifest()
        have = manifest.get(e["id"])
        if have and have.get("source") == "personal" and have["files"] and all(os.path.lexists(self.roms / f) for f in have["files"]):
            return {"status": "already", "entry": e, "files": have["files"]}
        files = self._group_files(group)
        for r in group["items"]:
            self._verify_backup(r)
        folder, ident, exts = system["folder"], e["id"], {x.lower() for x in system["exts"]}
        primary_row = group["items"][0]
        extract = bool(primary_row["member"]) and "zip" not in exts and len(files) == 1
        if extract:
            with zipfile.ZipFile(files[0]) as zf:
                size = zf.getinfo(primary_row["member"]).file_size
        else:
            size = sum(f.stat().st_size for f in files)
        problem = self.budget_check(size)
        if problem:
            raise StoreError(f"not installing {e['title']}: {problem}")
        if not link and self.free_bytes() < size + 100 * 1024 * 1024:
            raise StoreError(f"not installing {e['title']}: only {human(self.free_bytes())} of disk is free")
        dest_dir = self.roms / folder
        base = re.sub(r'[&*/:`<>?\\|"]', "_", group["name"])
        plan = []   # (source, dest name)
        for i, f in enumerate(files):
            if i == 0:
                suffix = (Path(primary_row["member"]).suffix if extract else f.suffix).lower()
                plan.append((f, base + suffix))
            else:
                plan.append((f, f.name))   # tracks keep the names the sheet refers to
        owned = set(have["files"]) if have else set()
        for src, name in plan:
            out = dest_dir / name
            if os.path.lexists(out) and f"{folder}/{name}" not in owned:
                raise StoreError(f"{folder}/{name} already exists and was not installed by the store; not overwriting it")
        dest_dir.mkdir(parents=True, exist_ok=True)
        placed = []
        try:
            for src, name in plan:
                out = dest_dir / name
                tmp = out.with_name("." + out.name + ".part")
                tmp.unlink(missing_ok=True)
                if extract:
                    with zipfile.ZipFile(src) as zf, zf.open(primary_row["member"]) as m, open(tmp, "wb") as dst:
                        shutil.copyfileobj(m, dst)
                elif link:
                    os.symlink(src.resolve(), tmp)
                else:
                    shutil.copyfile(src, tmp)
                    if tmp.stat().st_size != src.stat().st_size:
                        raise StoreError(f"{name}: the copy is not the same size as the original; nothing installed")
                os.replace(tmp, out)
                placed.append(out)
        except BaseException:
            for out in placed:
                out.unlink(missing_ok=True)
            raise
        rels = [f"{folder}/{name}" for _, name in plan]
        manifest[e["id"]] = {
            "id": e["id"], "slug": e["slug"], "title": e["title"], "platformKey": e["platformKey"], "folder": folder, "mode": "guide",
            "source": "personal", "linked": bool(link and not extract), "canonicalName": group["name"], "snapshot": snap.version["version"],
            "files": rels, "size": size, "sha1": primary_row["sha1"], "sha256": None,
            "installedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(self.now())),
        }
        self._save_manifest(manifest)
        self._write_credits(folder, manifest)
        return {"status": "installed", "entry": e, "files": rels, "folder": folder, "source": "personal", "linked": bool(link and not extract)}

    # ---- health
    def health(self):
        out = {"key": self.key_path.exists(), "client": self.client_version, "source": None, "snapshot": None, "problem": None}
        try:
            out["source"] = self.source()
        except StoreError:
            pass
        try:
            snap = self.current()
        except StoreError as e:
            snap, out["problem"] = None, str(e)
        if snap:
            by_mode = {m: sum(1 for e in snap.entries if e["mode"] == m) for m in MODES}
            created = snap.version["createdAt"]
            try:
                age = (self.now() - calendar.timegm(time.strptime(created, "%Y-%m-%dT%H:%M:%SZ"))) / 86400
            except ValueError:
                age = None
            out["snapshot"] = {"version": snap.version["version"], "createdAt": created, "age_days": age, "entries": len(snap.entries),
                               "tombstones": len(snap.tombstones), "by_mode": by_mode, "stale": age is not None and age > STALE_DAYS}
        m = self.manifest()
        out["installed"] = len(m)
        out["installed_bytes"] = sum(r["size"] for r in m.values())
        out["budget"] = self.budget_info()
        try:
            n = pl.PersonalDB(self.personal_path).counts()
            out["backups"] = {"locations": len(self.locations().all()), **n}
        except pl.PersonalError:
            out["backups"] = {"locations": 0, "identified": 0, "unidentified": 0}
        return out

    def health_lines(self):
        h = self.health()
        out = [f"store client      {h['client']}",
               f"publisher key     {'pinned' if h['key'] else 'MISSING (put the publisher\'s public key in ' + str(self.key_path) + ')'}",
               f"snapshot source   {h['source'] or 'not configured (use --from, or set [store] source in ' + str(self.config_path) + ')'}"]
        s = h["snapshot"]
        if s:
            age = f"{s['age_days']:.0f} days old" if s["age_days"] is not None else "age unknown"
            out += [f"snapshot          {s['version']}  ({age}{', STALE: run refresh' if s['stale'] else ''})",
                    f"catalog           {s['entries']} entries (host {s['by_mode']['host']}, link {s['by_mode']['link']}, guide {s['by_mode']['guide']}), {s['tombstones']} tombstones"]
        else:
            out.append("snapshot          none yet" + (f" ({h['problem']})" if h["problem"] else ""))
        out.append(f"installed         {h['installed']} titles, {human(h['installed_bytes'])}")
        b2 = h["backups"]
        out.append(f"your backups      {b2['locations']} locations, {b2['identified']} recognised files, {b2['unidentified']} unidentified (counts only; nothing leaves this machine)")
        b = h["budget"]
        if b and b.get("cap"):
            out.append(f"library budget    {human(b['used'])} of {human(b['cap'])}")
        return out
