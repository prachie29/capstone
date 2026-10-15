import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics import f1_score, precision_score, recall_score

from common.dataset import load_dataset, select_samples
from module_a.prompt_a import build_prompt

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATASET_PATH = (
    PROJECT_ROOT / "datasets unused" / "primevul_test.jsonl"
)

MODEL = "gpt-4o-mini"
SAMPLE_SIZE = 10
RANDOM_SEED = 42

load_dotenv(PROJECT_ROOT / ".env")


def validate_prediction(result: dict) -> None:
    """Validate the model's prediction and response fields."""

    required_fields = {
        "prediction",
        "confidence",
        "reasoning_summary",
    }

    if set(result) != required_fields:
        raise ValueError(
            f"Unexpected response fields: {set(result)}"
        )

    if result["prediction"] not in {
        "vulnerable",
        "non-vulnerable",
    }:
        raise ValueError("Invalid prediction label.")

    confidence = result["confidence"]

    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise ValueError(
            "Confidence must be a number between 0 and 1."
        )

    if not isinstance(result["reasoning_summary"], str):
        raise ValueError(
            "reasoning_summary must be a string."
        )


def predict_vulnerability(client: OpenAI, code: str) -> dict:
    """Send source code to GPT-4o mini and return its prediction."""

    prompt = build_prompt(code)
    start_time = time.perf_counter()

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        text={"format": {"type": "json_object"}},
    )

    latency = time.perf_counter() - start_time

    result = json.loads(response.output_text)
    validate_prediction(result)

    return {
        "prediction": (
            1 if result["prediction"] == "vulnerable" else 0
        ),
        "confidence": result["confidence"],
        "reasoning_summary": result["reasoning_summary"],
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_seconds": round(latency, 3),
    }


def evaluate(results: list[dict]) -> dict:
    """Calculate vulnerability-detection metrics."""

    if not results:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "evaluated": 0,
        }

    y_true = [result["ground_truth"] for result in results]
    y_pred = [result["prediction"] for result in results]

    return {
        "precision": precision_score(
            y_true, y_pred, pos_label=1, zero_division=0
        ),
        "recall": recall_score(
            y_true, y_pred, pos_label=1, zero_division=0
        ),
        "f1": f1_score(
            y_true, y_pred, pos_label=1, zero_division=0
        ),
        "evaluated": len(results),
    }


def run(n_samples: int = SAMPLE_SIZE) -> None:
    """Run the code-only baseline on a reproducible sample."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Check your .env file."
        )

    client = OpenAI(api_key=api_key)

    dataset = load_dataset(DATASET_PATH)

    selected_samples = select_samples(
        dataset,
        sample_size=n_samples,
        seed=RANDOM_SEED,
    )

    results = []
    errors = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_latency = 0.0

    print(f"Model: {MODEL}")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Total dataset samples: {len(dataset)}")
    print(f"Selected samples: {len(selected_samples)}")
    print("=" * 55)

    for i, sample in enumerate(selected_samples, start=1):
        sample_id = sample["idx"]
        code = sample["func"]
        ground_truth = int(sample["target"])

        print(f"\n[{i}/{len(selected_samples)}] Sample ID: {sample_id}")

        if not code or not code.strip():
            errors += 1
            print("  ERROR: Empty source code; sample not evaluated.")
            continue

        try:
            prediction = predict_vulnerability(client, code)

            pred_label = prediction["prediction"]
            correct = pred_label == ground_truth

            result = {
                "sample_id": sample_id,
                "ground_truth": ground_truth,
                **prediction,
                "correct": correct,
            }

            results.append(result)

            total_input_tokens += prediction["input_tokens"]
            total_output_tokens += prediction["output_tokens"]
            total_latency += prediction["latency_seconds"]

            print(f"  Actual label : {ground_truth}")
            print(f"  Prediction   : {pred_label}")
            print(f"  Correct      : {correct}")
            print(f"  Confidence   : {prediction['confidence']}")
            print(f"  Input tokens : {prediction['input_tokens']}")
            print(f"  Output tokens: {prediction['output_tokens']}")
            print(f"  Latency      : {prediction['latency_seconds']} s")
            print(f"  Explanation  : {prediction['reasoning_summary']}")

        except Exception as error:
            errors += 1
            print(
                f"  ERROR: {type(error).__name__}: {error}"
            )

    metrics = evaluate(results)

    print("\n" + "=" * 55)
    print("MODULE A — CODE-ONLY BASELINE RESULTS")
    print("=" * 55)

    print(f"Selected samples : {len(selected_samples)}")
    print(f"Evaluated        : {metrics['evaluated']}")
    print(f"Failed/skipped   : {errors}")
    print(f"Precision        : {metrics['precision']:.3f}")
    print(f"Recall           : {metrics['recall']:.3f}")
    print(f"F1 score         : {metrics['f1']:.3f}")
    print(f"Input tokens     : {total_input_tokens}")
    print(f"Output tokens    : {total_output_tokens}")
    print(f"Total tokens     : {total_input_tokens + total_output_tokens}")

    if metrics["evaluated"] > 0:
        print(f"Avg latency      : {total_latency / metrics['evaluated']:.3f} s")

    print("=" * 55)
    print("Results were kept in memory; nothing was saved to disk.")


if __name__ == "__main__":
    import sys

    sample_count = int(sys.argv[1]) if len(sys.argv) > 1 else SAMPLE_SIZE
    run(sample_count)
