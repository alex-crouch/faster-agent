import asyncio
import json

from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.prompt import Prompt

from pydantic import BaseModel, Json
from typing import Any, List

agents = FastAgent(name="cities")

# Define your expected response structure

class SubTaskInfo(BaseModel):
    subTaskName: str
    goal: str
    inputs: List[str]
    outputs: List[str]
    exampleOutputs: Json[Any]
    challenges: List[str]

class PlanInfo(BaseModel):
    planName: str
    coreObjective: str
    assumptions: List[str]
    subtask: List[SubTaskInfo]

@agents.agent(
    name="planner",
    instruction="""
# Role: Expert Task Planner

You are an expert autonomous task planner. Your primary focus is to analyze a user request and break it down into a comprehensive, structured plan with clear subtasks.

## Task Analysis Principles:
1. Carefully analyze the user's request, what is the extent of their desired outputs
2. Carefully identify aspects of the request that are vague or ambiguous, state the assumptions that you have made, and take note where clarification is needed
3. Identify the core objective and restate if needed
4. Give the workflow a camelCase name

## Subtask Identification
1. Identify all necessary subtasks required to fulfill the request

## Subtask Decomposition
For each subtask and fallback subtask identified:
1. Give a camelCase name that represents the sub task
2. Describe the specific goal of the subtask in detail
3. Name and describe each required input in detail
4. Name and describe each desired output in detail
5. Give an in depth example of the output that this subtask would produce
6. Identify the potential challenges that may occur during execution


## Best Practices
- For ambiguous requests, make reasonable assumptions about the user's intent
- Consider resource constraints and permissions that might be required
- Think about edge cases and include contingency plans
- Consider both technical and non-technical aspects of completing the request
- When generating example outputs give as much information as possible
"""
    )

async def main() -> None:
    async with agents.run() as agent:

        user_prompt = """
Get me the top 3 latest news stories from the Australian ABC and rewrite them in the style of gossip girl.
    	"""

        # await agent.planner.send(user_prompt)

        result, message = await agent.planner.structured(
            [Prompt.user(user_prompt)],
            PlanInfo
        )

        # print("=== Printing the full result object ===")
        # print(message)

        # print("\n=== Accessing specific properties ===")
        # print(f"Plan Name: {result.planName}")
        # print(f"Core Objective: {result.coreObjective}")
        # print(f"Assumptions: {', '.join(result.assumptions)}")

        # print("\n=== Accessing subtasks ===")
        # for i, subtask in enumerate(result.subtask, 1):
        #     print(f"\nSubtask {i}: {subtask.subTaskName}")
        #     print(f"  Goal: {subtask.goal}")
        #     print(f"  Inputs: {', '.join(subtask.inputs)}")
        #     print(f"  Outputs: {', '.join(subtask.outputs)}")
        #     print(f"  Example Output: {subtask.exampleOutput}")
        #     print(f"  Challenges: {', '.join(subtask.challenges)}")

        print("\n=== Converting to dictionary ===")
        # Convert to dictionary representation
        result_dict = result.model_dump()
        print(json.dumps(result_dict, indent=2))

        # print("\n=== Converting to JSON string ===")
        # # Convert to JSON string
        # result_json = result.model_dump_json(indent=2)
        # print(result_json)

if __name__ == "__main__":
    asyncio.run(main())
