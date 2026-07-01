from langsmith import Client
import pandas as pd
from langsmith.evaluation import evaluate, EvaluationResult, EvaluationResults
from langchain_core.messages import HumanMessage
from src.agents.agents import job_search_agent, ai_news_agent, finance_agent

def upload_dataset(dataset_path: str, dataset_name: str) -> str:
    """
        Upload the dataset to LangSmith

        Args:
            dataset_path: path of the golden dataset of agent.
            dataset_name: name for dataset
    """
    client = Client()

    if client.has_dataset(dataset_name = dataset_name):
        client.delete_dataset(dataset_name = dataset_name)

    dataset = client.create_dataset(dataset_name = dataset_name)
    df = pd.read_csv(dataset_path)

    for _,row in df.iterrows():
        client.create_example(
            inputs = {"query":row['query']},
            outputs = {
                "expected_tool": row['expected_tool'],
                "expected_contains": row['expected_contains']
            },
            dataset_id = dataset.id
        )

    print(f"Uploaded {len(df)} examples to: {dataset_name}")

    return dataset_name

def make_target_function(agent):
    """
        create a target function for a given agent.
    """

    def predict(inputs: dict) -> dict:
        query = inputs['query']
        result = agent.invoke({"messages": [HumanMessage(content = query)]})

        # Extract tools called
        tools_called = [
            msg.name for msg in result['messages']
            if hasattr(msg, "name") and msg.name
        ]

        # get the reasoning
        reasoning = ""

        for msg in result["messages"]:
            if msg.type == "ai" and msg.content and hasattr(msg, 'content'):
                reasoning = msg.content[:200]
                break

        # Final response
        final_response = result["messages"][-1].content

        return {
            "tools_called": tools_called,
            "response": final_response,
            "reasoning": reasoning
        }
    
    return predict


def tool_selection_evaluator(run, example) -> EvaluationResult:
    """
        check if the expected tool was called.
    """
    expected_tool = example.outputs['expected_tool']
    tools_called = run.outputs.get("tools_called", "")

    score = 1.0 if expected_tool in tools_called else 0.0

    return EvaluationResult(key="tool_selection", score=score)


def response_content_evaluator(run, example) -> EvaluationResult:
    """
        Check if the response contains expected keywords.
    """
    expected_contains = example.outputs["expected_contains"]
    response = run.outputs.get("response", "").lower()

    keywords = [k.strip().lower() for k in expected_contains.split("|")]
    matched = sum(1 for k in keywords if k in response)
    score = matched / len(keywords) if keywords else 0

    return EvaluationResult(key = "response_completeness", score = round(score, 3))


def tool_summary_metrics(runs, examples) -> EvaluationResults:
    """
        Calculate precision, recall, f1 per tool after all examples complete.
    """
    results = []

    predictions = []
    for run, example in zip(runs, examples):
        expected = example.outputs['expected_tool']
        called = run.outputs.get('tools_called',"")
        predictions.append((expected, called))
    
    tools = list(set(e for e,_ in predictions))

    all_tp, all_fp, all_fn = 0, 0, 0

    for tool in tools:

        tp = sum(1 for e, c in predictions if e == tool and tool in c)
        fp = sum(1 for e, c in predictions if e != tool and tool in c)
        fn = sum(1 for e, c in predictions if e == tool and tool not in c)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results.append(EvaluationResult(key=f"precision_{tool}", score=round(precision, 3)))
        results.append(EvaluationResult(key=f"recall_{tool}", score=round(recall, 3)))
        results.append(EvaluationResult(key=f"f1_{tool}", score=round(f1, 3)))

        all_tp += tp
        all_fp += fp
        all_fn += fn

    # Overall
    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    results.append(EvaluationResult(key="precision_overall", score=round(overall_precision, 3)))
    results.append(EvaluationResult(key="recall_overall", score=round(overall_recall, 3)))
    results.append(EvaluationResult(key="f1_overall", score=round(overall_f1, 3)))

    return EvaluationResults(results=results)


def run_agent_eval():
    """
        evaluate the ReAct agents.
    """
    agents_config = [
        {   
            "agent": job_search_agent,
            "dataset": "data/golden_dataset_job_search.csv",
            "name": "Job Search Agent",
            "prefix": "job-search-eval"
        },
        {
            "agent": ai_news_agent,
            "dataset": "data/golden_dataset_ai_news.csv",
            "name": "AI News Agent",
            "prefix": "ai-news-eval"
        },
        {
            "agent": finance_agent,
            "dataset": "data/golden_dataset_finance.csv",
            "name": "Finance Agent",
            "prefix": "finance-eval"
        }
    ]

    for config in agents_config:
        print(f"\n{'='*60}")
        print(f"Running: {config['name']}")
        print(f"{'='*60}")

        dataset_name = upload_dataset(config['dataset'], config['name'])
        target_fn = make_target_function(config['agent'])

        evaluate(
            target_fn,
            data = dataset_name,
            evaluators = [tool_selection_evaluator, response_content_evaluator],
            summary_evaluators = [tool_summary_metrics],
            experiment_prefix = config['prefix']
        )



if __name__ == "__main__":
    run_agent_eval()