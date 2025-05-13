#!/usr/bin/env python3
"""
Kernel Go Command Generator for fast-agent

This script generates 'fast-agent go' commands for kernels specified in a JSON file.
It reads kernel definitions and creates appropriate commands for each kernel,
using the specified model.

Usage:
    python kernel_go.py [--run] [--json-file FILE] [--model MODEL]

Examples:
    # Generate commands for kernels in the default enhanced_kernels.json file
    python kernel_go.py
    
    # Generate and run a command for a specific kernel from the file
    python kernel_go.py --run --kernel FetchLatestNYTStories
    
    # Specify a different JSON file to read kernels from
    python kernel_go.py --json-file my_kernels.json
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional


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


def generate_command(
    kernel_name: str,
    kernel_data: Dict,
    model: str = "openai.gpt-4.1-nano",
    instruction: Optional[str] = None,
) -> str:
    """
    Generate a fast-agent go command for the given kernel.
    
    Args:
        kernel_name: The name of the kernel
        kernel_data: Dictionary containing kernel configuration
        model: The model to use (default: openai.gpt-4.1-nano)
        instruction: Optional instruction for the agent
        
    Returns:
        A formatted command string
    """
    # Start with the base command
    cmd_parts = ["fast-agent", "go"]
    
    # Add the model parameter (always use the specified model)
    cmd_parts.append(f"--model={model}")
    
    # Add instruction if provided, otherwise use kernel description
    if instruction:
        cmd_parts.append(f'--instruction="{instruction}"')
    elif "description" in kernel_data:
        cmd_parts.append(f'--instruction="{kernel_data["description"]}"')
    
    # Add name parameter
    cmd_parts.append(f'--name="{kernel_name}"')
    
    # Add servers if available
    if "servers" in kernel_data and kernel_data["servers"]:
        servers = ",".join(kernel_data["servers"])
        cmd_parts.append(f"--servers={servers}")
    
    # Join all parts into a single command string
    return " ".join(cmd_parts)


def main() -> None:
    """Main function to parse arguments and generate/run commands."""
    parser = argparse.ArgumentParser(
        description="Generate and optionally run fast-agent go commands for kernels in a JSON file."
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
    data = load_kernels(args.json_file)
    
    # Check if the JSON has the expected structure
    if "kernels" not in data:
        print(f"Error: The JSON file does not contain a 'kernels' field.")
        sys.exit(1)
    
    # Process kernels
    kernels_data = data["kernels"]
    
    if args.kernel:
        # Process only the specified kernel
        kernel_found = False
        for kernel in kernels_data:
            if kernel.get("name") == args.kernel:
                kernel_found = True
                cmd = generate_command(kernel["name"], kernel, args.model)
                print(f"Command for {kernel['name']}: {cmd}")
                
                if args.run:
                    print(f"\nRunning command: {cmd}\n")
                    os.system(cmd)
                break
        
        if not kernel_found:
            print(f"Error: Kernel '{args.kernel}' not found in the JSON file.")
            print("Available kernels:")
            for kernel in kernels_data:
                print(f"  - {kernel.get('name', 'unnamed')}")
    else:
        # Process all kernels
        for kernel in kernels_data:
            if "name" in kernel:
                cmd = generate_command(kernel["name"], kernel, args.model)
                print(f"Command for {kernel['name']}: {cmd}")
                
                if args.run:
                    print(f"\nRunning command: {cmd}\n")
                    os.system(cmd)
                    # Only run the first kernel if multiple are specified
                    break
            else:
                print("Warning: Kernel without a name found, skipping.")


if __name__ == "__main__":
    main()