import tarfile
import tempfile
import unittest
from pathlib import Path

from package import PACKAGE_FILES, PACKAGE_DIRS, create_package


class PackageTest(unittest.TestCase):
    def test_package_file_list_includes_runtime_entrypoints(self):
        self.assertIn("wecom_ai_bot.py", PACKAGE_FILES)
        self.assertIn("report.py", PACKAGE_FILES)
        self.assertIn("yarb.py", PACKAGE_FILES)
        self.assertIn("requirements.txt", PACKAGE_FILES)
        self.assertIn("rss", PACKAGE_DIRS)
        self.assertIn("archive", PACKAGE_DIRS)

    def test_create_package_excludes_local_environment_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "dist"
            for name in PACKAGE_FILES:
                (root / name).write_text(name, encoding="utf-8")
            for dirname in PACKAGE_DIRS:
                (root / dirname).mkdir(parents=True, exist_ok=True)
            (root / "rss" / "CustomRSS.opml").write_text("<opml />", encoding="utf-8")
            (root / "archive" / "2026").mkdir(parents=True)
            (root / "archive" / "2026" / "2026-05-28.md").write_text("# test", encoding="utf-8")
            (root / ".venv").mkdir()
            (root / ".venv" / "secret.txt").write_text("no", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "x.pyc").write_text("no", encoding="utf-8")

            package_path = create_package(root=root, output_dir=out, version="test")

            with tarfile.open(package_path, "r:gz") as tar:
                names = tar.getnames()

        self.assertIn("qzvulner/wecom_ai_bot.py", names)
        self.assertIn("qzvulner/rss/CustomRSS.opml", names)
        self.assertIn("qzvulner/archive/2026/2026-05-28.md", names)
        self.assertNotIn("qzvulner/.venv/secret.txt", names)
        self.assertNotIn("qzvulner/__pycache__/x.pyc", names)


if __name__ == "__main__":
    unittest.main()
