import asyncio
from mcp_agent.core.fastagent import FastAgent
from typing import Optional

# Create the FastAgent application
fast = FastAgent("Complex Request Planner")

# Experience Agent: Determines if an experience exists
@fast.agent(
    name="experience_agent",
    instruction="""
        You are an expert in determining whether an experience exists to fulfill the user's request. Your role is to evaluate the request and decide if there is an existing experience (a predefined set of steps and requirements) that can satisfy it.

        To make this determination, you will use the experience RAG tool to search through the currently available experiences. Based on your findings, return one of the following:

        - TRUE: If an experience exists that can fulfill the user's request.
        - FALSE: If no such experience exists.

        Provide a brief explanation for your decision, referencing the results of your search.
    """
)

# Complexity Agent: Only kept for providing difficulty assessment
@fast.agent(
    name="complexity_agent",
    instruction="""
        You are an expert in assessing the complexity of tasks. Your role is to evaluate the user's request and determine its difficulty level.

        Consider the following criteria when making your assessment:
        - Task clarity: Is the request straightforward and unambiguous?
        - Task scope: Does the request involve multiple components or dependencies?
        - Task difficulty: Does the request require specialized knowledge or advanced reasoning?

        Rate the task on a scale of 1-3:
        - 1: Moderate complexity (fewer steps, straightforward dependencies)
        - 2: Substantial complexity (multiple steps, several dependencies)
        - 3: High complexity (many steps, complex dependencies, specialized knowledge)

        Always classify the task as COMPLEX, but provide a numerical difficulty rating (1-3) in your explanation.
    """,
    use_history=True,
)

# TOOLRAG Agent: Identifies required tools
@fast.agent(
    name="toolrag_agent",
    instruction="""
        You are an expert in identifying the tools required to fulfill the user's request. Your role is to evaluate the request and determine the necessary tools by querying the TOOLRAG MCP server.

        To achieve this, follow these steps:
        1. Analyze the user's request to understand the requirements.
        2. Use the TOOLRAG MCP server to search for tools that match the requirements.
        3. Identify and list the tools that are essential to completing the task.

        Provide a detailed explanation of your findings, including:
        - The tools identified.
        - How each tool contributes to fulfilling the request.
        - Any gaps or limitations in the available tools.

        If no tools are found, explain why and suggest alternative approaches if possible.
    """
    # We would add the actual TOOLRAG MCP server in a real implementation
    # servers=["toolrag_mcp"]
)

# Complex Planning Agent: Creates detailed multi-step plans
@fast.agent(
    name="complex_planner",
    instruction="""
        You are an expert in writing instructions for an LLM agent and generating a structured plan.
        You understand how many steps are required to complete the task and you create the detailed plan that will enable the fulfilment of the user's request.

        To achieve this, follow these steps:
        1. Break the user's request into subtasks.
        2. Identify whether the subtask has any fallback options that would give the result that the subtask is trying to achieve.
        3. For each subtask list out all the necessary steps in granular detail.
        4. Group or divide these steps into kernels that correspond to individual agents. These kernels require, an instruction, a level
        of difficulty, and a dependency tree that lists only the kernel that it is dependent on.

        You are only responsible for planning.
    """
)

@fast.agent(
    name="complex_evaluator",
    instruction="""
        Evaluate the response from the planning agent based on the criteria, ensure strictly that all criteria are met:
        - Plan Congruency. Has the planning agent correctly divided the plan into subtasks and kernels?
        - Fallback. Has the planning agent correctly identified fallback options for each subtask?
        - Dependencies. Has the planning agent correctly identified the dependencies between the kernels?
        - Alignment. Has the planning agent acted and addressed feedback from any previous assessments?

        For each criterion:
        - Provide a rating (EXCELLENT (3), GOOD (2), FAIR (1), or POOR (0)).
        - Offer specific feedback or suggestions for improvement.

        Summarize your evaluation as a structured response with:
        - Overall quality rating.
        - Specific feedback and areas for improvement.
    """
)

@fast.evaluator_optimizer(
    name="planning_evaluator",
    generator="complex_planner",
    evaluator="complex_evaluator",
    min_rating='GOOD',
    max_refinements=3,
)

@fast.chain(
  "era",
   sequence=["complexity_agent","planning_evaluator"],
   cumulative=True,
)

# # we can them prompt it directly:
# async with fast.run() as agent:
#   await agent.interactive(agent="post_writer")

async def check_for_experience(agent, user_request: str) -> tuple[bool, Optional[str]]:
    """Check if an experience exists for the request."""
    print("\nExperience Agent ->")
    experience_result = await agent.experience_agent.send(user_request)
    print(experience_result)

    has_experience = "TRUE" in experience_result.upper()
    return has_experience, experience_result

async def determine_difficulty(agent, user_request: str) -> int:
    """Determine the difficulty level of the task."""
    print("\nComplexity Assessment Agent -->")
    complexity_result = await agent.complexity_agent.send(user_request)
    print(complexity_result)

    # Extract difficulty level (default to 1)
    difficulty_level = 1
    try:
        # Simple heuristic - in a real system you might want a more structured output
        if "3" in complexity_result or "high complexity" in complexity_result.lower():
            difficulty_level = 3
        elif "2" in complexity_result or "substantial complexity" in complexity_result.lower():
            difficulty_level = 2
    except:
        pass

    return difficulty_level

async def handle_complex_task(agent, user_request: str, difficulty_level: int = 1):
    """Handle a complex task with planning and evaluation."""
    print(f"\n=== COMPLEX (Difficulty level: {difficulty_level})")

    # Create complex plan with evaluation
    print("\nComplex Planning Agent with Evaluation -->")
    plan_result = await agent.planning_evaluator.send(user_request)
    print(plan_result)

    return plan_result

async def process_request(user_request: str):
    """Process a user request through the full workflow."""

    async with fast.run() as agent:
        print("\nUser Request >", user_request)

        # Step 1: Check if an experience exists
        # has_experience, experience_detail = await check_for_experience(agent, user_request)

        # if has_experience:
        #     print("\n=== TRUE")
        #     print("\nExperience -->")
        #     # In a real implementation, this would fetch and return the existing experience
        #     return "Using existing experience for this request."
        # else:
            #
        print("\n=== FALSE")

        # Step 2: Determine difficulty level
        # difficulty_level = await determine_difficulty(agent, user_request)

        # Step 3: Process as complex task
        final_plan = await handle_complex_task(agent, user_request)
        return final_plan

async def main():
    """Main entry point for the application."""
    print("Complex Planner System")
    print("---------------------")
    # user_request = "Take me home."
    user_request = "Read me the latest news stories in the style of gossip girl."
    # user_request = input("Enter your request: ")

    await process_request(user_request)

if __name__ == "__main__":
    asyncio.run(main())
