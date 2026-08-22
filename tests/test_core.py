from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "deskpilot"))
import core

def test_category_for_known_and_unknown(tmp_path):
    assert core.category_for(Path("photo.PNG")) == "Images"
    assert core.category_for(Path("thing.xyzabc")) == "Other"

def test_build_plan_does_not_move_files(tmp_path):
    source = tmp_path / "receipt.pdf"; source.write_text("hello")
    plan = core.build_organize_plan(tmp_path)
    assert len(plan) == 1 and plan[0].category == "Documents" and source.exists()

def test_duplicate_detection(tmp_path):
    (tmp_path / "a.txt").write_text("same"); (tmp_path / "b.txt").write_text("same"); (tmp_path / "c.txt").write_text("different")
    groups = core.find_duplicates(tmp_path)
    assert len(groups) == 1 and {p.name for p in groups[0]} == {"a.txt", "b.txt"}

def test_quick_search(tmp_path):
    (tmp_path / "CraftyBrother_final.png").write_text("x"); (tmp_path / "notes.txt").write_text("x")
    assert [p.name for p in core.quick_search(tmp_path, "crafty")] == ["CraftyBrother_final.png"]
