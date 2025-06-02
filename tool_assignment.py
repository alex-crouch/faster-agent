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

    def __init__(self, openai_api_key: str, qdrant_host: str = "192.168.194.33", qdrant_port: int = 6333):
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
        """Find appropriate tools for a given kernel based on its description and required tool types.

        Args:
            kernel: The kernel dictionary from the kernel structure
            max_servers: Maximum number of tools to assign to a kernel

        Returns:
            List of server dictionaries with name, description and relevance score
        """
        servers = []

        # Check if kernel has specific required tool types
        required_tool_types = kernel.get("required_tool_types", [])

        if required_tool_types:
            logger.info(f"Kernel '{kernel['name']}' requires specific tool types: {required_tool_types}")

            # Perform a search for each required tool type
            for tool_type in required_tool_types:
                # Construct a search query based on the tool type and kernel description
                # search_query = f"tool type: {tool_type}, {kernel['agent_type']}: {kernel['description']}"
                # logger.info(f"Searching servers for tool type '{tool_type}' with query: '{search_query}'")

                # Use ToolRAG to retrieve relevant tools for this type
                search_results = self.tool_rag.retrieve(tool_type)

                # Take the top result for each tool type
                if search_results:
                    result = search_results[0]
                    payload = result.payload
                    servers_name = payload.get(self.tool_rag.payload_name_field, f"Server {result.id}")
                    servers_desc = payload.get(self.tool_rag.payload_text_field, "No description available")

                    servers.append({
                        "name": servers_name,
                        "description": servers_desc,
                        "relevance_score": result.score,
                        "tool_type": tool_type
                    })
                    logger.info(f"Found server '{servers_name}' for tool type '{tool_type}' with score {result.score:.4f}")
        else:
            # Fallback to the original method if no specific tool types are defined
            search_query = f"{kernel['agent_type']}: {kernel['description']}"
            logger.info(f"No specific tool types defined. Searching servers for kernel '{kernel['name']}' with query: '{search_query}'")

            # Use ToolRAG to retrieve relevant tools
            search_results = self.tool_rag.retrieve(search_query)

            # Extract and format tool information
            for result in search_results[:max_servers]:  # Limit to max_tools
                payload = result.payload
                servers_name = payload.get(self.tool_rag.payload_name_field, f"Server {result.id}")
                servers_desc = payload.get(self.tool_rag.payload_text_field, "No description available")

                servers.append({
                    "name": servers_name,
                    "description": servers_desc,
                    "relevance_score": result.score,
                    "tool_type": "general"
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
                # Check if kernel has specified required tool types
                if not kernel.get("required_tool_types"):
                    # If tools are required but no types are specified, initialize the field
                    logger.warning(f"Kernel '{kernel['name']}' requires tools but no specific types are defined")
                    kernel["required_tool_types"] = []

                # Find tools for this kernel based on required types and descriptions
                servers = self.find_servers_for_kernel(kernel)

                # Add tools to the kernel
                kernel["assigned_tools"] = servers

                # Extract server names for FastAgent configuration
                server_names = [server["name"] for server in servers]
                kernel["servers"] = server_names

                # Group assigned tools by type for clarity
                tool_types_assigned = {}
                for server in servers:
                    tool_type = server.get("tool_type", "general")
                    if tool_type not in tool_types_assigned:
                        tool_types_assigned[tool_type] = []
                    tool_types_assigned[tool_type].append(server["name"])

                kernel["tool_types_assigned"] = tool_types_assigned

                logger.info(f"Assigned {len(servers)} tools to {kernel['name']}: {', '.join(server_names)}")
                for tool_type, tools in tool_types_assigned.items():
                    logger.info(f"  - Type '{tool_type}': {', '.join(tools)}")
            else:
                logger.info(f"No tools required for {kernel['name']}, skipping tool assignment")
                # Add empty lists to maintain consistency in structure
                kernel["assigned_tools"] = []
                kernel["servers"] = []
                kernel["tool_types_assigned"] = {}
                if not kernel.get("required_tool_types"):
                    kernel["required_tool_types"] = []
        return enhanced_structure

def main():
    """Main execution function for the script."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Assign appropriate tools to kernels based on their descriptions")
    parser.add_argument("input_file", type=str, help="Path to the JSON file containing the kernel structure")
    parser.add_argument("--output-file", type=str, default=None,
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

    # Set default output file if not specified
    if args.output_file is None:
        # Split the input filename and add "-enhanced" before the extension
        input_base, input_ext = os.path.splitext(args.input_file)
        args.output_file = f"{input_base}-enhanced{input_ext}"

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

            # Print required tool types
            required_types = kernel.get("required_tool_types", [])
            if required_types:
                print(f"  Required tool types: {', '.join(required_types)}")

            # Print assigned tools grouped by type
            tool_types = kernel.get("tool_types_assigned", {})
            if tool_types:
                for tool_type, servers in tool_types.items():
                    print(f"  - Type '{tool_type}': {', '.join(servers)}")
            else:
                for server in kernel.get("assigned_tools", []):
                    print(f"  - {server['name']} (Score: {server['relevance_score']:.4f}, Type: {server.get('tool_type', 'general')})")
        print("\n-----------------------------")

    except Exception as e:
        logger.error(f"Error assigning tools to kernels: {e}")
        exit(1)

if __name__ == "__main__":
    main()
