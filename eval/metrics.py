import pandas as pd

def calculate_metrics(routing_eval_df:pd.DataFrame, run_col: str = None) -> pd.DataFrame:
    """
    Load results CSV and calculate precison, Recall and F1 score per category

    Args:
        routing_eval_df: routing agent evaluation dataframe
        run_col: which predicted column to evaluate (e.g. "predicted_run_1")

                If None, use the latest run column.
    """
    metrics = []
    if run_col is None:
        run_cols = [col for col in routing_eval_df.columns if col.startswith("predicted_run_")]
        run_col = run_cols[-1]

    categories = routing_eval_df["expected_intent"].unique()

    for category in categories:
        # expected is this category and predicted is this category
        true_positive = len(routing_eval_df[(routing_eval_df["expected_intent"] == category) & (routing_eval_df[run_col] == category)])

        # expected is not this category and predicted is this category
        false_positive = len(routing_eval_df[(routing_eval_df["expected_intent"] != category) & (routing_eval_df[run_col] == category)])

        # expected is this category and predicted is not this category
        false_negative = len(routing_eval_df[(routing_eval_df["expected_intent"] == category) & (routing_eval_df[run_col] != category)])

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0

        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0

        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        support = true_positive + false_negative

        metrics.append({
            "category": category,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "support": support
        })

    metrics_df = pd.DataFrame(metrics)

    return metrics_df 