import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("Planner")

@fast.agent(
    name="planner",  # name of the agent
    instruction="""
    You are an AI planning agent, you create the top level plan that will enable the fulfilment of the user's request.
    To achieve this, break the user's request into subtasks and list all the necessary steps in granular detail. Then,
    divide the subtasks into kernels corresponding to individual agents. These kernels require, an instruction, a level
    of difficulty, a list of tools, and a dependency tree.
  """,
    servers=[],  # list of MCP Servers for the agent
    use_history=False,  # agent maintains chat history
    human_input=False,  # agent can request human input
)
@fast.agent(
    name="evaluator",
    instruction="""
Evaluate the response from the planning agent based on the criteria:
 - Plan Congruency. Has the planning agent correctly divided the top level plan into kernels?
 - Dependencies. Has the planning agent correctly identified the dependencies between the kernels?
 - Alignment. Has the planning agent acted and addressed feedback from any previous assessments?

For each criterion:
- Provide a rating (EXCELLENT, GOOD, FAIR, or POOR).
- Offer specific feedback or suggestions for improvement.

Summarize your evaluation as a structured response with:
- Overall quality rating.
- Specific feedback and areas for improvement.""",
)
@fast.evaluator_optimizer(
    name="planning_evaluator",  # name of the workflow
    generator="planner",  # name of the content generator agent
    evaluator="evaluator",  # name of the evaluator agent
    min_rating="GOOD",  # minimum acceptable quality (EXCELLENT, GOOD, FAIR, POOR)
    max_refinements=3,  # maximum number of refinement iterations
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.planning_evaluator.send("""
        Get me the top 3 latest news stories from the New York Times news website and rewrite them in the style of gossip girl.
        """)
        # await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
