#!/usr/bin/python3

import argparse
import tarfile
from datetime import datetime
from pathlib import Path


PACKAGE_FILES = [
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "requirements.txt",
    "config.json",
    "_config.yml",
    "install.sh",
    "utils.py",
    "yarb.py",
    "report.py",
    "llm.py",
    "web_search.py",
    "diagnose_tavily.py",
    "wecom_ai_bot.py",
    "today.md",
]

PACKAGE_DIRS = [
    "rss",
    "archive",
]

EXCLUDE_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".DS_Store",
    "dist",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".tar",
    ".gz",
    ".zip",
}


def should_include(path: Path) -> bool:
    return not any(part in EXCLUDE_NAMES for part in path.parts) and path.suffix not in EXCLUDE_SUFFIXES


def create_package(root: Path | str = ".", output_dir: Path | str = "dist", version: str | None = None) -> Path:
    root = Path(root).resolve()
    output_dir = Path(output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    version = version or datetime.now().strftime("%Y%m%d-%H%M%S")
    # 包文件名带时间戳（方便版本区分），但包内目录固定为 qzvulner（方便解压覆盖）
    archive_dir = "qzvulner"
    package_path = output_dir / f"qzvulner-{version}.tar.gz"

    with tarfile.open(package_path, "w:gz") as tar:
        for filename in PACKAGE_FILES:
            path = root / filename
            if path.exists() and should_include(path.relative_to(root)):
                tar.add(path, arcname=f"{archive_dir}/{filename}")

        for dirname in PACKAGE_DIRS:
            directory = root / dirname
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                rel = path.relative_to(root)
                if path.is_file() and should_include(rel):
                    tar.add(path, arcname=f"{archive_dir}/{rel}")

    return package_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a deployable qzvulner package.")
    parser.add_argument("--output-dir", default="dist", help="Directory for the .tar.gz package.")
    parser.add_argument("--version", help="Package version suffix. Defaults to current timestamp.")
    args = parser.parse_args()

    package_path = create_package(output_dir=args.output_dir, version=args.version)
    print(package_path)


if __name__ == "__main__":
    main()
