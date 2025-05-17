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

@fast.agent(instruction="You are a helpful ai agent", servers=["fetch","everything"])

# Define the agenta
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
