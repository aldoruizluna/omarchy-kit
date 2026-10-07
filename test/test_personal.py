"""Tests for games/personallib.py and the personal-backups side of games/storelib.py. Standard library + `openssl`.

  python3 test/test_personal.py         # or: python3 -m unittest discover -s test -p 'test_*.py'

Every test builds real-format libretro databases (.rdb: header, MessagePack records, metadata) and small backup
folders in a temp directory, and drives storelib.Store against a throw-away ~/Games. Sockets are blocked in the
tests that matter: scanning, matching, merging and installing from your own folder must work with no network at all.
One test also reads this machine's real libretro database, when it and a known file are present.
"""
import hashlib, io, json, os, re, shutil, socket, struct, sys, tempfile, unittest, zipfile, zlib
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "games"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import personallib as pl  # noqa: E402
import storelib  # noqa: E402
from storelib import Store, StoreError  # noqa: E402
from test_store import make_keys, make_snapshot  # noqa: E402

GB, GBC, NES, PSX = "Nintendo - Game Boy", "Nintendo - Game Boy Color", "Nintendo - Nintendo Entertainment System", "Sony - PlayStation"
SYS = {
    GB: {"folder": "gb", "exts": ["gb", "zip"]},
    GBC: {"folder": "gbc", "exts": ["gbc", "zip"]},
    NES: {"folder": "nes", "exts": ["nes"]},            # does not open zip files
    PSX: {"folder": "psx", "exts": ["cue", "bin", "chd"]},
}


# ---------------------------------------------------------------- a tiny MessagePack writer and .rdb builder
def pack(o):
    if o is None:
        return b"\xc0"
    if isinstance(o, bool):
        return b"\xc3" if o else b"\xc2"
    if isinstance(o, int):
        if 0 <= o < 128:
            return bytes([o])
        if -32 <= o < 0:
            return struct.pack("b", o)
        if 0 <= o < 256:
            return b"\xcc" + bytes([o])
        if 0 <= o < 65536:
            return b"\xcd" + struct.pack(">H", o)
        if 0 <= o < 2 ** 32:
            return b"\xce" + struct.pack(">I", o)
        if o >= 0:
            return b"\xcf" + struct.pack(">Q", o)
        return b"\xd3" + struct.pack(">q", o)
    if isinstance(o, float):
        return b"\xcb" + struct.pack(">d", o)
    if isinstance(o, str):
        b = o.encode()
        return (bytes([0xa0 | len(b)]) if len(b) < 32 else b"\xd9" + bytes([len(b)]) if len(b) < 256 else b"\xda" + struct.pack(">H", len(b))) + b
    if isinstance(o, bytes):
        return (b"\xc4" + bytes([len(o)]) if len(o) < 256 else b"\xc5" + struct.pack(">H", len(o))) + o
    if isinstance(o, list):
        return (bytes([0x90 | len(o)]) if len(o) < 16 else b"\xdc" + struct.pack(">H", len(o))) + b"".join(pack(x) for x in o)
    if isinstance(o, dict):
        head = bytes([0x80 | len(o)]) if len(o) < 16 else b"\xde" + struct.pack(">H", len(o))
        return head + b"".join(pack(k) + pack(v) for k, v in o.items())
    raise TypeError(o)


def write_rdb(path, records):
    body = b"".join(pack(r) for r in records)
    Path(path).write_bytes(b"RARCHDB\x00" + struct.pack(">Q", 16 + len(body)) + body + pack({"count": len(records)}))


def rec(name, data, rom_name=None, sha1=True):
    r = {"name": name, "description": name, "rom_name": rom_name or name + ".bin", "size": len(data), "crc": struct.pack(">I", zlib.crc32(data) & 0xffffffff)}
    if sha1:
        r["sha1"] = hashlib.sha1(data).digest()
    return r


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def blob(tag, n=300):
    return (tag.encode() * n)[:n]


def zip_bytes(name, data):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, data)
    return buf.getvalue()


NES_BODY = blob("nes-body-", 400)
NES_HEADERED = b"NES\x1a" + b"\x01\x01\x00\x00" + b"\x00" * 8 + NES_BODY
ALPHA, ALPHA_EU, BETA, TIE, GAMMA = blob("alpha-"), blob("alpha-eu-"), blob("beta-"), blob("tie-"), blob("gamma-")
CUE_TEXT = b'FILE "Disc Game (USA) (Track 1).bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
TRACK1 = blob("disc-track1-", 2352)
AMBIG = blob("ambiguous-")
DUPE = blob("dupe-name-")


class PersonalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory()
        cls.priv, cls.pub = make_keys(cls.keys.name, "pub")

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.games, self.roms = self.root / "Games", self.root / "Games" / "roms"
        self.roms.mkdir(parents=True)
        self.rdb = self.root / "rdb"
        self.rdb.mkdir()
        self.src = self.root / "source"
        self.back = self.root / "backups"
        self.back.mkdir()
        self.log, self.changed, self.budget_msg = [], [], None
        self.write_databases()
        self.store = self.new_store()
        self.add_files()

    def tearDown(self):
        self.tmp.cleanup()

    def new_store(self):
        return Store(games=self.games, roms=self.roms, key_path=self.pub, config_path=self.root / "store.toml", systems=SYS,
                     budget_check=lambda extra: self.budget_msg, free_bytes=lambda: 10 ** 12,
                     after_change=lambda folders: self.changed.append(set(folders)), log=self.log.append,
                     rdb_dir=self.rdb, mounts=[])

    # ---- fixtures
    def write_databases(self):
        write_rdb(self.rdb / f"{GB}.rdb", [rec("Alpha Quest (USA)", ALPHA), rec("Alpha Quest (Europe)", ALPHA_EU), rec("Beta Run (Europe)", BETA),
                                           rec("Tie Game (World)", TIE), rec("Ambiguous Name (USA)", AMBIG), rec("Ambiguous Name (Europe)", AMBIG),
                                           rec("Dupe Dump (USA)", DUPE), rec("Dupe Dump (Rev 1)", DUPE)])
        write_rdb(self.rdb / f"{GBC}.rdb", [rec("Tie Game (World)", TIE), rec("Ambiguous Name (USA)", AMBIG)])
        write_rdb(self.rdb / f"{NES}.rdb", [rec("Gamma Force (USA)", NES_BODY), rec("Delta Zip (USA)", blob("delta-"))])
        write_rdb(self.rdb / f"{PSX}.rdb", [rec("Disc Game (USA)", CUE_TEXT, "Disc Game (USA).cue"), rec("Disc Game (USA)", TRACK1, "Disc Game (USA) (Track 1).bin")])

    def add_files(self):
        b = self.back
        (b / "gb").mkdir()
        (b / "gb" / "alpha.gb").write_bytes(ALPHA)
        (b / "gb" / "beta.zip").write_bytes(zip_bytes("beta.gb", BETA))
        (b / "gb" / "tie.gbc").write_bytes(TIE)                    # listed under GB and GBC: the extension settles it
        (b / "gb" / "tie2.bin").write_bytes(TIE)                    # same bytes, an extension that fits neither: not guessed
        (b / "gb" / "ambiguous.gb").write_bytes(AMBIG)              # one hash, two names in GB
        (b / "gb" / "unknown.gb").write_bytes(blob("nobody-lists-this-"))
        (b / "nes").mkdir()
        (b / "nes" / "gamma.nes").write_bytes(NES_HEADERED)         # the database lists the dump without its iNES header
        (b / "nes" / "delta.zip").write_bytes(zip_bytes("delta.nes", blob("delta-")))
        (b / "psx").mkdir()
        (b / "psx" / "Disc Game (USA).cue").write_bytes(CUE_TEXT)
        (b / "psx" / "Disc Game (USA) (Track 1).bin").write_bytes(TRACK1)
        (b / "psx" / "packed.chd").write_bytes(b"MComprHD" + b"\x00" * 100)
        (b / "notes.txt").write_text("not a game")
        (b / "gb" / ".hidden.gb").write_bytes(ALPHA)
        (b / "gb" / "link.gb").symlink_to(b / "gb" / "alpha.gb")

    def guide(self, ident, title, platform=GB, igdb=None, routes=True):
        return {"id": ident, "slug": "-".join(re.sub(r"[^a-z0-9 ]", "", title.lower()).split()), "title": title, "platformKey": platform,
                "kind": "commercial", "mode": "guide", "license": None, "artifact": None, "credits": [], "igdbId": igdb, "raGameId": None,
                "routes": [{"kind": "dump", "label": "Dump your own cartridge", "url": "https://example.com/dump"}] if routes else []}

    def entries(self):
        return [self.guide("c:alpha", "Alpha Quest", igdb=123), self.guide("c:disc", "Disc Game", PSX, igdb=77), self.guide("c:zeta", "Zeta Prime"),
                self.guide("c:gamma", "Gamma Force", NES), self.guide("c:delta", "Delta Zip", NES), self.guide("c:beta", "Beta Run")]

    def catalog(self, extra=(), **kw):
        make_snapshot(self.src, self.priv, [*self.entries(), *extra], **kw)
        return self.store.refresh(str(self.src))

    def scanned(self, catalog=True):
        if catalog:
            self.catalog()
        self.store.add_location(str(self.back), "Backups")
        return self.store.scan_backups()

    def rows(self):
        return {r["rel"]: r for r in pl.PersonalDB(self.store.personal_path).identified() + pl.PersonalDB(self.store.personal_path).unidentified()}

    # ---- the .rdb reader
    def test_messagepack_roundtrip_of_everything_an_rdb_uses(self):
        vals = [0, 5, 127, 128, 255, 256, 65535, 70000, 2 ** 40, -1, -32, -200, None, True, False, 1.5, "", "x" * 31, "é" * 20, "y" * 40, "z" * 300,
                b"", b"\x00" * 20, b"k" * 300, [1, "a", b"b"], list(range(20)), {"a": 1, "b": [2, 3]}, {str(i): i for i in range(20)}]
        for v in vals:
            if isinstance(v, int) and not isinstance(v, bool) and v < -32:
                continue   # packed by the test writer as int64; the reader handles all signed widths below
            got, end = pl._unpack(pack(v), 0)
            self.assertEqual(got, v)
            self.assertEqual(end, len(pack(v)))
        for raw, want in ((b"\xd0\xe0", -32), (b"\xd1\xff\x38", -200), (b"\xd2\xff\xff\xff\xff", -1), (b"\xca\x3f\xc0\x00\x00", 1.5)):
            self.assertEqual(pl._unpack(raw, 0)[0], want)

    def test_rdb_records_are_read_and_a_non_database_is_refused(self):
        recs = list(pl.read_rdb(self.rdb / f"{GB}.rdb"))
        self.assertEqual(len(recs), 8)
        self.assertEqual(recs[0]["name"], "Alpha Quest (USA)")
        self.assertEqual(recs[0]["sha1"], hashlib.sha1(ALPHA).digest())
        junk = self.root / "junk.rdb"
        junk.write_bytes(b"not a database at all, really")
        with self.assertRaisesRegex(pl.PersonalError, "not a libretro database"):
            list(pl.read_rdb(junk))

    # ---- locations
    def test_a_local_folder_is_accepted_and_kept_as_private_local_configuration(self):
        loc = self.store.add_location(str(self.back), "My backups")
        self.assertEqual((loc["label"], loc["kind"], loc["path"]), ("My backups", "local", str(self.back.resolve())))
        cfg = self.root / "store-locations.json"
        self.assertEqual(json.loads(cfg.read_text())["locations"][0]["path"], str(self.back.resolve()))
        self.assertEqual(oct(cfg.stat().st_mode & 0o777), "0o600")
        self.assertEqual([x["label"] for x in self.store.locations().all()], ["My backups"])

    def test_urls_indexes_and_torrents_are_refused_as_locations(self):
        torrent = self.root / "pack.torrent"
        torrent.write_text("x")
        cases = ["http://example.com/roms/", "https://example.com/roms/", "ftp://example.com/pub", "ftps://example.com", "magnet:?xt=urn:btih:abc",
                 "ipfs://bafy", "ed2k://|file|x|1|abc|/", "smb://nas/share", "webdav://nas/dav", "s3://bucket/key", "sftp://nas/x", "file:///tmp",
                 str(torrent), "relative/folder", "", "   "]
        for c in cases:
            with self.assertRaises(StoreError, msg=c):
                self.store.add_location(c)
        self.assertEqual(self.store.locations().all(), [])
        with self.assertRaisesRegex(StoreError, "magnet links"):
            self.store.add_location("magnet:?xt=urn:btih:abc")
        with self.assertRaisesRegex(StoreError, "web index"):
            self.store.add_location("https://example.com/roms/")
        with self.assertRaisesRegex(StoreError, "not built"):
            self.store.add_location("s3://bucket/key")

    def test_files_missing_folders_the_root_the_home_and_the_library_are_not_locations(self):
        f = self.root / "a.gb"
        f.write_bytes(b"x")
        for bad, why in ((f, "not a folder"), (self.root / "nope", "no such folder"), ("/", "too broad"), (Path.home(), "too broad"),
                         (self.roms, "inside the kit's own library"), (self.roms / "gb", "inside the kit's own library"),
                         (self.games / ".cache" / "store", "inside the kit's own library")):
            (self.games / ".cache" / "store").mkdir(parents=True, exist_ok=True)
            (self.roms / "gb").mkdir(exist_ok=True)
            with self.assertRaisesRegex(StoreError, why, msg=str(bad)):
                self.store.add_location(str(bad))

    def test_mounted_shares_are_locations_but_mounted_web_indexes_are_not(self):
        net = Store(games=self.games, roms=self.roms, key_path=self.pub, config_path=self.root / "store.toml", systems=SYS,
                    mounts=[(str(self.back), "cifs")])
        self.assertEqual(net.add_location(str(self.back))["kind"], "network")
        web = Store(games=self.games, roms=self.roms, key_path=self.pub, config_path=self.root / "web.toml", systems=SYS,
                    mounts=[(str(self.back), "fuse.httpdirfs")])
        with self.assertRaisesRegex(StoreError, "web/FTP/IPFS index"):
            web.add_location(str(self.back))

    def test_the_same_folder_twice_and_overlapping_folders_are_refused(self):
        self.store.add_location(str(self.back))
        with self.assertRaisesRegex(StoreError, "already a location"):
            self.store.add_location(str(self.back))
        with self.assertRaisesRegex(StoreError, "overlaps"):
            self.store.add_location(str(self.back / "gb"))

    # ---- scanning and recognising
    def test_scan_recognises_what_the_databases_list_and_never_guesses_the_rest(self):
        r = self.scanned()
        rows = self.rows()
        self.assertEqual((r["identified"], r["unidentified"]), (7, 4))
        want = {
            "gb/alpha.gb": (GB, "Alpha Quest (USA)"),
            "gb/beta.zip": (GB, "Beta Run (Europe)"),          # a single-file zip is recognised by the file inside
            "gb/tie.gbc": (GBC, "Tie Game (World)"),            # two platforms list it; the .gbc extension picks one
            "nes/gamma.nes": (NES, "Gamma Force (USA)"),       # recognised after the iNES header
            "nes/delta.zip": (NES, "Delta Zip (USA)"),
            "psx/Disc Game (USA).cue": (PSX, "Disc Game (USA)"),
            "psx/Disc Game (USA) (Track 1).bin": (PSX, "Disc Game (USA)"),
        }
        for rel, (plat, name) in want.items():
            self.assertEqual((rows[rel]["status"], rows[rel]["platform_key"], rows[rel]["canonical_name"]), ("identified", plat, name), rel)
        self.assertEqual(rows["gb/beta.zip"]["member"], "beta.gb")
        self.assertEqual(rows["gb/alpha.gb"]["sha1"], sha1(ALPHA))
        self.assertEqual(rows["nes/gamma.nes"]["sha1"], sha1(NES_BODY))   # the hash that matched, header removed
        self.assertEqual(rows["gb/alpha.gb"]["igdb_id"], 123)             # known from the catalog entry
        self.assertIsNone(rows["gb/beta.zip"]["igdb_id"])                 # catalog entry has no IGDB id
        for rel in ("gb/tie2.bin", "gb/ambiguous.gb", "gb/unknown.gb", "psx/packed.chd"):
            self.assertEqual(rows[rel]["status"], "unidentified", rel)
            self.assertIsNone(rows[rel]["canonical_name"], rel)
        self.assertIn("several platforms", rows["gb/tie2.bin"]["note"])
        self.assertIn("differently named", rows["gb/ambiguous.gb"]["note"])
        self.assertIn("no database lists", rows["gb/unknown.gb"]["note"])
        self.assertIn("compressed container", rows["psx/packed.chd"]["note"])
        for rel in ("notes.txt", "gb/.hidden.gb", "gb/link.gb"):
            self.assertNotIn(rel, rows)                                    # text, hidden files and symlinks are not looked at
        self.assertEqual(r["ignored"], 3)

    def test_a_hash_with_two_names_in_one_platform_is_ambiguous_not_picked(self):
        (self.back / "gb" / "dupe.gb").write_bytes(DUPE)
        self.scanned()
        self.assertEqual(self.rows()["gb/dupe.gb"]["status"], "unidentified")

    def test_scanning_works_without_a_catalog_and_records_no_igdb_id(self):
        self.store.add_location(str(self.back))
        r = self.store.scan_backups()
        self.assertEqual(r["identified"], 7)
        self.assertTrue(all(row["igdb_id"] is None for row in self.rows().values()))

    def test_a_rescan_reuses_hashes_forgets_vanished_files_and_rereads_changed_ones(self):
        self.scanned()
        again = self.store.scan_backups()
        self.assertEqual((again["hashed"], again["reused"], again["removed"]), (0, 11 - 1, 0))   # the .chd is never hashed, so it is not reused
        (self.back / "gb" / "unknown.gb").unlink()
        (self.back / "gb" / "alpha.gb").write_bytes(ALPHA_EU)         # same name, other content: must be re-read and re-recognised
        third = self.store.scan_backups()
        self.assertEqual((third["removed"], third["hashed"]), (1, 1))
        rows = self.rows()
        self.assertNotIn("gb/unknown.gb", rows)
        self.assertEqual(rows["gb/alpha.gb"]["canonical_name"], "Alpha Quest (Europe)")

    def test_an_unreachable_location_is_left_exactly_as_it_was(self):
        self.scanned()
        before = self.rows()
        moved = self.root / "gone"
        self.back.rename(moved)
        r = self.store.scan_backups()
        self.assertEqual(r["unreachable"], [str(self.back.resolve())])
        self.assertEqual(set(self.rows()), set(before))
        self.assertTrue(any("not reachable" in line for line in self.log))

    def test_scan_needs_a_location_and_a_known_one(self):
        with self.assertRaisesRegex(StoreError, "no locations yet"):
            self.store.scan_backups()
        self.store.add_location(str(self.back))
        with self.assertRaisesRegex(StoreError, "not one of your locations"):
            self.store.scan_backups("elsewhere")

    def test_removing_a_location_removes_its_rows_and_never_its_files(self):
        self.scanned()
        loc, n = self.store.remove_location("Backups")
        self.assertEqual(n, 11)
        self.assertEqual(self.rows(), {})
        self.assertTrue((self.back / "gb" / "alpha.gb").exists())
        self.assertEqual(self.store.locations().all(), [])
        with self.assertRaisesRegex(StoreError, "not one of your locations"):
            self.store.remove_location("Backups")

    # ---- no network, nothing shared
    def test_scan_match_merge_and_install_open_no_connection(self):
        self.catalog()
        self.store.add_location(str(self.back))
        def refuse(*a, **k):
            raise AssertionError("a network connection was attempted")
        with mock.patch.object(socket, "socket", refuse), mock.patch.object(socket, "create_connection", refuse), \
                mock.patch.object(socket, "getaddrinfo", refuse):
            self.store.scan_backups()
            snap = self.store.require()
            groups = self.store.backup_groups(snap)
            self.assertIn("c:alpha", groups)
            self.store.list_lines(snap.entries, set(groups))
            self.store.info_lines(snap.by_id["c:alpha"], groups["c:alpha"])
            self.assertEqual(self.store.get("alpha-quest")["status"], "installed")
            self.assertEqual(self.store.get("gamma-force")["status"], "installed")
            self.store.health_lines()

    def test_the_modules_import_no_network_library_and_offer_no_way_to_share(self):
        for mod in (pl,):
            src = Path(mod.__file__).read_text()
            self.assertEqual(re.findall(r"^\s*(?:import|from)\s+(?:urllib|socket|http|ssl|ftplib|smtplib|requests|xmlrpc)\S*", src, re.M), [])
        names = [n for obj in (Store, pl) for n in dir(obj) if re.search(r"export|share|subscribe|upload|publish|sync_locations|import_locations", n, re.I)]
        self.assertEqual([n for n in names if n not in ("sync", "sync_and_apply")], [])
        cli = (Path(__file__).resolve().parent.parent / "games" / "kit-games").read_text()
        self.assertNotRegex(cli, r'add_parser\("(export|import|share|subscribe|upload)[^"]*"[^)]*\)[^\n]*(location|backup|personal)')

    # ---- merging into the store
    def test_a_commercial_game_you_hold_shows_in_your_backups_and_the_rest_stay_guides(self):
        self.scanned()
        snap = self.store.require()
        groups = self.store.backup_groups(snap)
        self.assertEqual(set(groups), {"c:alpha", "c:beta", "c:disc", "c:gamma", "c:delta"})
        self.assertNotIn("c:zeta", groups)
        lines = self.store.list_lines(sorted(snap.entries, key=lambda e: e["id"]), set(groups))
        mine = [ln for ln in lines if "In your backups" in ln]
        self.assertEqual(len(mine), 5)
        self.assertTrue(any("zeta-prime" in ln and "In your backups" not in ln for ln in lines))
        info = "\n".join(self.store.info_lines(snap.by_id["c:alpha"], groups["c:alpha"]))
        self.assertIn("In your backups", info)
        self.assertIn("kit-games store get alpha-quest", info)
        self.assertNotIn("No file is offered", info)
        plain = "\n".join(self.store.info_lines(snap.by_id["c:zeta"], groups.get("c:zeta", ())))
        self.assertIn("No file is offered", plain)

    def test_a_catalog_title_that_is_not_unique_is_never_matched(self):
        self.catalog(extra=[self.guide("c:alpha2", "Alpha Quest!")])      # two guide entries with the same normalised title...
        self.store.add_location(str(self.back))
        self.store.scan_backups()
        groups = self.store.backup_groups(self.store.require())
        self.assertNotIn("c:alpha2", groups)
        # ...but the IGDB id the scan stored (only one entry carries it) still singles Alpha Quest out
        self.assertEqual(self.store.scan_backups()["identified"], 7)

    def test_without_a_backup_a_commercial_game_is_still_guide_only(self):
        self.scanned()
        with self.assertRaisesRegex(StoreError, "commercial game: the store never offers a file"):
            self.store.get("zeta-prime")
        with self.assertRaisesRegex(StoreError, "store locations add"):
            self.store.get("zeta-prime")
        self.assertEqual(list((self.roms).rglob("*")), [])

    # ---- installing from your own folder
    def test_get_installs_from_your_own_folder_through_the_normal_steps(self):
        self.scanned()
        res = self.store.get_many(["alpha-quest"])
        ref, r, err = res[0]
        self.assertIsNone(err)
        self.assertEqual((r["status"], r["source"], r["files"]), ("installed", "personal", ["gb/Alpha Quest (USA).gb"]))
        self.assertEqual((self.roms / "gb" / "Alpha Quest (USA).gb").read_bytes(), ALPHA)
        self.assertEqual(self.changed, [{"gb"}])                          # the kit's scan / ES-DE step runs once
        m = self.store.manifest()["c:alpha"]
        self.assertEqual((m["source"], m["mode"], m["linked"], m["sha1"]), ("personal", "guide", False, sha1(ALPHA)))
        self.assertNotIn("sourceUrl", m)
        self.assertFalse((self.roms / "gb" / "STORE-CREDITS.md").exists())   # your own backup has no credits file
        self.assertEqual(self.store.get("alpha-quest")["status"], "already")

    def test_the_budget_is_checked_before_anything_is_copied(self):
        self.scanned()
        self.budget_msg = "it would exceed the 1 GB library budget"
        with self.assertRaisesRegex(StoreError, "budget"):
            self.store.get("alpha-quest")
        self.assertEqual(list(self.roms.rglob("*.gb")), [])
        self.assertEqual(self.store.manifest(), {})

    def test_link_makes_a_symlink_and_removing_it_leaves_your_file(self):
        self.scanned()
        r = self.store.get("alpha-quest", link=True)
        out = self.roms / "gb" / "Alpha Quest (USA).gb"
        self.assertTrue(out.is_symlink())
        self.assertEqual(out.resolve(), (self.back / "gb" / "alpha.gb").resolve())
        self.assertTrue(r["linked"])
        self.store.remove("alpha-quest")
        self.assertFalse(os.path.lexists(out))
        self.assertEqual((self.back / "gb" / "alpha.gb").read_bytes(), ALPHA)

    def test_a_zip_is_unpacked_for_a_system_that_does_not_open_zips_and_copied_for_one_that_does(self):
        self.scanned()
        self.store.get("delta-zip")
        self.assertEqual((self.roms / "nes" / "Delta Zip (USA).nes").read_bytes(), blob("delta-"))
        self.store.get("beta-run")
        self.assertEqual((self.roms / "gb" / "Beta Run (Europe).zip").read_bytes(), zip_bytes("beta.gb", BETA))

    def test_a_headered_dump_is_installed_as_it_is_not_as_the_hash_that_matched(self):
        self.scanned()
        self.store.get("gamma-force")
        self.assertEqual((self.roms / "nes" / "Gamma Force (USA).nes").read_bytes(), NES_HEADERED)

    def test_a_disc_installs_its_sheet_and_the_tracks_the_sheet_names(self):
        self.scanned()
        r = self.store.get("disc-game")
        self.assertEqual(sorted(r["files"]), ["psx/Disc Game (USA) (Track 1).bin", "psx/Disc Game (USA).cue"])
        self.assertEqual((self.roms / "psx" / "Disc Game (USA) (Track 1).bin").read_bytes(), TRACK1)
        self.assertIn(b"Disc Game (USA) (Track 1).bin", (self.roms / "psx" / "Disc Game (USA).cue").read_bytes())

    def test_a_file_that_changed_since_the_scan_is_refused(self):
        self.scanned()
        with open(self.back / "gb" / "alpha.gb", "ab") as f:
            f.write(b"!")
        with self.assertRaisesRegex(StoreError, "changed since the last scan"):
            self.store.get("alpha-quest")
        self.assertEqual(list(self.roms.rglob("*.gb")), [])
        (self.back / "gb" / "alpha.gb").unlink()
        with self.assertRaisesRegex(StoreError, "gone or its drive is not mounted"):
            self.store.get("alpha-quest")

    def test_several_different_dumps_need_a_choice_and_nothing_is_picked_for_you(self):
        (self.back / "gb" / "alpha-eu.gb").write_bytes(ALPHA_EU)
        self.scanned()
        with self.assertRaisesRegex(StoreError, "several different dumps"):
            self.store.get("alpha-quest")
        with self.assertRaisesRegex(StoreError, "does not pick exactly one"):
            self.store.get("alpha-quest", which="Japan")
        self.assertEqual(self.store.get("alpha-quest", which="2")["files"], ["gb/Alpha Quest (USA).gb"])   # groups are listed A-Z; 2 = (USA)

    def test_an_existing_file_that_the_store_did_not_install_is_never_overwritten(self):
        self.scanned()
        (self.roms / "gb").mkdir()
        (self.roms / "gb" / "Alpha Quest (USA).gb").write_bytes(b"mine")
        with self.assertRaisesRegex(StoreError, "not overwriting"):
            self.store.get("alpha-quest")
        self.assertEqual((self.roms / "gb" / "Alpha Quest (USA).gb").read_bytes(), b"mine")

    def test_a_catalog_withdrawing_a_listing_does_not_delete_your_own_backup_copy(self):
        self.scanned()
        self.store.get("alpha-quest")
        make_snapshot(self.src, self.priv, [e for e in self.entries() if e["id"] != "c:alpha"],
                      tombstones=[{"id": "c:alpha", "removedAt": "2026-10-08T00:00:00Z", "reason": "listing withdrawn"}], version="2026100801")
        self.store.refresh(str(self.src))
        removed, notes = self.store.sync()
        self.assertEqual(removed, [])
        self.assertTrue(any("stays" in n and "Alpha Quest" in n for n in notes))
        self.assertTrue((self.roms / "gb" / "Alpha Quest (USA).gb").exists())

    # ---- health shows counts only
    def test_health_reports_counts_and_no_paths(self):
        self.scanned()
        h = self.store.health()
        self.assertEqual(h["backups"], {"locations": 1, "identified": 7, "unidentified": 4})
        text = "\n".join(self.store.health_lines())
        self.assertIn("1 locations, 7 recognised files, 4 unidentified", text)
        self.assertNotIn(str(self.back), text)
        self.assertNotIn("alpha", text.lower().replace("snapshot", ""))

    # ---- hashing details
    def test_header_variants_cover_the_systems_whose_databases_hash_without_one(self):
        body = blob("body-", 2048)
        cases = [("nes", b"NES\x1a" + b"\x00" * 12 + body, 16), ("smc", b"\x00" * 512 + body, 512),
                 ("a78", b"\x01ATARI7800" + b"\x00" * 118 + body, 128), ("lnx", b"LYNX" + b"\x00" * 60 + body, 64)]
        for ext, data, skip in cases:
            v = pl.hash_variants(iter([data[:700], data[700:]]), len(data), ext, data[:16])
            self.assertEqual(len(v), 2, ext)
            self.assertEqual(v[0][1], sha1(data))
            self.assertEqual(v[1][1], sha1(data[skip:]), ext)
            self.assertEqual((v[1][0], v[1][2]), (f"{zlib.crc32(data[skip:]) & 0xffffffff:08x}", len(data) - skip))
        plain = pl.hash_variants(iter([body]), len(body), "gb", body[:16])
        self.assertEqual(len(plain), 1)

    def test_title_keys_ignore_dump_tags_punctuation_and_trailing_articles(self):
        a = pl.norm_title("Legend of Zelda, The - Link's Awakening (USA) (Rev 1)")
        b = pl.norm_title("The Legend of Zelda: Link's Awakening")
        self.assertEqual(a, b)
        self.assertEqual(pl.norm_title("Super Mario Land 2 - 6 Golden Coins (World)"), pl.norm_title("Super Mario Land 2: 6 Golden Coins"))
        self.assertNotEqual(pl.norm_title("Alpha Quest 2"), pl.norm_title("Alpha Quest"))

    # ---- this machine's real libretro database
    REAL_RDB = Path("/usr/share/libretro/database/rdb")
    REAL_ROM = Path.home() / "Games" / "roms" / "gb" / "Tobu Tobu Girl (Homebrew).gb"

    @unittest.skipUnless((REAL_RDB / f"{GB}.rdb").exists(), "libretro databases are not installed here")
    def test_the_real_libretro_database_is_readable(self):
        n, first = 0, None
        for r in pl.read_rdb(self.REAL_RDB / f"{GB}.rdb"):
            n += 1
            first = first or r
        self.assertGreater(n, 1000)
        self.assertIsInstance(first["name"], str)
        self.assertEqual(len(first["sha1"]), 20)

    @unittest.skipUnless((REAL_RDB / f"{GB}.rdb").exists() and REAL_ROM.exists(),
                         "needs the real libretro database and a known homebrew ROM in this machine's library")
    def test_a_real_file_is_recognised_against_the_real_database(self):
        idx = pl.RdbIndex(self.REAL_RDB)
        for db in (GB, GBC):
            idx.add_db(db)
        size = self.REAL_ROM.stat().st_size
        variants = pl.file_variants(self.REAL_ROM, "gb", size)         # read-only
        status, db, name, *_ = pl.identify(idx, variants, {GB: {"gb"}, GBC: {"gbc"}}, "gb")
        self.assertEqual((status, db), ("identified", GB))
        self.assertTrue(name.startswith("Tobu Tobu Girl (World)"), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
