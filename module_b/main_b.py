from pathlib import Path
from collections import Counter

from common.dataset import load_dataset, select_samples

PROJECT_ROOT = Path('__file__').parent
DATASET_PATH = PROJECT_ROOT / "datasets unused" / "primevul_test.jsonl"

dataset = load_dataset(DATASET_PATH)

pilot = select_samples(dataset, sample_size=10, seed=42)

print(f"Total dataset samples: {len(dataset)}")
print(f"Pilot samples: {len(pilot)}")


print("\n--- Project Distribution ---")
for project, count in Counter(s["project"] for s in pilot).items():
    print(f"{project}: {count}")

print("\n--- Pilot Samples ---")
for sample in pilot:
    print(
        f"Sample ID: {sample['idx']} | "
        f"Project: {sample['project']} | "
        f"Commit: {sample['commit_id']}"
    )
    print(f"Function preview: {sample['func'][:150]!r}")
    print("-" * 70)

