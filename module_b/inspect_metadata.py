import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FILE_INFO_PATH = PROJECT_ROOT / "datasets unused" / "file_info.json"

with FILE_INFO_PATH.open("r", encoding="utf-8") as file:
    file_info = json.load(file)

print(f"Total metadata entries: {len(file_info)}")

# Inspect the first metadata entry.
first_key = next(iter(file_info))
first_entry = file_info[first_key]

print("\n--- First metadata entry ---")
print(f"Function hash: {first_key}")
print(json.dumps(first_entry, indent=2))

# Inspect available metadata fields.
field_counts = Counter()

for entry in file_info.values():
    field_counts.update(entry.keys())

print("\n--- Metadata fields ---")
for field, count in field_counts.most_common():
    print(f"{field}: {count}/{len(file_info)} entries")

# Check how many unique projects and source files exist.
projects = set()
file_paths = set()

for entry in file_info.values():
    local_path = entry.get("local_file_path", "")
    project_path = entry.get("project_file_path", "")

    if local_path:
        parts = Path(local_path).parts
        if len(parts) >= 2:
            projects.add(parts[-2])

    if project_path:
        file_paths.add(project_path)

print(f"\nUnique project directories (approximate): {len(projects)}")
print(f"Unique project file paths: {len(file_paths)}")

# Check whether metadata includes commit information.
commit_fields = [
    field for field in field_counts
    if "commit" in field.lower() or "revision" in field.lower()
]

print(f"\nCommit/revision-related fields: {commit_fields}")
