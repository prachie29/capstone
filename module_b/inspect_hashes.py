import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "datasets unused"
FILE_INFO_PATH = DATA_DIR / "file_info.json"

FUNCTION_NAME = "vfswrap_fsctl"
COMMIT_ID = "eb50fb8f3bf670bd7d1cf8fd4368ef4a73083696"


def main():
    with FILE_INFO_PATH.open("r", encoding="utf-8") as file:
        file_info = json.load(file)

    print(f"Metadata entries: {len(file_info)}")

    # First, inspect entries whose paths suggest they belong to Samba.
    samba_entries = [
        (func_hash, info)
        for func_hash, info in file_info.items()
        if "samba" in (
            info.get("local_file_path", "")
            + info.get("project_file_path", "")
        ).lower()
    ]

    print(f"Samba-related metadata entries: {len(samba_entries)}")

    matches = []

    for func_hash, info in file_info.items():
        source_path = DATA_DIR / info.get("local_file_path", "")

        if not source_path.is_file():
            continue

        try:
            source_code = source_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        if "vfswrap_fsctl" in source_code:
            matches.append((func_hash, info, source_path))

    print(f"Files containing vfswrap_fsctl: {len(matches)}")

    for func_hash, info, source_path in matches:
        print(func_hash, info["project_file_path"], source_path)