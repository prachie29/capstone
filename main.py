from datasets import load_dataset


ds = load_dataset("Code-TREAT/PrimeVul_original")


print("AVAILABLE SPLITS")
print(list(ds.keys()))

for split_name, split_data in ds.items():
    print(f"\n{'=' * 50}")
    print(f"SPLIT: {split_name}")
    print(f"{'=' * 50}")

    # Number of rows
    print("Number of samples:", len(split_data))

    # Column names
    print("\nColumn names:")
    print(split_data.column_names)
    print(len(split_data.column_names))

    # Data types and feature definitions
    print("\nFeature schema:")
    print(split_data.features)
