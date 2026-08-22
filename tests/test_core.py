import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "deskpilot"))
import core

class DeskPilotCoreTests(unittest.TestCase):
    def test_category(self):
        self.assertEqual(core.category_for(Path("photo.PNG")), "Images")
        self.assertEqual(core.category_for(Path("notes.md")), "Documents")
        self.assertEqual(core.category_for(Path("script.ps1")), "Code")

    def test_organize_preview_does_not_move(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "a.jpg"
            source.write_bytes(b"x")
            plan = core.build_organize_plan(root)
            self.assertTrue(source.exists())
            self.assertEqual(plan[0].category, "Images")
            self.assertEqual(plan[0].destination.parent.name, "Images")

    def test_exact_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.bin").write_bytes(b"same")
            (root / "b.bin").write_bytes(b"same")
            (root / "c.bin").write_bytes(b"different")
            groups = core.find_duplicates(root)
            self.assertEqual(len(groups), 1)
            self.assertEqual({p.name for p in groups[0]}, {"a.bin", "b.bin"})

    def test_quick_search(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "Halloween Design.png").write_bytes(b"x")
            (root / "other.txt").write_bytes(b"x")
            result = core.quick_search(root, "halloween")
            self.assertEqual([p.name for p in result], ["Halloween Design.png"])

    def test_recent_activity_orders_newest_first(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old.txt"
            new = root / "new.txt"
            old.write_text("o")
            new.write_text("n")
            now = datetime.now().timestamp()
            os.utime(old, (now - 3600, now - 3600))
            os.utime(new, (now, now))
            result = core.recent_activity(root, days=1)
            self.assertEqual([x[0].name for x in result], ["new.txt", "old.txt"])

    def test_attention_queue_finds_partial_and_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            partial = root / "video.crdownload"
            empty = root / "empty.txt"
            partial.write_bytes(b"partial")
            empty.write_bytes(b"")
            old = (datetime.now() - timedelta(days=2)).timestamp()
            os.utime(partial, (old, old))
            items = core.attention_queue(root)
            reasons = {item.path.name: item.reason for item in items}
            self.assertIn("Leftover partial", reasons["video.crdownload"])
            self.assertEqual(reasons["empty.txt"], "Empty file")

    def test_folder_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.png").write_bytes(b"123")
            (root / "b.txt").write_bytes(b"45")
            snap = core.folder_snapshot(root)
            self.assertEqual(snap["files"], 2)
            self.assertEqual(snap["bytes"], 5)
            self.assertEqual(snap["categories"]["Images"], 1)
            self.assertEqual(snap["categories"]["Documents"], 1)

if __name__ == "__main__":
    unittest.main()
