import asyncio
from mcp_agent.core.fastagent import FastAgent
# from mcp_agent.core.prompt import Prompt
from typing import Optional  # Add missing import for type hints

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

# Complexity Determination Agent: Assesses task complexity
@fast.agent(
    name="complexity_agent",
    instruction="""
        You are an expert in assessing the complexity of tasks. Your role is to evaluate the user's request and determine whether it can be completed by a simple agent in a single step or requires a planning agent to generate a detailed list of subtasks.
        Consider the following criteria when making your assessment:
        - Task clarity: Is the request straightforward and unambiguous?
        - Task scope: Does the request involve multiple components or dependencies?
        - Task difficulty: Does the request require specialized knowledge or advanced reasoning?

        Based on your evaluation, classify the task as either:
        - SIMPLE: A single-step task manageable by a simple agent.
        - COMPLEX: A multi-step task requiring a planning agent.

        Provide a brief explanation for your classification.
    """
)

# Simple TOOLRAG Agent: Identifies required tools
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
    """,
    # We would add the actual TOOLRAG MCP server in a real implementation
    # servers=["toolrag_mcp"]
)

# Simple Planning Agent: Creates actionable plans
@fast.agent(
    name="simple_planning_agent",
    instruction="""
        You are an expert in creating actionable plans for fulfilling user requests.
        Your role is to generate a step-by-step experience plan that leverages the provided tools to address the user's request effectively.

        To achieve this, follow these steps:
        1. Analyze the user's request and the provided list of tools, along with their explanations, to understand the requirements and constraints.
        2. Break down the user's request into a sequence of clear, actionable steps that can be executed to fulfill the request.
        3. For each step, specify which tool(s) will be used and how they contribute to completing the task.
        4. Ensure the plan is concise, logically ordered, and directly aligned with the user's request.

        Provide the experience plan in a structured format, including:
        - A numbered list of steps.
        - A brief description of each step.
        - The tool(s) associated with each step and their role in fulfilling the task.

        If any gaps or limitations in the tools are identified, include suggestions for alternative approaches or additional steps to address these gaps.
    """
)

# Complex Planning Agent: Creates detailed multi-step plans
@fast.agent(
    name="complex_planner",  # name of the agent
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
    """,
    # servers=[],  # list of MCP Servers for the agent
    # use_history=True,  # agent maintains chat history
    # human_input=False,  # agent can request human input
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
    """,
    # use_history=True,  # agent maintains chat history
)

@fast.evaluator_optimizer(
    name="planning_evaluator",  # name of the workflow
    generator="complex_planner",  # name of the content generator agent
    evaluator="complex_evaluator",  # name of the evaluator agent
    min_rating='EXCELLENT',  # minimum acceptable quality (EXCELLENT, GOOD, FAIR, POOR)
    max_refinements=3,  # maximum number of refinement iterations
)

async def check_for_experience(agent, user_request: str) -> tuple[bool, Optional[str]]:
    """Check if an experience exists for the request."""
    print("\nExperience Agent ->")
    experience_result = await agent.experience_agent.send(user_request)
    print(experience_result)

    has_experience = "TRUE" in experience_result.upper()
    return has_experience, experience_result

async def determine_complexity(agent, user_request: str) -> tuple[bool, str]:
    """Determine if the task is simple or complex."""
    print("\nComplexity Determination Agent -->")
    complexity_result = await agent.complexity_agent.send(user_request)
    print(complexity_result)

    is_simple = "SIMPLE" in complexity_result.upper()
    return is_simple, complexity_result

async def handle_simple_task(agent, user_request: str):
    """Handle a simple task using the TOOLRAG and Simple Planning agents."""
    print("\n=== SIMPLE")

    # Identify required tools
    print("\nSimple TOOLRAG Agent -->")
    tools_result = await agent.toolrag_agent.send(user_request)
    print(tools_result)

    # Create simple plan
    print("\nSimple Planning Agent -->")
    tools_prompt = f"User Request: {user_request}\n\nAvailable Tools:\n{tools_result}"
    plan_result = await agent.simple_planning_agent.send(tools_prompt)
    print(plan_result)

    return plan_result

async def handle_complex_task(agent, user_request: str, difficulty_level: int = 1):
    """Handle a complex task with planning and evaluation, with optional iterations."""
    print("\n=== COMPLEX (Loop x Task difficulty level)")

    previous_plan = None
    previous_evaluation = None

    for iteration in range(difficulty_level):
        print(f"\nIteration {iteration+1}/{difficulty_level}")

        # Create complex plan
        print("\nComplex Planning Agent -->")
        plan_prompt = user_request
        if previous_plan and previous_evaluation:
            plan_prompt = f"User Request: {user_request}\n\nPrevious Plan:\n{previous_plan}\n\nFeedback:\n{previous_evaluation}"

        plan_result = await agent.planning_evaluator.send(plan_prompt)
        print(plan_result)
        return plan_result
        # previous_plan = plan_result

        # # Evaluate the plan
        # print("\nEvaluation Agent -->")
        # eval_prompt = f"User Request: {user_request}\n\nPlanned Solution:\n{plan_result}"
        # eval_result = await agent.evaluation_agent.send(eval_prompt)
        # print(eval_result)
        # previous_evaluation = eval_result

        # # If we get an EXCELLENT rating, we can break early
        # if "EXCELLENT" in eval_result.upper():
        #     print("Plan achieved EXCELLENT rating, breaking early.")
        #     break

    # return previous_plan, previous_evaluation

async def process_request(user_request: str):
    """Process a user request through the full workflow."""

    async with fast.run() as agent:
        print("\nUser Request >", user_request)

        # Step 1: Check if an experience exists
        has_experience, experience_detail = await check_for_experience(agent, user_request)

        if has_experience:
            print("\n=== TRUE")
            print("\nExperience -->")
            # In a real implementation, this would fetch and return the existing experience
            # For now, we'll just return a placeholder
            return "Using existing experience for this request."
        else:
            print("\n=== FALSE")

            # Step 2: Determine complexity
            is_simple, complexity_detail = await determine_complexity(agent, user_request)

            is_simple = False
            # Extract difficulty level for complex tasks (default to 1)
            difficulty_level = 1
            if not is_simple:
                # Try to extract a difficulty level from the complexity assessment
                try:
                    # This is a simple heuristic - in a real system you might want a more structured output
                    if "high complexity" in complexity_detail.lower():
                        difficulty_level = 3
                    elif "moderate complexity" in complexity_detail.lower():
                        difficulty_level = 2
                except:
                    pass

            # Step 3: Process based on complexity
            if is_simple:
                return await handle_simple_task(agent, user_request)
            else:
                # final_plan, final_evaluation = await handle_complex_task(agent, user_request, difficulty_level)
                final_plan = await handle_complex_task(agent, user_request, difficulty_level)
                return final_plan

async def main():
    """Main entry point for the application."""
    print("Complex Planner System")
    print("---------------------")
    user_request = "Take me home."
    # user_request = "Read me the latest news stories in the style of gossip girl."
    # user_request = input("Enter your request: ")

    await process_request(user_request)
    # result = await process_request(user_request)

    # print("\nFinal Result:")
    # print(result)

if __name__ == "__main__":
    asyncio.run(main())
