from pathlib import Path

from common.dataset import load_dataset, select_samples

dataset_path = Path("datasets unused/primevul_test.jsonl")

samples = load_dataset(dataset_path)
selected = select_samples(samples, sample_size=10, seed=42)

print("Total samples:", len(samples))
print("Selected samples:", len(selected))
print("Selected IDs:", [sample["idx"] for sample in selected])