import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from common.dataset import load_dataset, select_samples
from common.schemas import VulnerabilityPrediction
from module_c.analyzers_c import analyze_code
from module_c.prompt_c import build_prompt

PROJECT_ROOT = Path(__file__).parent.parent

DATASET_PATH = (
    PROJECT_ROOT / "datasets unused" / "primevul_test.jsonl"
)

MODEL = "gpt-4o-mini"
SAMPLE_SIZE = 5
RANDOM_SEED = 42

load_dotenv(PROJECT_ROOT / ".env")




def predict_vulnerability(client: OpenAI, code: str, findings: str) -> dict:
    prompt = build_prompt(code, findings)

    start_time = time.perf_counter()

    response = client.responses.parse(
        model=MODEL,
        input=prompt,
        text_format=VulnerabilityPrediction,
    )

    latency = time.perf_counter() - start_time
    result = response.output_parsed

    return {
        "is_vulnerable": result.is_vulnerable,
        "confidence": result.confidence,
        "reasoning_summary": result.reasoning_summary,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_seconds": round(latency, 3),
    }

def evaluate_predictions(y_true: list[int], y_pred: list[int])->dict:

    return {
        "precision": precision_score(y_true, y_pred, zero_division= 0),

        "recall": recall_score(y_true, y_pred, zero_division=0),

        "f1": f1_score(y_true, y_pred, zero_division=0),

        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist()

    }


if __name__ == "__main__":
    dataset = load_dataset(DATASET_PATH)
    samples = select_samples(dataset, SAMPLE_SIZE, RANDOM_SEED)

    client = OpenAI()

    results = []
    y_true = []
    y_pred = []

    for sample in samples:
        code = sample["func"]
        ground_truth = sample["target"]


        analyzer_results = analyze_code(code, language="c")

        all_findings = []

        for tool, analyzer_result in analyzer_results.items():
            finding_text = (
                f"Tool: {tool.upper()}\n"
                f"Success: {analyzer_result['success']}\n"
                f"Findings: {analyzer_result['findings']}"
            )
            all_findings.append(finding_text)

        findings = "\n\n".join(all_findings)

 
        prediction = predict_vulnerability(client, code, findings)
        llm_prediction = int(prediction["is_vulnerable"])

        y_true.append(ground_truth)
        y_pred.append(llm_prediction)

        results.append({
            "sample_id": sample["idx"],
            "ground_truth": ground_truth,
            "prediction": prediction,
            "analyzer_results": analyzer_results,
        })

    evaluation = evaluate_predictions(y_true, y_pred)

    print("\n--- Module C Evaluation ---")
    print(f"Samples evaluated: {len(results)}")
    print(f"Precision: {evaluation['precision']:.4f}")
    print(f"Recall: {evaluation['recall']:.4f}")
    print(f"F1-score: {evaluation['f1']:.4f}")
    print(f"Confusion matrix:\n{evaluation['confusion_matrix']}")