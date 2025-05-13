#!/usr/bin/env python3

import os
import json
import argparse
import logging
from typing import Dict, List, Any

# Import the ToolRAG class from rag_search.py
from rag_search import ToolRAG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KernelServerAssigner:
    """A class that assigns appropriate tools to kernels based on their descriptions."""

    def __init__(self, openai_api_key: str, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize the KernelToolAssigner with necessary configurations.

        Args:
            openai_api_key: API key for OpenAI services
            qdrant_host: Hostname for Qdrant server
            qdrant_port: Port for Qdrant server
        """
        self.openai_api_key = openai_api_key
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        # Initialize the ToolRAG for tool discovery
        self.tool_rag = ToolRAG(
            openai_api_key=self.openai_api_key,
            qdrant_host=self.qdrant_host,
            qdrant_port=self.qdrant_port
        )

    def find_servers_for_kernel(self, kernel: Dict[str, Any], max_servers: int = 3) -> List[Dict[str, Any]]:
        """Find appropriate tools for a given kernel based on its description.

        Args:
            kernel: The kernel dictionary from the kernel structure
            max_servers: Maximum number of tools to assign to a kernel

        Returns:
            List of server dictionaries with name, description and relevance score
        """
        # Construct a search query based on the kernel's description and agent type
        search_query = f"{kernel['agent_type']}: {kernel['description']}"
        logger.info(f"Searching servers for kernel '{kernel['name']}' with query: '{search_query}'")

        # Use ToolRAG to retrieve relevant tools
        search_results = self.tool_rag.retrieve(search_query)

        # Extract and format tool information
        servers = []
        for result in search_results[:max_servers]:  # Limit to max_tools
            payload = result.payload
            servers_name = payload.get(self.tool_rag.payload_name_field, f"Server {result.id}")
            servers_desc = payload.get(self.tool_rag.payload_text_field, "No description available")

            servers.append({
                "name": servers_name,
                "description": servers_desc,
                "relevance_score": result.score
            })

        return servers

    def assign_servers_to_kernels(self, kernel_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Assign tools to each kernel in the kernel structure.

        Args:
            kernel_structure: The JSON kernel structure from KernelStructurer

        Returns:
            Updated kernel structure with tool assignments
        """
        # Create a new structure to avoid modifying the original
        enhanced_structure = kernel_structure.copy()

        # Process each kernel
        for i, kernel in enumerate(enhanced_structure.get("kernels", [])):
            # Check if tools are required for this kernel
            tools_required = kernel.get("tools_required", "False")

            if tools_required.lower() == "true":
                # Find tools for this kernel
                servers = self.find_servers_for_kernel(kernel)

                # Add tools to the kernel
                kernel["assigned_tools"] = servers

                # Extract server names for FastAgent configuration
                server_names = [server["name"] for server in servers]
                kernel["servers"] = server_names

                logger.info(f"Assigned {len(servers)} tools to {kernel['name']}: {', '.join(server_names)}")
            else:
                logger.info(f"No tools required for {kernel['name']}, skipping tool assignment")
                # Add empty lists to maintain consistency in structure
                kernel["assigned_tools"] = []
                kernel["servers"] = []
        return enhanced_structure

def main():
    """Main execution function for the script."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Assign appropriate tools to kernels based on their descriptions")
    parser.add_argument("input_file", type=str, help="Path to the JSON file containing the kernel structure")
    parser.add_argument("--output-file", type=str, default="enhanced_kernels.json",
                       help="Path to save the enhanced kernel structure with tool assignments")
    parser.add_argument("--openai-key", type=str, default=os.environ.get("OPENAI_API_KEY"),
                       help="OpenAI API Key (defaults to OPENAI_API_KEY environment variable)")
    parser.add_argument("--qdrant-host", type=str, default=os.environ.get("QDRANT_HOST", "192.168.194.33"),
                       help="Qdrant host (defaults to localhost)")
    parser.add_argument("--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", 6333)),
                       help="Qdrant port (defaults to 6333)")

    args = parser.parse_args()

    # Check for OpenAI API Key
    if not args.openai_key:
        logger.error("Error: OpenAI API Key is required. Set --openai-key or OPENAI_API_KEY environment variable.")
        exit(1)

    # Load the kernel structure from the input file
    try:
        with open(args.input_file, 'r') as f:
            kernel_structure = json.load(f)
    except Exception as e:
        logger.error(f"Error loading kernel structure from {args.input_file}: {e}")
        exit(1)

    # Initialize the KernelToolAssigner
    tool_assigner = KernelServerAssigner(
        openai_api_key=args.openai_key,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port
    )

    # Process the kernel structure and assign tools
    try:
        enhanced_structure = tool_assigner.assign_servers_to_kernels(kernel_structure)

        # Save the enhanced structure to the output file
        with open(args.output_file, 'w') as f:
            json.dump(enhanced_structure, f, indent=2)

        logger.info(f"Enhanced kernel structure saved to {args.output_file}")

        # Print a summary of the assigned tools
        print("\n--- Server Assignment Summary ---")
        for kernel in enhanced_structure.get("kernels", []):
            print(f"\n{kernel['name']} ({kernel['agent_type']}):")
            for server in kernel.get("assigned_servers", []):
                print(f"  - {server['name']} (Score: {server['relevance_score']:.4f})")
        print("\n-----------------------------")

    except Exception as e:
        logger.error(f"Error assigning tools to kernels: {e}")
        exit(1)

if __name__ == "__main__":
    main()
