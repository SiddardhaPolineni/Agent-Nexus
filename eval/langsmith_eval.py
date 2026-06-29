import pandas as pd
from langsmith import Client
from langsmith.evaluation import evaluate, EvaluationResult, EvaluationResults
from config import GOLDEN_DATASET_PATH
from src.guards.guardrails import run_guardrails
from src.prompts.agent_prompts import SUPERVISOR_PROMPT
from config import LLM
import logging

logger = logging.getLogger(__name__)

def upload_dataset() -> str:
    """
        Upload golden dataset to LangSmith
    """
    client = Client()
    dataset_name = "Agent Nexus - Routing Eval"

    # delete the dataset if it is already exists
    if client.has_dataset(dataset_name = dataset_name):
        client.delete_dataset(dataset_name = dataset_name)

    dataset = client.create_dataset(dataset_name = dataset_name)

    df = pd.read_csv(GOLDEN_DATASET_PATH)

    for _,row in df.iterrows():
        client.create_example(
            inputs = {"query": row["query"]},
            outputs = {"expected_intent": row["expected_intent"]},
            dataset_id = dataset.id
        )
    
    return dataset_name


def predict_intent(inputs: dict) -> dict:
    """
        Target function for LangSmith evaluation.
    """
    query = inputs["query"]

    guardrail_check = run_guardrails(query)

    if not guardrail_check["passed"]:
        return {"predicted_intent": "blocked"}
    
    routing_prompt = SUPERVISOR_PROMPT.format(context = query)
    response = LLM.invoke(routing_prompt)

    predicted = response.content.strip().lower().strip("'\"")

    return {"predicted_intent": predicted}


def routing_accuracy(run, example) -> EvaluationResult:
    """
        Check if predicted intent matches with expected intent.
    """
    predicted = run.outputs["predicted_intent"]
    expected = example.outputs["expected_intent"]

    return EvaluationResult(
        key= "routing_accuracy",
        score = 1.0 if predicted == expected else 0.0
    )

def summary_metrics(runs, examples) -> EvaluationResults:
    """
        Summary evaluator: calculates precision, recall, F1 per category
        after all examples have been evaluated
    """
    categories = ["job_search", "ai_news", "finance", "general", "blocked"]
    results = []

    # Collect all predicted/expected pairs
    predictions = []

    for run, example in zip(runs, examples):
        predicted = run.outputs["predicted_intent"]
        expected = example.outputs["expected_intent"]
        predictions.append((expected, predicted))

    all_tp, all_fp, all_fn = 0, 0, 0

    for category in categories:
        tp = sum(1 for e, p in predictions if e == category and p == category)
        fp = sum(1 for e, p in predictions if e != category and p == category)
        fn = sum(1 for e,p in predictions if e == category and p != category)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results.append(EvaluationResult(key=f"precision_{category}", score=round(precision, 3)))
        results.append(EvaluationResult(key=f"recall_{category}", score=round(recall, 3)))
        results.append(EvaluationResult(key=f"f1_{category}", score=round(f1, 3)))

        all_tp += tp
        all_fp += fp
        all_fn += fn

    # Overall (micro-average)
    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    results.append(EvaluationResult(key="precision_overall", score=round(overall_precision, 3)))
    results.append(EvaluationResult(key="recall_overall", score=round(overall_recall, 3)))
    results.append(EvaluationResult(key="f1_overall", score=round(overall_f1, 3)))

    return EvaluationResults(results = results)


def run_eval():
    """
        Run the evaluation experiment
    """

    dataset_name = upload_dataset()

    results = evaluate(
        predict_intent,
        data = dataset_name,
        evaluators = [routing_accuracy],
        summary_evaluators = [summary_metrics],
        experiment_prefix = "routing-eval"
    )

    logger.info("Evaluation complete! Check LangSmith for results")

    return results

if __name__ == "__main__":
    run_eval()

