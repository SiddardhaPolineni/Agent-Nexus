from eval.routing_eval import routing_eval
from eval.metrics import calculate_metrics
import os
import pandas as pd


def main():

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    GOLDEN_DATASET_PATH = os.path.join(DATA_DIR,"golden_dataset_routing.csv")

    results_path = "eval/routing_results.xlsx"

    golden_dataset_df = pd.read_csv(GOLDEN_DATASET_PATH)

    distribution_df = golden_dataset_df["expected_intent"].value_counts().reset_index()
    distribution_df.columns = ["category", "count"]
    distribution_df["percentage"] = (distribution_df["count"] / len(golden_dataset_df) * 100).round(1)

    routing_eval_df, run_col = routing_eval(golden_dataset_df, results_path)
    metrics_df = calculate_metrics(routing_eval_df, run_col)

    with pd.ExcelWriter("eval/routing_results.xlsx", engine = "openpyxl") as writer:
        routing_eval_df.to_excel(writer, sheet_name = "Routing Evals", index = False)
        metrics_df.to_excel(writer, sheet_name = "Metrics", index = False)
        distribution_df.to_excel(writer, sheet_name = "Distribution", index = False)


if __name__ == "__main__":
    main()