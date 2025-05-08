import asyncio
from mcp_agent.core.fastagent import FastAgent

# query = input("Enter your query: ")

# planner = planning_agent(query) #returns a list of tasks

# #for each task:
# for task in planner:
#     tools = retrieve_from_vdb(task)
#     description = generate_description(task)

# @fast.agent(instruction=description, servers=tools)

# Create the application
fast = FastAgent("fast-agent example")


@fast.agent(
    instruction="You are a helpful AI assistant.",
    servers=["playwright"],
)

# @fast.agent(
# @fast.agent(
#     instruction="You are an AI assistant that can use the sear library to interact with web pages and make searches. ",
#     servers=["searxng"],
# )

# @fast.agent(instruction='''
# You are an AI planning agent, you create the plan to execute the user's request by
# breaking the request into subtasks and creating agents with the appropriate tools to
# complete each subtask.
# ''', servers=["tool-rag"])

# Define the agent
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        # await agent("""
        # Get me the top 3 latest news stories from the New York Times news website and rewrite them in the style of gossip girl.
        # """)
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
