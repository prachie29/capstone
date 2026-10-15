import json
import random
from pathlib import Path


def load_dataset(dataset_path: Path) -> list[dict]:
    """Load samples from a JSONL dataset."""
    samples = []

    with dataset_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {dataset_path}, line {line_number}"
                ) from error

    return samples


def select_samples(
    samples: list[dict],
    sample_size: int,
    seed: int = 42,
) -> list[dict]:
    """Select a reproducible random subset of samples."""
    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero.")

    if sample_size > len(samples):
        raise ValueError(
            f"Requested {sample_size} samples, "
            f"but dataset contains only {len(samples)}."
        )

    rng = random.Random(seed)
    return rng.sample(samples, sample_size)
