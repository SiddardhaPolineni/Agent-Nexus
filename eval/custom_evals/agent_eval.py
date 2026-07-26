import pandas as pd
from src.agents.agents import job_search_agent, ai_news_agent, finance_agent
import os
from langchain_core.messages import HumanMessage


def calculate_agent_metrics(results_df: pd.DataFrame, agent_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
        calculate precision, recall, f1 for tool selection + distribution.

        Args:
            results_df: Dataframe with 'expected_tool' and 'tools_called' column
            agent_name: for display

        returns:
            (metrics_df, distribution_df)
    """

    # get unique expected tools
    categories = results_df['expected_tool'].unique()

    metrics_rows = []

    for tool in categories:
        
        # expected this tool AND it was called
        tp = len(results_df[
            (results_df['expected_tool'] == tool) &
            (results_df['tools_called'].str.contains(tool, na=False))
        ])

        # expected a different tool but this tool was called
        fp = len(results_df[
            (results_df['expected_tool'] != tool) &
            (results_df['tools_called'].str.contains(tool, na=False))
        ])

        # expected this tool but it was not called.
        fn = len(results_df[
            (results_df['expected_tool'] == tool) &
            (~results_df['tools_called'].str.contains(tool, na=False))
        ])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = tp + fn

        metrics_rows.append({
            "tool": tool,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "support": support
        })

    metrics_df = pd.DataFrame(metrics_rows)

    # distribution
    distribution_df = results_df['expected_tool'].value_counts().reset_index()
    distribution_df.columns = ['tool', 'count']
    distribution_df['percentage'] = (distribution_df['count'] / len(results_df) * 100).round(1)

    return metrics_df, distribution_df

def run_agent(agent, query:str) -> dict:
    """
        Invoke a react agent and return the tool called

        returns:
            {
                "tools_called": ["search_jobs],..
                "response": "1. Software Engineer at Google..."
            }
    """

    result = agent.invoke({"messages": [HumanMessage(content = query)]})

    # Extract tools called from messaged
    tools_called = [
        msg.name for msg in result["messages"]
        if hasattr(msg, "name") and msg.name
    ]

    # capture agents reasoning
    reasoning = ""
    for msg in result['messages']:
        if hasattr(msg, 'content') and msg.type == "ai" and msg.content:
            reasoning = msg.content[:200]
            break

    # final response
    final_response = result['messages'][-1].content

    return {
        "tools_called": tools_called,
        "response": final_response,
        "reasoning": reasoning
    }

def check_tool_selection(expected_tool: str, tools_called: list) -> bool:
    """
        check if the expected tool was called by the agent
    """
    return expected_tool in tools_called


def check_response_content(expected_contains: str, response: str) -> dict:
    """
        Check if the response contains expected keywords.
        expected _contains is pipe-sepearted: "compay|location|link"

        return:
            {
                "passed": True/False, "matched": [...], "missing": [...]
            }
    """

    keywords = [k.strip() for k in expected_contains.split("|")]

    response_lower = response.lower()

    matched = [k for k in keywords if k.lower() in response_lower]
    missing = [k for k in keywords if k.lower() not in response_lower]

    return {
        "passed": len(missing) == 0,
        "matched": matched,
        "missing": missing
    }


def evaluate_agent(agent_name:str, dataset_path:str, agent) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
        Run the evaluation for a single agent

        Args:
            agent_name: name for display/output.
            dataset_path: path to the golden dataset.
            agent: the react agent to evaluate.
    """

    df = pd.read_csv(dataset_path)

    results = []

    for index, row in df.iterrows():
        query = row['query']
        expected_tool = row['expected_tool']
        expected_contains = row['expected_contains']

        try:

            agent_response = run_agent(agent,query)

            # check tool selection
            tool_correct = check_tool_selection(expected_tool, agent_response['tools_called'])

            # check response content
            content_check = check_response_content(expected_contains, agent_response['response'])

            results.append({
                "query": query,
                "expected_tool": expected_tool,
                "tools_called": ", ".join(agent_response['tools_called']),
                "tool_correct": tool_correct,
                "content_passed": content_check['passed'],
                "missing_keywords": ", ".join(content_check['missing']),
                "reasoning": agent_response["reasoning"],
                "status": "pass" if tool_correct and content_check["passed"] else "fail",
                "error": ""
            })

            status = "pass" if tool_correct and content_check['passed'] else "Fail"
        
        except Exception as e:
            results.append({
                "query": query,
                "expected_tool": expected_tool,
                "tools_called": "",
                "tool_correct": False,
                "content_passed": False,
                "missing_keywords": "",
                "reasoning": "",
                "status": "fail",
                "error": str(e)
            })

            status = "Error"
    
    results_df = pd.DataFrame(results)
    metrics_df, distribution_df = calculate_agent_metrics(results_df, agent_name)

    print(f"\n--- {agent_name} Tool Selection Metrics ---")
    print(metrics_df.to_string(index=False))
    print(f"\n--- Distribution ---")
    print(distribution_df.to_string(index=False))

    tool_accuracy = results_df['tool_correct'].mean() * 100
    content_accuracy = results_df['content_passed'].mean() * 100
    
    print(f"\n--- {agent_name} Results ---")
    print(f"Tool Selection Accuracy: {tool_accuracy:.1f}%")
    print(f"Content Completeness:    {content_accuracy:.1f}%")
    
    return results_df, metrics_df, distribution_df

def main():

    agents_config = [
        {
            "agent": job_search_agent,
            "name": "Job Search Agent",
            "dataset": "data/golden_dataset_job_search.csv",

        },
        {
            "agent": ai_news_agent,
            "name": "AI News Agent",
            "dataset": "data/golden_dataset_ai_news.csv"
        },
        {
            "agent": finance_agent,
            "name": "Finance Agent",
            "dataset": "data/golden_dataset_finance.csv"
        }
    ]

    all_results = {}

    for config in agents_config:
        print(f"\n{'='*60}")
        print(f"Evaluating: {config['name']}")
        print(f"{'='*60}")

        results_df, metrics_df, distribution_df = evaluate_agent(config['name'], config['dataset'], config['agent'])

        # Save to Excel with multiple sheets
        output_path = f"eval/{config['name'].lower().replace(' ', '_')}_results.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            results_df.to_excel(writer, sheet_name="Results", index=False)
            metrics_df.to_excel(writer, sheet_name="Metrics", index=False)
            distribution_df.to_excel(writer, sheet_name="Distribution", index=False)



if __name__ == "__main__":
    main()