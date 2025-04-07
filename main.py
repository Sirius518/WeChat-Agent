from openai import OpenAI
from pcagent import PCAgent
from planning import PlanningAgent
from grounding import GroundingAgent


alibab_key = 'sk-75d3339aff9d45e8be99e2bdcfd973ef'
volc_key = '6a9ad134-6df0-4023-b958-ce8d68307b51'


grounding_client = OpenAI(
    api_key=volc_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
)

planning_client = OpenAI(
    api_key=alibab_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def exec_task(output_queue=None):
    agent = PCAgent(PlanningAgent(planning_client), GroundingAgent(grounding_client), output_queue)
    agent.run()

if __name__ == "__main__":
    exec_task()
