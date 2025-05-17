#!/usr/bin/env python3
"""
Kernel Go Command Generator for fast-agent

This script generates and optionally runs 'fast-agent go' commands for different kernels
defined in a JSON file.

Usage:
    python kernel_go.py [--run] [--json-file FILE] [--model MODEL] [--kernel KERNEL_NAME]

Examples:
    # Generate commands for all kernels in the default enhanced_kernels.json file
    python kernel_go.py
    
    # Generate and run a command for a specific kernel
    python kernel_go.py --run --kernel "Fetch Latest News from NYT"
    
    # Specify a different JSON file to read kernels from
    python kernel_go.py --json-file my_kernels.json --model openai.gpt-4o
"""

import argparse
import json
import os
import sys
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
    agent_type = kernel.get("agent_type", "")
    
    if description:
        instruction = f"{description}\n\nYou are acting as a {agent_type}."
        cmd_parts.append(f"--instruction=\"{instruction}\"")
    
    # Add servers if available
    servers = kernel.get("servers", [])
    if servers:
        servers_str = ",".join(servers)
        cmd_parts.append(f"--servers={servers_str}")
    
    # Join all parts into a single command string
    return " ".join(cmd_parts)


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


def main() -> None:
    """Main function to parse arguments and generate/run commands."""
    parser = argparse.ArgumentParser(
        description="Generate and optionally run fast-agent go commands for kernels."
    )
    parser.add_argument(
        "--json-file",
        default="enhanced_kernels.json",
        help="Path to the JSON file containing kernel definitions (default: enhanced_kernels.json)"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the generated command(s)"
    )
    parser.add_argument(
        "--model",
        default="openai.gpt-4.1-nano",
        help="Model to use for all kernels (default: openai.gpt-4.1-nano)"
    )
    parser.add_argument(
        "--kernel",
        help="Specific kernel to process (if omitted, all kernels are processed)"
    )
    
    args = parser.parse_args()
    
    # Load kernels from the JSON file
    kernels_data = load_kernels(args.json_file)
    
    # Generate and optionally run commands
    generate_go_commands(kernels_data, args.model, args.run, args.kernel)


if __name__ == "__main__":
    main()