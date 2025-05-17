#!/usr/bin/env python3
"""
Kernel Manager for fast-agent

This is a unified script that provides tools to:
1. Generate fast-agent go commands for kernels (kernel_go.py functionality)
2. Compose kernels into a complete agent workflow (kernel_compose.py functionality)
3. Visualize the kernel workflow as a dependency graph
4. Validate kernels for completeness and correctness

Usage:
    python kernel_manager.py [command] [options]

Commands:
    go         Generate fast-agent go commands for kernels
    compose    Compose kernels into a complete agent workflow
    visualize  Generate a visualization of the kernel workflow
    validate   Validate the kernel definitions

Examples:
    # Generate go commands for all kernels
    python kernel_manager.py go

    # Compose kernels into an agent workflow
    python kernel_manager.py compose --output my_workflow.py

    # Visualize the kernel workflow
    python kernel_manager.py visualize
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


def load_kernels(json_file: str) -> Dict:
    """
    Load kernels from a JSON file.
    
    Args:
        json_file: Path to the JSON file containing kernel definitions
        
    Returns:
        Dictionary containing the parsed JSON data
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {json_file} contains invalid JSON.")
        sys.exit(1)


def validate_kernels(kernels_data: Dict) -> bool:
    """
    Validate the kernel definitions for completeness and correctness.
    
    Args:
        kernels_data: Dictionary containing kernel definitions
        
    Returns:
        True if valid, False otherwise
    """
    if "kernels" not in kernels_data:
        print("Error: The JSON file does not contain a 'kernels' field.")
        return False
    
    kernels = kernels_data["kernels"]
    if not kernels:
        print("Error: No kernels defined in the JSON file.")
        return False
    
    kernel_names = set()
    valid = True
    
    # First pass: collect all kernel names
    for i, kernel in enumerate(kernels):
        if "name" not in kernel:
            print(f"Error: Kernel at index {i} has no name.")
            valid = False
            continue
        
        name = kernel["name"]
        if name in kernel_names:
            print(f"Error: Duplicate kernel name '{name}'.")
            valid = False
        
        kernel_names.add(name)
    
    # Second pass: validate dependencies
    for i, kernel in enumerate(kernels):
        if "name" not in kernel:
            continue
        
        name = kernel["name"]
        deps = kernel.get("dependencies", [])
        
        for dep in deps:
            if dep not in kernel_names:
                print(f"Error: Kernel '{name}' depends on non-existent kernel '{dep}'.")
                valid = False
    
    # Check for circular dependencies
    try:
        execution_order = compute_execution_order(kernels)
        if len(execution_order) != len(kernel_names):
            print("Error: Circular dependencies detected in the kernel definitions.")
            valid = False
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        valid = False
    
    return valid


def compute_execution_order(kernels: List[Dict]) -> List[str]:
    """
    Compute the execution order of kernels based on dependencies.
    
    Args:
        kernels: List of kernel dictionaries
        
    Returns:
        List of kernel names in execution order
    """
    # Build dependency map
    dependency_map = {}
    for kernel in kernels:
        name = kernel.get("name", "")
        dependencies = kernel.get("dependencies", [])
        if name:
            dependency_map[name] = dependencies
    
    # Find kernels with no dependencies (starting points)
    no_deps = [k["name"] for k in kernels if not k.get("dependencies", [])]
    
    # Determine the execution order based on dependencies
    execution_order = []
    remaining = [k["name"] for k in kernels]
    
    # Start with kernels that have no dependencies
    current_level = no_deps
    
    while current_level and remaining:
        execution_order.extend(current_level)
        for name in current_level:
            if name in remaining:
                remaining.remove(name)
        
        # Find next level (kernels whose dependencies are all satisfied)
        next_level = []
        for name in remaining:
            deps = dependency_map.get(name, [])
            if all(dep in execution_order for dep in deps):
                next_level.append(name)
        
        current_level = next_level
    
    # If we still have remaining kernels, there might be circular dependencies
    if remaining:
        raise ValueError(f"Circular dependencies detected: {remaining}")
    
    return execution_order


def snake_case(text: str) -> str:
    """
    Convert text to snake_case for safe variable names.
    
    Args:
        text: The text to convert
        
    Returns:
        Snake case version of the text
    """
    # Convert spaces and special characters to underscores
    result = ''.join(c if c.isalnum() else '_' for c in text)
    
    # Remove consecutive underscores
    while '__' in result:
        result = result.replace('__', '_')
    
    # Remove leading and trailing underscores
    result = result.strip('_')
    
    return result.lower()


def generate_agent_file(kernels_data: Dict, output_file: str, model: str = "openai.gpt-4.1-nano") -> None:
    """
    Generate a complete agent file from kernel definitions.
    
    Args:
        kernels_data: Dictionary containing kernel definitions
        output_file: Path to save the generated Python file
        model: The model to use for all agents (default: openai.gpt-4.1-nano)
    """
    if not validate_kernels(kernels_data):
        print("Warning: Kernel validation failed. The generated file may not work as expected.")
    
    kernels = kernels_data["kernels"]
    summary = kernels_data.get("summary", "Generated workflow from kernel definitions")
    execution_sequence = kernels_data.get("execution_sequence", "")
    
    # Create a mapping between original kernel names and safe variable names
    kernel_name_map = {}
    for kernel in kernels:
        original_name = kernel.get("name", "")
        if original_name:
            safe_name = snake_case(original_name)
            # Make sure we don't have duplicate names after conversion
            base_name = safe_name
            counter = 1
            while safe_name in kernel_name_map.values():
                safe_name = f"{base_name}_{counter}"
                counter += 1
            kernel_name_map[original_name] = safe_name
    
    # Compute execution order
    try:
        execution_order = compute_execution_order(kernels)
        # Map to safe names
        execution_order_safe = [kernel_name_map[name] for name in execution_order]
    except ValueError as e:
        print(f"Warning: {e}")
        execution_order = [k["name"] for k in kernels]
        execution_order_safe = [kernel_name_map[name] for name in execution_order]
    
    # Generate imports and FastAgent setup
    code = [
        "#!/usr/bin/env python3",
        '"""',
        f"{summary}",
        "",
        "This file was auto-generated by kernel_compose.py",
        '"""',
        "",
        "import asyncio",
        "# import json",
        "from mcp_agent.core.fastagent import FastAgent",
        "# from pathlib import Path",
        "# from typing import List, Dict, Any",
        "",
        f"# Create the FastAgent application",
        f'fast = FastAgent(name="Kernel Workflow")',
        "",
    ]
    
    # Generate agent definitions
    for kernel in kernels:
        original_name = kernel.get("name", "")
        if not original_name:
            continue
            
        safe_name = kernel_name_map[original_name]
        agent_type = kernel.get("agent_type", "")
        description = kernel.get("description", "")
        servers = kernel.get("servers", [])
        tools_required = kernel.get("tools_required", "False")
        
        # Format servers if they exist
        servers_param = ""
        if servers and len(servers) > 0:
            servers_str = ", ".join([f'"{s}"' for s in servers])
            servers_param = f'servers=[{servers_str}],'
        
        # Create the agent decorator
        agent_code = [
            f'@fast.agent(',
            f'    name="{safe_name}",',
            f'    instruction="""{description}',
            f'',
            f'    You are acting as a {agent_type}',
            f'    """,',
        ]
        
        # Add servers if needed
        if servers_param:
            agent_code.append(f'    {servers_param}')
            
        # Add model parameter
        agent_code.append(f'    model="{model}",')
        
        # Close the decorator
        agent_code.append(')')
        
        # Add the agent code to the main code list
        code.extend(agent_code)
    
    # Create main workflow chain if there are multiple kernels
    if len(execution_order_safe) > 1:
        # Format sequence
        sequence_str = ", ".join([f'"{s}"' for s in execution_order_safe])
        
        chain_code = [
            "",
            f'@fast.chain(',
            f'    name="WorkflowChain",',
            f'    sequence=[{sequence_str}],',
            f'    instruction="{summary}",',
            f'    cumulative=False,',
            ')'
        ]
        
        # Add the chain code to the main code list
        code.extend(chain_code)
    
    # Generate the main function
    main_func = [
        "",
        "async def main() -> None:",
        "    async with fast.run() as agent:",
    ]
    
    # Choose how to start the agent based on chain existence
    if len(execution_order_safe) > 1:
        main_func.extend([
            "        # Run the workflow and get the final result",
            '        result = await agent.WorkflowChain.send("")',
            "",
            "        # Print the result",
            "        # print(\"\\nWorkflow completed!\\n\")",
            "        # print(result)",
            "",
            "        # Start interactive mode with the last agent in the chain",
            "        # await agent.Rewrite in Gossip Girl Style.interactive()",
        ])
    elif execution_order_safe:
        main_func.extend([
            f'        # Start interactive mode with the only agent',
            f'        await agent.{execution_order_safe[0]}.interactive()',
        ])
    else:
        main_func.append('        await agent.interactive()')
        
    # Add the entry point code
    entry_point = [
        "",
        'if __name__ == "__main__":',
        '    asyncio.run(main())',
        ""
    ]
    
    # Combine all code sections
    code.extend(main_func)
    code.extend(entry_point)
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write("\n".join(code))
        
    print(f"Generated agent file: {output_file}")
    
    # Make the file executable
    try:
        os.chmod(output_file, 0o755)
    except:
        print("Warning: Could not make the file executable.")


def generate_go_commands(kernels_data: Dict, model: str = "openai.gpt-4.1-nano", run: bool = False, kernel_name: Optional[str] = None) -> None:
    """
    Generate fast-agent go commands for kernels.
    
    Args:
        kernels_data: Dictionary containing kernel definitions
        model: Model to use for all kernels (default: openai.gpt-4.1-nano)
        run: Whether to run the command (default: False)
        kernel_name: Name of a specific kernel to run (default: None)
    """
    if "kernels" not in kernels_data:
        print("Error: The JSON file does not contain a 'kernels' field.")
        sys.exit(1)
    
    kernels = kernels_data["kernels"]
    
    if kernel_name:
        # Process only the specified kernel
        kernel_found = False
        for kernel in kernels:
            if kernel.get("name") == kernel_name:
                kernel_found = True
                cmd = build_go_command(kernel, model)
                print(f"Command for {kernel['name']}: {cmd}")
                
                if run:
                    print(f"\nRunning command: {cmd}\n")
                    os.system(cmd)
                break
        
        if not kernel_found:
            print(f"Error: Kernel '{kernel_name}' not found in the JSON file.")
            print("Available kernels:")
            for kernel in kernels:
                print(f"  - {kernel.get('name', 'unnamed')}")
    else:
        # Process all kernels
        for kernel in kernels:
            if "name" in kernel:
                cmd = build_go_command(kernel, model)
                print(f"Command for {kernel['name']}: {cmd}")
                
                if run:
                    print(f"\nRunning command: {cmd}\n")
                    os.system(cmd)
                    # Only run the first kernel if multiple are specified
                    break
            else:
                print("Warning: Kernel without a name found, skipping.")


def build_go_command(kernel: Dict, model: str = "openai.gpt-4.1-nano") -> str:
    """
    Build a fast-agent go command for a kernel.
    
    Args:
        kernel: Dictionary containing kernel configuration
        model: Model to use (default: openai.gpt-4.1-nano)
        
    Returns:
        A formatted command string
    """
    # Start with the base command
    cmd_parts = ["fast-agent", "go"]
    
    # Add the model parameter
    cmd_parts.append(f"--model={model}")
    
    # Add name parameter
    name = kernel.get("name", "")
    if name:
        cmd_parts.append(f"--name=\"{name}\"")
    
    # Add instruction based on description
    description = kernel.get("description", "")
    if description:
        cmd_parts.append(f"--instruction=\"{description}\"")
    
    # Add servers if available
    servers = kernel.get("servers", [])
    if servers:
        servers_str = ",".join(servers)
        cmd_parts.append(f"--servers={servers_str}")
    
    # Join all parts into a single command string
    return " ".join(cmd_parts)


def generate_visualization(kernels_data: Dict, output_file: Optional[str] = None) -> None:
    """
    Generate a visualization of the kernel workflow.
    
    Args:
        kernels_data: Dictionary containing kernel definitions
        output_file: Path to save the visualization (default: kernel_workflow.png)
    """
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: This feature requires networkx and matplotlib.")
        print("Install them with: pip install networkx matplotlib")
        return
    
    if "kernels" not in kernels_data:
        print("Error: The JSON file does not contain a 'kernels' field.")
        return
    
    kernels = kernels_data["kernels"]
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes (kernels)
    for kernel in kernels:
        name = kernel.get("name", "")
        if name:
            G.add_node(name)
    
    # Add edges (dependencies)
    for kernel in kernels:
        name = kernel.get("name", "")
        dependencies = kernel.get("dependencies", [])
        for dep in dependencies:
            G.add_edge(dep, name)
    
    # Set up the plot
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    # Draw nodes and edges
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=1500, arrows=True, connectionstyle='arc3,rad=0.1')
    
    # Save or show the figure
    if output_file:
        plt.savefig(output_file)
        print(f"Visualization saved to {output_file}")
    else:
        default_output = "kernel_workflow.png"
        plt.savefig(default_output)
        print(f"Visualization saved to {default_output}")


def command_go(args):
    """Handle the 'go' command."""
    kernels_data = load_kernels(args.json_file)
    generate_go_commands(kernels_data, args.model, args.run, args.kernel)


def command_compose(args):
    """Handle the 'compose' command."""
    kernels_data = load_kernels(args.json_file)
    
    # Set default output file if not provided
    output_file = args.output
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"generated_workflow_{timestamp}.py"
    
    generate_agent_file(kernels_data, output_file, args.model)
    
    # Run the agent if requested
    if args.run:
        print(f"Running generated agent file: {output_file}")
        try:
            subprocess.run(["uv", "run", output_file], check=True)
        except subprocess.CalledProcessError:
            print("Error running the generated agent file.")
        except FileNotFoundError:
            print("Error: 'uv' command not found. Please install UV or run the file manually.")
            print(f"You can run it with: python {output_file}")


def command_visualize(args):
    """Handle the 'visualize' command."""
    kernels_data = load_kernels(args.json_file)
    generate_visualization(kernels_data, args.output)


def command_validate(args):
    """Handle the 'validate' command."""
    kernels_data = load_kernels(args.json_file)
    if validate_kernels(kernels_data):
        print("Kernel validation successful! The kernel definitions are valid.")
    else:
        print("Kernel validation failed. Please fix the errors and try again.")


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description="Kernel Manager for fast-agent"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Common arguments
    json_file_arg = {"help": "Path to the JSON file containing kernel definitions (default: enhanced_kernels.json)",
                   "default": "enhanced_kernels.json"}
    model_arg = {"help": "Model to use for all agents (default: openai.gpt-4.1-nano)",
               "default": "openai.gpt-4.1-nano"}
    
    # 'go' command
    go_parser = subparsers.add_parser("go", help="Generate fast-agent go commands for kernels")
    go_parser.add_argument("--json-file", **json_file_arg)
    go_parser.add_argument("--model", **model_arg)
    go_parser.add_argument("--run", action="store_true", help="Run the generated command")
    go_parser.add_argument("--kernel", help="Specific kernel to process")
    
    # 'compose' command
    compose_parser = subparsers.add_parser("compose", help="Compose kernels into a complete agent workflow")
    compose_parser.add_argument("--json-file", **json_file_arg)
    compose_parser.add_argument("--output", help="Path where the generated agent file will be saved")
    compose_parser.add_argument("--model", **model_arg)
    compose_parser.add_argument("--run", action="store_true", help="Run the generated agent file after creation")
    
    # 'visualize' command
    visualize_parser = subparsers.add_parser("visualize", help="Generate a visualization of the kernel workflow")
    visualize_parser.add_argument("--json-file", **json_file_arg)
    visualize_parser.add_argument("--output", help="Path where the visualization will be saved")
    
    # 'validate' command
    validate_parser = subparsers.add_parser("validate", help="Validate the kernel definitions")
    validate_parser.add_argument("--json-file", **json_file_arg)
    
    args = parser.parse_args()
    
    if args.command == "go":
        command_go(args)
    elif args.command == "compose":
        command_compose(args)
    elif args.command == "visualize":
        command_visualize(args)
    elif args.command == "validate":
        command_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()