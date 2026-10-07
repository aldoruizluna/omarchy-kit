"""personallib: your own backups, found and recognised on this machine.

A *location* is a folder you control (a local folder, a removable drive, a share that is already mounted as a
path) where you keep backups of games you own. `scan` walks the locations on this device, hashes the files
(CRC32 and SHA-1) and recognises them against the libretro databases already installed for RetroArch. The
result is `personal.sqlite` next to the store cache. It is your data and it stays here:

  * This module opens no network connection and imports no network library. Paths, hashes and file lists are
    never sent anywhere; there is deliberately no export, import or share of locations or of personal.sqlite.
  * Files that match nothing are listed as unidentified. Nothing is guessed, and a hash that fits several
    platforms or several differently named dumps is reported as ambiguous rather than picked.
  * Only formats whose bytes equal the dump the database lists can be recognised: cartridge ROMs (also inside a
    single-file .zip), disc images as plain .iso/.bin/.cue/.gdi. Compressed containers (CHD, RVZ, 7z), multi-file
    arcade sets and anything modified stay unidentified. Disc serial numbers are not read here.

Standard library only.
"""
import hashlib, json, os, re, sqlite3, struct, time, zipfile, zlib
from pathlib import Path

SCHEMA = 1
DEFAULT_RDB_DIR = Path("/usr/share/libretro/database/rdb")
CHUNK = 1024 * 1024
MAX_ZIP_MEMBER = 8 * 1024 ** 3
# Containers whose bytes are not the dump's bytes: never hashed, always reported as unidentified.
OPAQUE_EXTS = {"chd", "rvz", "7z", "wia", "gcz", "cso", "ciso", "pbp"}
# Extra extensions worth hashing besides those the library's systems open.
DISC_EXTS = {"iso", "bin", "img", "cue", "gdi", "gcm", "mdf", "toc"}
SHEET_EXTS = {".cue", ".gdi"}
REFUSED_FSTYPES = {"httpdirfs", "fuse.httpdirfs", "curlftpfs", "fuse.curlftpfs", "ipfs", "fuse.ipfs"}
NETWORK_FSTYPES = {"cifs", "smb3", "smbfs", "nfs", "nfs4", "9p", "fuse.sshfs", "sshfs", "afs", "ceph", "glusterfs"}
FORBIDDEN_SCHEME_REASONS = {
    "http": "a web index is not storage you control", "https": "a web index is not storage you control",
    "ftp": "a public FTP index is not storage you control", "ftps": "a public FTP index is not storage you control",
    "magnet": "magnet links are not locations", "ipfs": "IPFS is not storage you control", "ed2k": "ed2k links are not locations",
}


class PersonalError(Exception):
    """A problem worth showing to the user as it is."""


def human(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1000 or unit == "TB":
            return f"{b:.0f} {unit}" if unit == "B" else f"{b:.1f} {unit}"
        b /= 1000


# ---------------------------------------------------------------- libretro .rdb (MessagePack records)
def _unpack(buf, pos):
    """One MessagePack value at buf[pos]; returns (value, next position). Only what .rdb files use."""
    b = buf[pos]
    pos += 1
    if b < 0x80:
        return b, pos
    if b >= 0xe0:
        return b - 256, pos
    if 0x80 <= b <= 0x8f:
        return _map(buf, pos, b & 0x0f)
    if 0x90 <= b <= 0x9f:
        return _array(buf, pos, b & 0x0f)
    if 0xa0 <= b <= 0xbf:
        n = b & 0x1f
        return buf[pos:pos + n].decode("utf-8", "replace"), pos + n
    if b == 0xc0:
        return None, pos
    if b == 0xc2:
        return False, pos
    if b == 0xc3:
        return True, pos
    if b in (0xc4, 0xc5, 0xc6):
        w = {0xc4: 1, 0xc5: 2, 0xc6: 4}[b]
        n = int.from_bytes(buf[pos:pos + w], "big")
        pos += w
        return bytes(buf[pos:pos + n]), pos + n
    if b == 0xca:
        return struct.unpack(">f", buf[pos:pos + 4])[0], pos + 4
    if b == 0xcb:
        return struct.unpack(">d", buf[pos:pos + 8])[0], pos + 8
    if 0xcc <= b <= 0xcf:
        w = 1 << (b - 0xcc)
        return int.from_bytes(buf[pos:pos + w], "big"), pos + w
    if 0xd0 <= b <= 0xd3:
        w = 1 << (b - 0xd0)
        return int.from_bytes(buf[pos:pos + w], "big", signed=True), pos + w
    if b in (0xd9, 0xda, 0xdb):
        w = {0xd9: 1, 0xda: 2, 0xdb: 4}[b]
        n = int.from_bytes(buf[pos:pos + w], "big")
        pos += w
        return buf[pos:pos + n].decode("utf-8", "replace"), pos + n
    if b in (0xdc, 0xdd):
        w = 2 if b == 0xdc else 4
        return _array(buf, pos + w, int.from_bytes(buf[pos:pos + w], "big"))
    if b in (0xde, 0xdf):
        w = 2 if b == 0xde else 4
        return _map(buf, pos + w, int.from_bytes(buf[pos:pos + w], "big"))
    raise PersonalError(f"unsupported MessagePack type 0x{b:02x}")


def _map(buf, pos, n):
    out = {}
    for _ in range(n):
        k, pos = _unpack(buf, pos)
        out[k], pos = _unpack(buf, pos)
    return out, pos


def _array(buf, pos, n):
    out = []
    for _ in range(n):
        v, pos = _unpack(buf, pos)
        out.append(v)
    return out, pos


def read_rdb(path):
    """Yield one dict per record of a libretro .rdb file (name, rom_name, size, crc, sha1, md5, serial, …)."""
    buf = Path(path).read_bytes()
    if buf[:8] != b"RARCHDB\x00" or len(buf) < 16:
        raise PersonalError(f"{path} is not a libretro database")
    end = struct.unpack(">Q", buf[8:16])[0]
    pos = 16
    while pos < end:
        rec, pos = _unpack(buf, pos)
        if isinstance(rec, dict):
            yield rec


class RdbIndex:
    """SHA-1 (and CRC32 + size, for records without a SHA-1) -> the database records that list that dump."""

    def __init__(self, rdb_dir=DEFAULT_RDB_DIR):
        self.rdb_dir = Path(rdb_dir)
        self.by_sha1, self.by_crc, self.loaded, self.records = {}, {}, [], 0

    def add_db(self, db):
        path = self.rdb_dir / f"{db}.rdb"
        if not path.exists():
            return False
        for r in read_rdb(path):
            if not isinstance(r.get("name"), str):
                continue
            rec = (db, r["name"], r.get("rom_name") or "", int(r.get("size") or 0), r.get("serial") or "")
            sha, crc = r.get("sha1"), r.get("crc")
            if isinstance(sha, bytes) and len(sha) == 20:
                self.by_sha1.setdefault(sha.hex(), []).append(rec)
            elif isinstance(crc, bytes) and len(crc) == 4:
                self.by_crc.setdefault((crc.hex(), rec[3]), []).append(rec)
            self.records += 1
        self.loaded.append(db)
        return True

    def lookup(self, sha1_hex, crc_hex, size):
        """The records that list a dump with these hashes: exact SHA-1, else CRC32 plus size."""
        return list(self.by_sha1.get(sha1_hex) or self.by_crc.get((crc_hex, size)) or [])


def identify(index, variants, exts_by_db, ext):
    """Decide what a file is from its hash variants [(crc_hex, sha1_hex, size), …].

    Returns (status, db, name, rom_name, serial, note). 'unidentified' with a note when nothing matches or when the
    match is not unique: a hash listed under two platforms (the extension must then single one out), or under two
    differently named dumps of one platform."""
    found = []
    for crc, sha1, size in variants:
        found = index.lookup(sha1, crc, size)
        if found:
            break
    if not found:
        return ("unidentified", None, None, None, None, "no database lists these hashes")
    dbs = sorted({r[0] for r in found})
    if len(dbs) > 1:
        fit = [d for d in dbs if ext in exts_by_db.get(d, ())]
        if len(fit) != 1:
            return ("unidentified", None, None, None, None, "these hashes are listed under several platforms: " + ", ".join(dbs))
        dbs = fit
    rows = [r for r in found if r[0] == dbs[0]]
    names = sorted({r[1] for r in rows})
    if len(names) > 1:
        return ("unidentified", None, None, None, None, f"these hashes are listed under {len(names)} differently named dumps of {dbs[0]}")
    r = rows[0]
    return ("identified", r[0], r[1], r[2], r[4] or None, None)


# ---------------------------------------------------------------- hashing
def hash_variants(read_chunks, size, ext, head):
    """[(crc32 hex, sha1 hex, size)] of the whole dump and of the dump without a copier/emulator header.

    Libretro's NES, SNES, Atari 7800 and Lynx databases hash the dump without the header some tools prepend, so
    a headered file is also hashed from after it. `read_chunks` yields the file's bytes in order."""
    skips = [0]
    if ext == "nes" and head[:4] == b"NES\x1a":
        skips.append(16)
    elif ext in ("smc", "swc", "fig") and size % 1024 == 512:
        skips.append(512)
    elif ext == "a78" and head[1:10] == b"ATARI7800":
        skips.append(128)
    elif ext == "lnx" and head[:4] == b"LYNX":
        skips.append(64)
    state = [[0, hashlib.sha1()] for _ in skips]
    pos = 0
    for chunk in read_chunks:
        for i, s in enumerate(skips):
            if pos + len(chunk) <= s:
                continue
            part = chunk[max(0, s - pos):]
            state[i][0] = zlib.crc32(part, state[i][0])
            state[i][1].update(part)
        pos += len(chunk)
    return [(f"{crc & 0xffffffff:08x}", h.hexdigest(), max(0, pos - s)) for (crc, h), s in zip(state, skips)]


def _file_chunks(path):
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            yield chunk


def file_variants(path, ext, size):
    with open(path, "rb") as f:
        head = f.read(16)
    return hash_variants(_file_chunks(path), size, ext, head)


def zip_single_member(path):
    """(ZipInfo, bytes of its first 16) when the archive holds exactly one file, else None."""
    try:
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if len(infos) != 1 or infos[0].file_size > MAX_ZIP_MEMBER:
                return None
            with zf.open(infos[0]) as m:
                return infos[0], m.read(16)
    except (zipfile.BadZipFile, OSError, NotImplementedError, RuntimeError):
        return None


def zip_member_variants(path, info, head):
    ext = Path(info.filename).suffix.lower().lstrip(".")
    def chunks():
        with zipfile.ZipFile(path) as zf, zf.open(info) as m:
            while chunk := m.read(CHUNK):
                yield chunk
    return hash_variants(chunks(), info.file_size, ext, head)


def disc_members(sheet):
    """The track files a .cue/.gdi sheet names that exist next to it, so they move together."""
    sheet = Path(sheet)
    out = []
    try:
        text = sheet.read_text(errors="ignore")
    except OSError:
        return out
    for line in text.splitlines():
        m = re.search(r'FILE\s+"([^"]+)"', line)
        if not m and sheet.suffix.lower() == ".gdi":
            m = re.match(r"\s*\d+\s+\d+\s+\d+\s+\d+\s+(\S+)", line)
        if m and (sheet.parent / m[1]).is_file():
            out.append(sheet.parent / m[1])
    return out


# ---------------------------------------------------------------- locations (local configuration only)
def read_mounts(path="/proc/mounts"):
    """[(mount point, fstype)] from /proc/mounts, longest mount point first."""
    out = []
    try:
        for line in Path(path).read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                mp = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), parts[1])
                out.append((mp, parts[2]))
    except OSError:
        pass
    return sorted(out, key=lambda t: -len(t[0]))


def check_location(raw, mounts=None, library_dirs=()):
    """Validate a location string; returns {"path", "kind"} or raises PersonalError.

    Accepted: an absolute (or ~) path to a folder on this machine, including removable drives and network shares
    that are already mounted as paths. Refused: every URL scheme (remote WebDAV/S3 with credentials is not built in
    this version), magnet/torrent/ed2k/ipfs, web or FTP indexes (also when mounted as a filesystem), single files."""
    text = (raw or "").strip()
    if not text:
        raise PersonalError("empty location")
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.\-]*):", text)
    if m and not text.startswith(("/", "~")):
        scheme = m[1].lower()
        why = FORBIDDEN_SCHEME_REASONS.get(scheme)
        if why:
            raise PersonalError(f"{scheme}: locations are refused ({why})")
        raise PersonalError(f"{scheme}: locations are not supported in this version: give the folder's path "
                            f"(mount a share first); remote storage with credentials is not built")
    if re.search(r"\.torrent$", text, re.I):
        raise PersonalError("torrent files are not locations")
    if not text.startswith(("/", "~")):
        raise PersonalError("a location is an absolute path to a folder (for example /mnt/backups or ~/Backups)")
    p = Path(text).expanduser()
    try:
        p = p.resolve(strict=True)
    except OSError:
        raise PersonalError(f"{text}: no such folder (is the drive mounted?)") from None
    if not p.is_dir():
        raise PersonalError(f"{p} is not a folder: a location is a folder that holds your backups")
    if p == Path("/") or p == Path.home().resolve():
        raise PersonalError(f"{p} is too broad to scan: pick the folder that holds your backups")
    for d in library_dirs:
        d = Path(d).resolve()
        if p == d or d in p.parents:
            raise PersonalError(f"{p} is inside the kit's own library; point at your backups folder instead "
                                "(`kit-games scan` covers the library itself)")
    kind, fstype = "local", ""
    for mp, fs in (mounts if mounts is not None else read_mounts()):
        if p == Path(mp) or Path(mp) in p.parents:
            fstype = fs
            break
    if fstype in REFUSED_FSTYPES:
        raise PersonalError(f"{p} is a mounted web/FTP/IPFS index ({fstype}), not storage you control")
    if fstype in NETWORK_FSTYPES:
        kind = "network"
    elif str(p).startswith(("/run/media/", "/media/")):
        kind = "removable"
    return {"path": str(p), "kind": kind}


class Locations:
    """~/.config/omarchy-kit/store-locations.json: the user's backup folders. Local configuration, never shared."""

    def __init__(self, path):
        self.path = Path(path)

    def all(self):
        try:
            data = json.loads(self.path.read_text())
        except FileNotFoundError:
            return []
        except Exception:
            raise PersonalError(f"{self.path} is not valid JSON; fix or remove it") from None
        return [x for x in data.get("locations", []) if isinstance(x, dict) and x.get("path")]

    def _save(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps({"version": 1, "locations": items}, indent=1, ensure_ascii=False))
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def add(self, raw, label=None, mounts=None, library_dirs=(), now=time.time):
        loc = check_location(raw, mounts, library_dirs)
        items = self.all()
        for x in items:
            if x["path"] == loc["path"]:
                raise PersonalError(f"{loc['path']} is already a location")
            if loc["path"].startswith(x["path"].rstrip("/") + "/") or x["path"].startswith(loc["path"].rstrip("/") + "/"):
                raise PersonalError(f"{loc['path']} overlaps the location {x['path']}: files would be counted twice")
        loc["label"] = label or Path(loc["path"]).name or loc["path"]
        loc["added"] = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now()))
        items.append(loc)
        self._save(items)
        return loc

    def remove(self, raw):
        text = str(Path(raw).expanduser()) if raw.startswith(("/", "~")) else raw
        try:
            text = str(Path(text).resolve())
        except OSError:
            pass
        items = self.all()
        keep = [x for x in items if x["path"] not in (text, raw) and x.get("label") != raw]
        if len(keep) == len(items):
            raise PersonalError(f"{raw!r} is not one of your locations (see `store locations list`)")
        gone = [x for x in items if x not in keep]
        self._save(keep)
        return gone[0]


# ---------------------------------------------------------------- personal.sqlite
DDL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, rel TEXT NOT NULL, path TEXT NOT NULL, member TEXT,
  size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, crc32 TEXT, sha1 TEXT, variants TEXT,
  status TEXT NOT NULL CHECK (status IN ('identified','unidentified')), note TEXT,
  platform_key TEXT, canonical_name TEXT, rom_name TEXT, serial TEXT, match_key TEXT, igdb_id INTEGER,
  last_seen TEXT NOT NULL, UNIQUE (location, rel)
);
CREATE INDEX IF NOT EXISTS items_status ON items (status);
CREATE INDEX IF NOT EXISTS items_name ON items (platform_key, match_key);
"""


def norm_title(name):
    """A comparison key for a title: dump-name tags and punctuation removed, "Legend of Zelda, The" -> "the legend of zelda"."""
    s = name
    prev = None
    while prev != s:
        prev, s = s, re.sub(r"\s*[\(\[][^\)\]]*[\)\]]\s*$", "", s)
    s = re.sub(r"^(.*?), (The|A|An)( - .*)?$", lambda m: f"{m[2]} {m[1]}{m[3] or ''}", s.strip())
    return re.sub(r"[^a-z0-9]+", "", s.lower())


class PersonalDB:
    def __init__(self, path):
        self.path = Path(path)

    def connect(self, create=False):
        if not create and not self.path.exists():
            return None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not self.path.exists()
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.executescript(DDL)
        db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA),))
        if fresh:
            os.chmod(self.path, 0o600)
        have = int(db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0])
        if have != SCHEMA:
            db.close()
            raise PersonalError(f"{self.path} has schema version {have}; this client reads {SCHEMA}")
        return db

    def counts(self):
        db = self.connect()
        if not db:
            return {"identified": 0, "unidentified": 0}
        try:
            return {s: db.execute("SELECT COUNT(*) FROM items WHERE status=?", (s,)).fetchone()[0] for s in ("identified", "unidentified")}
        finally:
            db.close()

    def identified(self):
        db = self.connect()
        if not db:
            return []
        try:
            return [dict(r) for r in db.execute("SELECT * FROM items WHERE status='identified' ORDER BY platform_key, canonical_name, path")]
        finally:
            db.close()

    def unidentified(self):
        db = self.connect()
        if not db:
            return []
        try:
            return [dict(r) for r in db.execute("SELECT * FROM items WHERE status='unidentified' ORDER BY path")]
        finally:
            db.close()

    def forget_location(self, location):
        db = self.connect()
        if not db:
            return 0
        try:
            n = db.execute("DELETE FROM items WHERE location=?", (location,)).rowcount
            db.commit()
            return n
        finally:
            db.close()


def _plausible(path, hash_exts):
    name = path.name
    return not name.startswith(".") and (path.suffix.lower().lstrip(".") in hash_exts or path.suffix.lower().lstrip(".") in OPAQUE_EXTS)


def scan_locations(db_path, locations, index, exts_by_db, catalog_lookup=None, log=print, now=time.time, only=None):
    """Walk the locations on this device, recognise files locally and update personal.sqlite.

    exts_by_db: {libretro db name: {extensions}} of the platforms this library has folders for (decides which
    databases are used and breaks cross-platform ties). catalog_lookup(db, name) -> igdb id or None.
    Returns a summary dict. A location that is not reachable is left untouched (its rows stay) and reported."""
    hash_exts = set(DISC_EXTS) | {e for s in exts_by_db.values() for e in s}
    pdb = PersonalDB(db_path)
    db = pdb.connect(create=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now()))
    summary = {"locations": [], "identified": 0, "unidentified": 0, "hashed": 0, "reused": 0, "ignored": 0, "removed": 0, "unreachable": []}
    try:
        for loc in locations:
            if only and only not in (loc["path"], loc.get("label")):
                continue
            root = Path(loc["path"])
            if not root.is_dir():
                summary["unreachable"].append(loc["path"])
                log(f"! {loc.get('label', root.name)}: not reachable right now (is the drive mounted?); left as it was")
                continue
            seen, stats = set(), {"label": loc.get("label") or root.name, "path": loc["path"], "files": 0, "identified": 0, "unidentified": 0}
            old = {r["rel"]: r for r in db.execute("SELECT * FROM items WHERE location=?", (loc["path"],))}
            for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                for fn in sorted(filenames):
                    p = Path(dirpath) / fn
                    if p.is_symlink() or not _plausible(p, hash_exts):
                        summary["ignored"] += 1
                        continue
                    try:
                        st = p.stat()
                    except OSError:
                        continue
                    rel = str(p.relative_to(root))
                    seen.add(rel)
                    stats["files"] += 1
                    prev = old.get(rel)
                    ext = p.suffix.lower().lstrip(".")
                    opaque = ext in OPAQUE_EXTS
                    if opaque:
                        variants, member, why = [], None, None      # containers are never hashed
                    elif prev and prev["size"] == st.st_size and prev["mtime_ns"] == st.st_mtime_ns and prev["variants"] is not None \
                            and not (prev["note"] or "").startswith("could not read"):
                        # unchanged since the last scan: reuse its hashes, but recognise it again (the databases may have changed)
                        summary["reused"] += 1
                        variants = [tuple(v) for v in json.loads(prev["variants"])]
                        member, why = prev["member"], None
                    else:
                        variants, member, why = _hash_file(p, st.st_size)
                        summary["hashed"] += 1
                    inner = (Path(member).suffix if member else p.suffix).lower().lstrip(".")
                    if opaque:
                        res = ("unidentified", None, None, None, None, "compressed container: not matched by hash")
                    elif not variants:
                        res = ("unidentified", None, None, None, None, why or "not hashed")
                    else:
                        res = identify(index, variants, exts_by_db, inner)
                    status, dbname, name, rom_name, serial, note = res
                    crc = sha1 = None
                    if variants:
                        # the variant the database matched (header-stripped for some systems), else the whole file
                        hit = next((v for v in variants if status == "identified" and index.lookup(v[1], v[0], v[2])), variants[0])
                        crc, sha1 = hit[0], hit[1]
                    igdb = catalog_lookup(dbname, name) if (status == "identified" and catalog_lookup) else None
                    db.execute(
                        "INSERT INTO items (location, rel, path, member, size, mtime_ns, crc32, sha1, variants, status, note, platform_key, canonical_name,"
                        " rom_name, serial, match_key, igdb_id, last_seen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                        " ON CONFLICT (location, rel) DO UPDATE SET path=excluded.path, member=excluded.member, size=excluded.size,"
                        " mtime_ns=excluded.mtime_ns, crc32=excluded.crc32, sha1=excluded.sha1, variants=excluded.variants,"
                        " status=excluded.status, note=excluded.note,"
                        " platform_key=excluded.platform_key, canonical_name=excluded.canonical_name, rom_name=excluded.rom_name,"
                        " serial=excluded.serial, match_key=excluded.match_key, igdb_id=excluded.igdb_id, last_seen=excluded.last_seen",
                        (loc["path"], rel, str(p), member, st.st_size, st.st_mtime_ns, crc, sha1, json.dumps(variants), status, note, dbname, name, rom_name, serial,
                         norm_title(name) if name else None, igdb, stamp))
                    stats[status] += 1
            gone = [r for r in old if r not in seen]
            for rel in gone:
                db.execute("DELETE FROM items WHERE location=? AND rel=?", (loc["path"], rel))
            summary["removed"] += len(gone)
            db.commit()
            summary["locations"].append(stats)
            summary["identified"] += stats["identified"]
            summary["unidentified"] += stats["unidentified"]
        db.execute("INSERT INTO meta VALUES ('scanned_at', ?) ON CONFLICT (key) DO UPDATE SET value=excluded.value", (stamp,))
        db.commit()
    finally:
        db.close()
    return summary


def _hash_file(p, size):
    """(variants, zip member name or None, note when nothing could be hashed)."""
    ext = p.suffix.lower().lstrip(".")
    try:
        if ext == "zip":
            one = zip_single_member(p)
            if one:
                info, head = one
                return zip_member_variants(p, info, head), info.filename, None
            # several files inside: only a hash of the archive itself could match
            return file_variants(p, "zip", size), None, None
        return file_variants(p, ext, size), None, None
    except OSError as e:
        return [], None, f"could not read it ({e.strerror or e})"
