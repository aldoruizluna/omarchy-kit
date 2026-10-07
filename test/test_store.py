"""Tests for games/storelib.py (the store client). Standard library + the `openssl` command only.

  python3 test/test_store.py            # or: python3 -m unittest discover -s test -p 'test_*.py'

Each test builds a real signed snapshot (SQLite in zstd, ECDSA P-256 over the file bytes) in a temp folder,
serves artifacts from a local HTTP server on 127.0.0.1, and drives storelib.Store against a throw-away ~/Games.
"""
import base64, calendar, hashlib, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, threading, unittest, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "games"))
from compression import zstd  # noqa: E402
import storelib  # noqa: E402
from storelib import DroppedEntries, Store, StoreError  # noqa: E402

DDL = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE entries (id TEXT PRIMARY KEY, slug TEXT NOT NULL, title TEXT NOT NULL, platform_key TEXT NOT NULL,
  kind TEXT NOT NULL, mode TEXT NOT NULL, igdb_id INTEGER, ra_game_id INTEGER, json TEXT NOT NULL);
CREATE TABLE tombstones (id TEXT PRIMARY KEY, removed_at TEXT NOT NULL, reason TEXT NOT NULL);
"""
SYSTEMS = {
    "Nintendo - Game Boy": {"folder": "gb", "exts": ["gb", "gbc", "zip", "7z"]},
    "Nintendo - GameCube": {"folder": "gc", "exts": ["rvz", "iso", "dol"]},
    "MAME": {"folder": "mame", "exts": ["zip"]},
    "ScummVM": {"folder": "scummvm", "exts": ["scummvm"]},
}


def openssl(*args):
    return subprocess.run(["openssl", *args], check=True, capture_output=True)


def make_keys(d, name, algo="ec"):
    priv, pub = Path(d) / f"{name}.key.pem", Path(d) / f"{name}.pub.pem"
    if algo == "ec":
        openssl("ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", str(priv))
    else:
        openssl("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv))
    openssl("pkey", "-in", str(priv), "-pubout", "-out", str(pub))
    return priv, pub


def make_snapshot(out, priv, entries, tombstones=(), version="2026100701", created="2026-10-07T00:00:00Z",
                  meta_version=None, min_client="0.1.0", count_delta=0):
    """Write version.json + catalog.sqlite.zst into `out`, signed like the publisher does."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "tmp.sqlite"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript(DDL)
    con.executemany("INSERT INTO meta VALUES (?, ?)", [("schema", "1"), ("version", meta_version or version), ("createdAt", created)])
    for e in entries:
        con.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?)", (e["id"], e["slug"], e["title"], e["platformKey"], e["kind"], e["mode"], None, None, json.dumps(e)))
    for t in tombstones:
        con.execute("INSERT INTO tombstones VALUES (?,?,?)", (t["id"], t["removedAt"], t["reason"]))
    con.commit()
    raw = con.serialize()
    con.close()
    db.unlink()
    blob = zstd.compress(raw)
    (out / "catalog.sqlite.zst").write_bytes(blob)
    sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(priv)], input=blob, capture_output=True, check=True).stdout
    (out / "version.json").write_text(json.dumps({
        "schema": 1, "version": version, "createdAt": created, "entries": len(entries) + count_delta, "tombstones": len(tombstones),
        "sha256": hashlib.sha256(blob).hexdigest(), "signature": base64.b64encode(sig).decode(), "minClient": min_client}))
    return out


class Handler(BaseHTTPRequestHandler):
    files, hits = {}, []

    def do_GET(self):
        Handler.hits.append(self.path)
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "http://example.org/evil.gb")
            self.end_headers()
            return
        data = Handler.files.get(self.path)
        if data is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


class StoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory()
        cls.priv, cls.pub = make_keys(cls.keys.name, "pub")
        cls.priv2, cls.pub2 = make_keys(cls.keys.name, "other")
        cls.rsa_priv, cls.rsa_pub = make_keys(cls.keys.name, "rsa", algo="rsa")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.keys.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.games, self.roms = self.root / "Games", self.root / "Games" / "roms"
        self.roms.mkdir(parents=True)
        self.src = self.root / "source"
        self.log, self.changed, self.budget_msg = [], [], None
        Handler.files, Handler.hits = {}, []
        self.store = self.new_store(self.pub)

    def tearDown(self):
        self.tmp.cleanup()

    def new_store(self, key):
        return Store(games=self.games, roms=self.roms, key_path=key, config_path=self.root / "store.toml", systems=SYSTEMS,
                     budget_check=lambda extra: self.budget_msg, free_bytes=lambda: 10 ** 12,
                     after_change=lambda folders: self.changed.append(set(folders)), log=self.log.append)

    # ---- fixtures
    def art(self, name, data):
        Handler.files["/" + name] = data
        return {"filename": name, "format": name.rsplit(".", 1)[-1], "size": len(data), "sha1": hashlib.sha1(data).hexdigest(),
                "sha256": hashlib.sha256(data).hexdigest(), "url": f"{self.base}/{name}"}

    def entry(self, ident, title, *, platform="Nintendo - Game Boy", mode="link", kind="homebrew", data=b"ROM" * 100, filename=None,
              spdx="MIT", routes=None):
        slug = "-".join(title.lower().split())
        if mode == "guide":
            return {"id": ident, "slug": slug, "title": title, "platformKey": platform, "kind": "commercial", "mode": "guide", "license": None,
                    "artifact": None, "credits": [], "igdbId": None, "raGameId": None,
                    "routes": routes or [{"kind": "dump", "label": "Dump your own cartridge", "url": "https://example.com/dump"}]}
        return {"id": ident, "slug": slug, "title": title, "platformKey": platform, "kind": kind, "mode": mode,
                "license": {"spdx": spdx, "kind": "spdx", "evidenceUrl": "https://example.com/license", "attribution": f"{title} by Ann ({spdx})"},
                "artifact": self.art(filename or f"{slug}.gb", data), "credits": [{"name": "Ann", "role": "developer"}],
                "igdbId": None, "raGameId": None, "routes": []}

    def publish(self, entries, **kw):
        return make_snapshot(self.src, self.priv, entries, **kw)

    def refreshed(self, entries, **kw):
        self.publish(entries, **kw)
        return self.store.refresh(str(self.src))

    # ---- verification
    def test_good_snapshot_verifies_and_installs(self):
        r = self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta", mode="host")])
        self.assertEqual((r["status"], r["version"], r["entries"]), ("updated", "2026100701", 2))
        snap = self.store.current()
        self.assertEqual([e["id"] for e in snap.entries], ["a:1", "a:2"])

    def test_refresh_over_http_from_a_base_address(self):
        self.publish([self.entry("a:1", "Alpha")])
        for n in ("version.json", "catalog.sqlite.zst"):
            Handler.files["/snap/" + n] = (self.src / n).read_bytes()
        self.assertEqual(self.store.refresh(self.base + "/snap")["status"], "updated")

    def test_source_can_come_from_the_config_file(self):
        self.publish([self.entry("a:1", "Alpha")])
        (self.root / "store.toml").write_text(f'[store]\nsource = "{self.src}"\n')
        self.assertEqual(self.store.refresh()["status"], "updated")

    def test_no_source_configured_explains_how(self):
        with self.assertRaisesRegex(StoreError, "no snapshot source"):
            self.store.refresh()

    def test_tampered_catalog_is_rejected_and_nothing_is_installed(self):
        self.publish([self.entry("a:1", "Alpha")])
        f = self.src / "catalog.sqlite.zst"
        b = bytearray(f.read_bytes())
        b[len(b) // 2] ^= 1
        f.write_bytes(bytes(b))
        with self.assertRaisesRegex(StoreError, "sha256 mismatch"):
            self.store.refresh(str(self.src))
        self.assertIsNone(self.store.current())

    def test_a_snapshot_signed_by_another_key_is_rejected(self):
        make_snapshot(self.src, self.priv2, [self.entry("a:1", "Alpha")])
        with self.assertRaisesRegex(StoreError, "signature does not verify"):
            self.store.refresh(str(self.src))
        self.assertIsNone(self.store.current())

    def test_refresh_refuses_without_a_pinned_key_and_never_fetches(self):
        self.publish([self.entry("a:1", "Alpha")])
        store = self.new_store(self.root / "missing.pem")
        with self.assertRaisesRegex(StoreError, "no publisher key"):
            store.refresh(self.base + "/snap")
        self.assertEqual(Handler.hits, [])

    def test_only_a_p256_public_key_is_accepted(self):
        self.publish([self.entry("a:1", "Alpha")])
        with self.assertRaisesRegex(StoreError, "P-256"):
            self.new_store(self.rsa_pub).refresh(str(self.src))
        with self.assertRaisesRegex(StoreError, "contains a private key"):
            self.new_store(self.priv).refresh(str(self.src))
        junk = self.root / "junk.pem"
        junk.write_text("not a key")
        with self.assertRaisesRegex(StoreError, "not a public key"):
            self.new_store(junk).refresh(str(self.src))

    def test_versions_never_go_backwards(self):
        self.refreshed([self.entry("a:1", "Alpha")], version="2026100702")
        self.publish([self.entry("a:1", "Alpha")], version="2026100701")
        with self.assertRaisesRegex(StoreError, "backwards"):
            self.store.refresh(str(self.src))
        self.assertEqual(self.store.current().version["version"], "2026100702")

    def test_same_version_is_up_to_date_but_different_content_under_it_is_refused(self):
        self.refreshed([self.entry("a:1", "Alpha")])
        self.assertEqual(self.store.refresh(str(self.src))["status"], "current")
        self.publish([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")])
        with self.assertRaisesRegex(StoreError, "same version number"):
            self.store.refresh(str(self.src))

    def test_version_json_cannot_relabel_an_old_signed_catalog(self):
        self.publish([self.entry("a:1", "Alpha")], version="2026100701", meta_version="2026100601")
        with self.assertRaisesRegex(StoreError, "signed catalog says"):
            self.store.refresh(str(self.src))

    def test_a_snapshot_that_needs_a_newer_client_is_refused(self):
        self.publish([self.entry("a:1", "Alpha")], min_client="9.0.0")
        with self.assertRaisesRegex(StoreError, "needs store client 9.0.0"):
            self.store.refresh(str(self.src))

    def test_row_counts_must_match_version_json(self):
        self.publish([self.entry("a:1", "Alpha")], count_delta=1)
        with self.assertRaisesRegex(StoreError, "row counts differ"):
            self.store.refresh(str(self.src))

    def test_signed_but_malformed_entries_are_refused_as_a_whole(self):
        cases = {
            "commercial host": {**self.entry("a:1", "Alpha"), "kind": "commercial"},
            "guide with a file": {**self.entry("a:1", "Alpha", mode="guide"), "artifact": self.entry("a:9", "X")["artifact"]},
            "path in filename": self.entry("a:1", "Alpha", filename="x.gb"),
            "insecure address": self.entry("a:1", "Alpha"),
            "no license": {**self.entry("a:1", "Alpha"), "license": None},
        }
        cases["path in filename"]["artifact"]["filename"] = "../evil.gb"
        cases["insecure address"]["artifact"]["url"] = "http://example.com/a.gb"
        for name, bad in cases.items():
            with self.subTest(name):
                self.publish([bad])
                with self.assertRaisesRegex(StoreError, "malformed"):
                    self.store.refresh(str(self.src))
                self.assertIsNone(self.store.current())

    # ---- no silent drops
    def test_dropping_an_entry_without_a_tombstone_keeps_the_previous_snapshot(self):
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")], version="2026100701")
        self.publish([self.entry("a:1", "Alpha")], version="2026100702")
        with self.assertRaises(DroppedEntries) as cm:
            self.store.refresh(str(self.src))
        self.assertEqual(cm.exception.dropped, ["a:2"])
        self.assertIn("without a tombstone", str(cm.exception))
        self.assertEqual(self.store.current().version["version"], "2026100701")

    def test_accept_drops_installs_and_warns(self):
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")], version="2026100701")
        self.publish([self.entry("a:1", "Alpha")], version="2026100702")
        r = self.store.refresh(str(self.src), accept_drops=True)
        self.assertEqual((r["status"], r["dropped"]), ("updated", ["a:2"]))
        self.assertTrue(any("without a tombstone" in m for m in self.log))
        self.assertEqual(self.store.current().version["version"], "2026100702")

    def test_a_tombstoned_entry_leaving_is_not_a_drop(self):
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")], version="2026100701")
        self.publish([self.entry("a:1", "Alpha")], version="2026100702",
                     tombstones=[{"id": "a:2", "removedAt": "2026-10-07T01:00:00Z", "reason": "takedown upheld"}])
        self.assertEqual(self.store.refresh(str(self.src))["dropped"], [])

    # ---- get
    def test_get_downloads_verifies_places_and_records(self):
        self.refreshed([self.entry("a:1", "Alpha Quest", data=b"\x00" * 500)])
        r = self.store.get_many(["alpha-quest"])
        self.assertEqual(r[0][1]["status"], "installed")
        f = self.roms / "gb" / "Alpha Quest.gb"
        self.assertEqual(f.read_bytes(), b"\x00" * 500)
        rec = self.store.manifest()["a:1"]
        self.assertEqual((rec["sha256"], rec["files"], rec["snapshot"], rec["license"]["spdx"]), (hashlib.sha256(b"\x00" * 500).hexdigest(), ["gb/Alpha Quest.gb"], "2026100701", "MIT"))
        self.assertIn("Alpha Quest", (self.roms / "gb" / "STORE-CREDITS.md").read_text())
        self.assertEqual(self.changed, [{"gb"}])
        self.assertEqual(list((self.games / ".cache" / "store" / "downloads").glob("*")), [])
        self.assertEqual(self.store.get("a:1")["status"], "already")

    def test_guide_entries_are_refused_with_the_routes(self):
        self.refreshed([self.entry("g:1", "Paid Game", mode="guide")])
        with self.assertRaisesRegex(StoreError, r"(?s)commercial game.*dump: Dump your own cartridge https://example.com/dump"):
            self.store.get("paid-game")
        self.assertEqual(Handler.hits, [])
        self.assertIn("No file is offered", "\n".join(self.store.info_lines(self.store.require().by_id["g:1"])))

    def test_budget_is_checked_before_any_download(self):
        self.refreshed([self.entry("a:1", "Alpha")])
        self.budget_msg = "would exceed the 231 GB budget"
        with self.assertRaisesRegex(StoreError, "not downloading Alpha: would exceed the 231 GB budget"):
            self.store.get("alpha")
        self.assertEqual(Handler.hits, [])
        self.assertEqual(self.store.manifest(), {})

    def test_free_disk_is_checked_too(self):
        self.refreshed([self.entry("a:1", "Alpha")])
        self.store.free_bytes = lambda: 1000
        with self.assertRaisesRegex(StoreError, "of disk is free"):
            self.store.get("alpha")
        self.assertEqual(Handler.hits, [])

    def test_a_checksum_mismatch_deletes_the_partial_and_installs_nothing(self):
        e = self.entry("a:1", "Alpha", data=b"good" * 50)
        Handler.files["/alpha.gb"] = b"evil" * 50          # same size, different bytes
        self.refreshed([e])
        with self.assertRaisesRegex(StoreError, "does not match the catalog's checksums"):
            self.store.get("alpha")
        self.assertEqual(list((self.games / ".cache" / "store" / "downloads").glob("*")), [])
        self.assertFalse((self.roms / "gb" / "Alpha.gb").exists())
        self.assertEqual(self.store.manifest(), {})

    def test_a_wrong_size_is_refused_and_cleaned_up(self):
        e = self.entry("a:1", "Alpha", data=b"x" * 100)
        Handler.files["/alpha.gb"] = b"x" * 150
        self.refreshed([e])
        with self.assertRaisesRegex(StoreError, "larger than the expected"):
            self.store.get("alpha")
        Handler.files["/alpha.gb"] = b"x" * 90
        with self.assertRaisesRegex(StoreError, "downloaded 90 bytes"):
            self.store.get("alpha")
        self.assertEqual(list((self.games / ".cache" / "store" / "downloads").glob("*")), [])

    def test_a_redirect_to_plain_http_elsewhere_is_refused(self):
        e = self.entry("a:1", "Alpha")
        e["artifact"]["url"] = self.base + "/redirect"
        self.refreshed([e])
        with self.assertRaisesRegex(StoreError, "refusing a redirect"):
            self.store.get("alpha")

    def test_an_unmanaged_file_with_the_same_name_is_never_overwritten(self):
        (self.roms / "gb").mkdir()
        (self.roms / "gb" / "Alpha.gb").write_bytes(b"MINE")
        self.refreshed([self.entry("a:1", "Alpha")])
        r = self.store.get("alpha")
        self.assertEqual((self.roms / "gb" / "Alpha.gb").read_bytes(), b"MINE")
        self.assertEqual(r["files"], ["gb/Alpha [alpha].gb"])

    def test_platforms_the_library_has_no_folder_for_are_refused_clearly(self):
        self.refreshed([self.entry("a:1", "Alpha", platform="Nintendo - Wii")])
        with self.assertRaisesRegex(StoreError, "no folder for Nintendo - Wii"):
            self.store.get("alpha")

    def test_mame_sets_keep_their_exact_file_name(self):
        self.refreshed([self.entry("mame:circus", "Circus", platform="MAME", filename="circus.zip", data=b"PK\x03\x04zip")])
        self.assertEqual(self.store.get("mame:circus")["files"], ["mame/circus.zip"])

    def test_scummvm_archives_are_extracted_with_a_launcher(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("sky-game/sky.dnr", "data")
            zf.writestr("sky-game/sub/sky.dsk", "disk")
        self.refreshed([self.entry("scummvm:sky", "Beneath a Steel Sky", platform="ScummVM", filename="bass.zip", data=buf.getvalue())])
        files = self.store.get("scummvm:sky")["files"]
        d = self.roms / "scummvm" / "Beneath a Steel Sky"
        self.assertEqual((d / "sky.scummvm").read_text(), "sky")
        self.assertEqual((d / "sub" / "sky.dsk").read_text(), "disk")
        self.assertIn("scummvm/Beneath a Steel Sky/sky.scummvm", files)

    def test_an_archive_with_an_unsafe_path_installs_nothing(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../escape.txt", "x")
        self.refreshed([self.entry("scummvm:bad", "Bad Game", platform="ScummVM", filename="bad.zip", data=buf.getvalue())])
        with self.assertRaisesRegex(StoreError, "unsafe path"):
            self.store.get("scummvm:bad")
        self.assertFalse((self.roms / "escape.txt").exists())
        self.assertFalse((self.roms / "scummvm" / "Bad Game").exists())

    def test_a_zip_for_a_system_that_does_not_open_zips_is_unpacked(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("Game.dol", "dol-bytes")
            zf.writestr("readme.txt", "hi")
        self.refreshed([self.entry("gc:1", "Cube Game", platform="Nintendo - GameCube", filename="cube.zip", data=buf.getvalue())])
        self.assertEqual(self.store.get("cube-game")["files"], ["gc/Cube Game.dol"])
        self.assertEqual((self.roms / "gc" / "Cube Game.dol").read_text(), "dol-bytes")

    # ---- remove / sync
    def test_remove_deletes_only_what_it_installed(self):
        (self.games / "saves").mkdir()
        (self.games / "saves" / "alpha.srm").write_bytes(b"SAVE")
        (self.roms / "gb").mkdir()
        (self.roms / "gb" / "Other.gb").write_bytes(b"OTHER")
        self.refreshed([self.entry("a:1", "Alpha")])
        self.store.get_many(["alpha"])
        self.store.remove_many(["alpha"])
        self.assertFalse((self.roms / "gb" / "Alpha.gb").exists())
        self.assertFalse((self.roms / "gb" / "STORE-CREDITS.md").exists())
        self.assertEqual((self.roms / "gb" / "Other.gb").read_bytes(), b"OTHER")
        self.assertEqual((self.games / "saves" / "alpha.srm").read_bytes(), b"SAVE")
        self.assertEqual(self.store.manifest(), {})
        self.assertEqual(self.changed[-1], {"gb"})

    def test_sync_removes_installs_that_were_tombstoned(self):
        (self.games / "saves").mkdir()
        (self.games / "saves" / "alpha.srm").write_bytes(b"SAVE")
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")], version="2026100701")
        self.store.get_many(["alpha", "beta"])
        self.publish([self.entry("a:2", "Beta")], version="2026100702",
                     tombstones=[{"id": "a:1", "removedAt": "2026-10-07T01:00:00Z", "reason": "takedown upheld"}])
        self.store.refresh(str(self.src))
        removed, notes = self.store.sync_and_apply()
        self.assertEqual([(r["id"], why) for r, why in removed], [("a:1", "takedown upheld")])
        self.assertFalse((self.roms / "gb" / "Alpha.gb").exists())
        self.assertTrue((self.roms / "gb" / "Beta.gb").exists())
        self.assertEqual(list(self.store.manifest()), ["a:2"])
        self.assertEqual((self.games / "saves" / "alpha.srm").read_bytes(), b"SAVE")
        self.assertNotIn("Alpha", (self.roms / "gb" / "STORE-CREDITS.md").read_text())
        self.assertEqual(notes, [])
        self.assertEqual(self.changed[-1], {"gb"})

    def test_sync_reports_but_keeps_an_install_that_vanished_without_a_tombstone(self):
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta")], version="2026100701")
        self.store.get_many(["alpha"])
        self.publish([self.entry("a:2", "Beta")], version="2026100702")
        self.store.refresh(str(self.src), accept_drops=True)
        removed, notes = self.store.sync()
        self.assertEqual(removed, [])
        self.assertTrue((self.roms / "gb" / "Alpha.gb").exists())
        self.assertRegex(notes[0], "no longer listed .* no tombstone")

    # ---- browsing, hygiene, health
    def test_list_search_info_and_ambiguity(self):
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("b:1", "Alpha", platform="Nintendo - GameCube", filename="alpha.dol"),
                        self.entry("g:1", "Paid Game", mode="guide")])
        snap = self.store.require()
        self.assertEqual(len(self.store.list_entries(snap)), 3)
        self.assertEqual([e["id"] for e in self.store.list_entries(snap, platform="gc")], ["b:1"])
        self.assertEqual([e["id"] for e in self.store.list_entries(snap, mode="guide")], ["g:1"])
        self.assertEqual([e["id"] for e in self.store.search(snap, "ann")], ["a:1", "b:1"])   # credits are searched
        with self.assertRaisesRegex(StoreError, "matches several entries"):
            self.store.resolve(snap, "alpha")
        self.assertEqual(self.store.resolve(snap, "alpha", platform="gc")["id"], "b:1")
        with self.assertRaisesRegex(StoreError, "Did you mean: .*alpha"):
            self.store.resolve(snap, "alph")

    def test_browsing_makes_no_network_calls(self):
        self.refreshed([self.entry("a:1", "Alpha")])
        Handler.hits.clear()
        orig, storelib._open_url = storelib._open_url, lambda *a, **k: self.fail("network used while browsing")
        try:
            snap = self.store.require()
            self.store.list_entries(snap), self.store.search(snap, "a"), self.store.info_lines(snap.entries[0]), self.store.health_lines()
        finally:
            storelib._open_url = orig
        self.assertEqual(Handler.hits, [])

    def test_health_reports_key_snapshot_installs_and_age(self):
        self.assertIn("pinned", "\n".join(self.store.health_lines()))
        self.refreshed([self.entry("a:1", "Alpha"), self.entry("a:2", "Beta", mode="host"), self.entry("g:1", "Paid", mode="guide")])
        self.store.get_many(["alpha"])
        self.store.now = lambda: calendar.timegm((2026, 10, 7, 0, 0, 0)) + 60 * 86400   # two months after createdAt
        text = "\n".join(self.store.health_lines())
        self.assertIn("host 1, link 1, guide 1", text)
        self.assertIn("STALE", text)
        self.assertIn("installed         1 titles", text)
        self.assertFalse(self.new_store(self.root / "none.pem").health()["key"])

    def test_corrupt_cached_snapshot_is_caught_on_every_load(self):
        self.refreshed([self.entry("a:1", "Alpha")])
        cat = self.games / ".cache" / "store" / "snapshots" / "2026100701" / "catalog.sqlite.zst"
        b = bytearray(cat.read_bytes())
        b[10] ^= 1
        cat.write_bytes(bytes(b))
        with self.assertRaisesRegex(StoreError, "sha256 mismatch"):
            self.store.require()


if __name__ == "__main__":
    unittest.main(verbosity=2)
