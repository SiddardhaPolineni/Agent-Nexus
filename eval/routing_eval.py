"""
Offline Evaluation Pipeline - Routing Agent
Evaluates the supervisor routing + guardrails against a golden dataset.
Outputs: Excel file with Results, Metrics (Precision/Recall/F1), and Distribution.

Usage: python -m eval.routing_eval
"""

import pandas as pd
import os
from config import GOLDEN_DATASET_PATH, LLM
from src.guards.guardrails import run_guardrails
from src.prompts.agent_prompts import SUPERVISOR_PROMPT, REASONING_PROMPT


# ============================
# 1. Prediction Logic
# ============================

def get_predicted_intent(query: str) -> tuple[str,str]:
    """Run guardrails and supervisor routing on a single query."""
    guardrail_check = run_guardrails(query)

    if not guardrail_check["passed"]:
        return "blocked", "Query blocked by guardrails" + guardrail_check['message']

    routing_prompt = REASONING_PROMPT.format(query=query)
    response = LLM.invoke(routing_prompt)
    content = response.content.strip()

    # Parse intent and reasoning from response
    intent = ""
    reasoning = ""

    for line in content.split("\n"):
        if line.lower().startswith("intent:"):
            intent = line.split(":", 1)[1].strip().lower().strip("'\"")
        elif line.lower().startswith("reasoning:"):
            reasoning = line.split(":", 1)[1].strip()
    
    # Fallback
    if not intent:
        intent = content.strip().lower().strip("'\"")
    
    if not reasoning:
        reasoning = "No reasoning provided"

    return intent, reasoning


# ============================
# 2. Run Evaluation
# ============================

def run_routing_eval(golden_dataset_df: pd.DataFrame, results_path: str) -> tuple[pd.DataFrame, str]:
    """
    Run routing eval on all queries in the golden dataset.
    Supports overlay — adds a new predicted column for each run.

    Returns:
        (results_df, col_name) — the results DataFrame and the current run column name.
    """
    if os.path.exists(results_path):
        routing_eval_df = pd.read_excel(results_path, sheet_name="Routing Evals")
        run_cols = [col for col in routing_eval_df.columns if col.startswith("predicted_run_")]
        run_number = len(run_cols) + 1
    else:
        routing_eval_df = golden_dataset_df[["query", "expected_intent"]].copy()
        run_number = 1

    col_name = f"predicted_run_{run_number}"
    predictions = []
    reasonings = []

    for index, row in golden_dataset_df.iterrows():
        query = row["query"]
        expected_intent = row["expected_intent"]

        predicted_intent, reasoning = get_predicted_intent(query)
        predictions.append(predicted_intent)
        reasonings.append(reasoning)

        status = "Pass" if predicted_intent == expected_intent else "Fail"
        print(f"[{index+1}/{len(golden_dataset_df)}] {status} | Expected: {expected_intent:12} | Predicted: {predicted_intent:12}")

    routing_eval_df[col_name] = predictions
    routing_eval_df[f"reasoning_run_{run_number}"] = reasonings
    routing_eval_df[f"status_run_{run_number}"] = [
        "pass" if p == e else "fail"
        for p, e in zip(predictions, golden_dataset_df["expected_intent"])
    ]

    return routing_eval_df, col_name


# ============================
# 3. Calculate Metrics
# ============================

def calculate_metrics(routing_eval_df: pd.DataFrame, run_col: str) -> pd.DataFrame:
    """
    Calculate Precision, Recall, F1 per category.

    Args:
        routing_eval_df: DataFrame with expected_intent and predicted run columns.
        run_col: which predicted column to evaluate (e.g. "predicted_run_1").
    """
    categories = routing_eval_df["expected_intent"].unique()
    metrics = []

    for category in categories:
        tp = len(routing_eval_df[(routing_eval_df["expected_intent"] == category) & (routing_eval_df[run_col] == category)])
        fp = len(routing_eval_df[(routing_eval_df["expected_intent"] != category) & (routing_eval_df[run_col] == category)])
        fn = len(routing_eval_df[(routing_eval_df["expected_intent"] == category) & (routing_eval_df[run_col] != category)])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = tp + fn

        metrics.append({
            "category": category,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "support": support
        })

    return pd.DataFrame(metrics)


# ============================
# 4. Main
# ============================

def main():
    results_path = "eval/routing_results.xlsx"

    golden_dataset_df = pd.read_csv(GOLDEN_DATASET_PATH)

    # Distribution
    distribution_df = golden_dataset_df["expected_intent"].value_counts().reset_index()
    distribution_df.columns = ["category", "count"]
    distribution_df["percentage"] = (distribution_df["count"] / len(golden_dataset_df) * 100).round(1)

    # Run eval
    routing_eval_df, run_col = run_routing_eval(golden_dataset_df, results_path)

    # Calculate metrics
    metrics_df = calculate_metrics(routing_eval_df, run_col)

    # Print summary
    print(f"\n{'='*60}")
    print("ROUTING EVAL METRICS")
    print(f"{'='*60}")
    print(metrics_df.to_string(index=False))
    print(f"\nDistribution:")
    print(distribution_df.to_string(index=False))

    # Save to Excel
    with pd.ExcelWriter(results_path, engine="openpyxl") as writer:
        routing_eval_df.to_excel(writer, sheet_name="Routing Evals", index=False)
        metrics_df.to_excel(writer, sheet_name="Metrics", index=False)
        distribution_df.to_excel(writer, sheet_name="Distribution", index=False)

    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()