import pandas as pd
import os
from src.guards.guardrails import run_guardrails
from src.prompts.agent_prompts import SUPERVISOR_PROMPT
from config import LLM
from typing import Tuple


def get_predicted_intent(query:str)->str:
    """
        Run guardrails and execute the supervisor agent for each query
    """

    guardrail_check = run_guardrails(query)

    if not guardrail_check["passed"]:
        return "blocked"

    routing_prompt = SUPERVISOR_PROMPT.format(context=query)
    response = LLM.invoke(routing_prompt)

    predicted_intent = response.content.strip().lower().strip("'\"")

    return predicted_intent


def routing_eval(golden_dataset_df: pd.DataFrame, results_path: str) -> Tuple[pd.DataFrame, str]:

    results = []

    if os.path.exists(results_path):
        routing_eval_df = pd.read_csv(results_path)
        run_cols = [col for col in routing_eval_df.columns if col.startswith("predicted_run_")]
        run_number = len(run_cols) + 1
    else:
        routing_eval_df = golden_dataset_df[["query", "expected_intent"]].copy()
        run_number = 1

    col_name = f"predicted_run_{run_number}"
    predictions = []

    for index,row in golden_dataset_df.iterrows():
        query = row["query"]
        expected_intent = row["expected_intent"]

        predicted_intent = get_predicted_intent(query)
        predictions.append(predicted_intent)

        status = "Pass" if predicted_intent == expected_intent else "Fail"
        print("Intent_Mathc:", status)


    routing_eval_df[col_name] = predictions

    return routing_eval_df, col_name