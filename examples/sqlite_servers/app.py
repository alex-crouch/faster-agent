#!/usr/bin/env python3
"""
Example FastAgent application that loads MCP server configurations from a SQLite database.
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncio
from mcp_agent.core.fastagent import FastAgent


# # Define the agent
# @fast.agent(instruction="You are a helpful AI Agent", servers=["tectonic"])
# async def main():
#     # use the --model command line switch or agent arguments to change model
#     async with fast.run() as agent:
#         await agent.interactive()


# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Create the FastAgent application with the config file that references the database
fast = FastAgent("DB Server Example", config_path="./fastagent.config.yaml")


@fast.agent(instruction="You are a helpful AI Agent", servers=["fetch", "everything"])
async def app():
    """Main application agent."""
    return "I'm connected to MCP servers configured in a SQLite database!"


async def main():
    """Run the FastAgent application."""
    print("Starting FastAgent with SQLite database server configurations...")

    # Check if database file exists
    if not os.path.exists("mcp_servers.db"):
        print("Database file not found. Please run init_db.py first.")

    # Run with the FastAgent context
    # async with fast.run() as agent:
    #     print("\nRegistered MCP servers:")

    #     # Get all server configurations from the registry
    #     for server_name, server_config in fast.app.server_registry.registry.items():
    #         source = "Database" if server_name in ["filesystem", "fetch", "remote-fs"] else "YAML"
    #         print(f"- {server_name} ({source}): {server_config.description}")

    #         # Display roots if available
    #         if server_config.roots:
    #             print(f"  Roots:")
    #             for root in server_config.roots:
    #                 print(f"    - {root.name}: {root.uri}")

    # Send a message to the agent
    print("\nSending message to agent...")
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
