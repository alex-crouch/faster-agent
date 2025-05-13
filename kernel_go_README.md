# Kernel Go Command Generator for fast-agent

This utility script generates and optionally runs `fast-agent go` commands for kernels defined in a JSON file. It's designed to work with the JSON structure provided in `enhanced_kernels.json` and automatically configures each kernel with the appropriate settings.

## Features

- Read kernel definitions from a JSON file
- Generate appropriate `fast-agent go` commands for each kernel
- Always use the specified model (default: openai.gpt-4.1-nano)
- Optionally run the generated commands
- Configure server connections based on the kernel definition
- Use kernel descriptions as instructions if available

## Installation

No installation is required beyond having fast-agent installed. Simply place the `kernel_go.py` script in your project directory alongside your JSON kernel definition file.

## Usage

```bash
python kernel_go.py [--run] [--json-file FILE] [--model MODEL] [--kernel KERNEL_NAME]
```

### Arguments

- `--json-file`: Path to the JSON file containing kernel definitions (default: enhanced_kernels.json)
- `--run`: Flag to run the generated command (if multiple kernels are in the file, only the first one is run)
- `--model`: Model to use for all kernels (default: openai.gpt-4.1-nano)
- `--kernel`: Specific kernel to process (if omitted, all kernels are processed)

## JSON File Format

The script expects a JSON file with the following structure:

```json
{
  "summary": "Summary description",
  "kernels": [
    {
      "name": "KernelName",
      "description": "Kernel description",
      "servers": ["server1", "server2"]
    },
    ...
  ]
}
```

## Examples

### Generate commands for all kernels in the default file

```bash
python kernel_go.py
```

Output:
```
Command for FetchLatestNYTStories: fast-agent go --model=openai.gpt-4.1-nano --instruction="Retrieve the top 3 most recent news stories from The New York Times." --name="FetchLatestNYTStories" --servers=nyt-mcp-server,mcp-server-airbnb,mcp-searxng
Command for ParseAndSummarizeContent: fast-agent go --model=openai.gpt-4.1-nano --instruction="Extract and condense the main points or summaries from each news story." --name="ParseAndSummarizeContent"
Command for RewriteInGossipStyle: fast-agent go --model=openai.gpt-4.1-nano --instruction="Transform the summaries into snarky, fashionable gossip-style narratives." --name="RewriteInGossipStyle"
```

### Generate and run a command for a specific kernel

```bash
python kernel_go.py --run --kernel FetchLatestNYTStories
```

This will run:
```
fast-agent go --model=openai.gpt-4.1-nano --instruction="Retrieve the top 3 most recent news stories from The New York Times." --name="FetchLatestNYTStories" --servers=nyt-mcp-server,mcp-server-airbnb,mcp-searxng
```

### Use a different JSON file and model

```bash
python kernel_go.py --json-file my_kernels.json --model gpt-4-turbo
```

## Notes

- When using the `--run` flag with multiple kernels in the file, only the first kernel will be executed.
- The script will use the kernel's description as the instruction for the agent.
- Servers listed in the kernel's "servers" array will be automatically added to the command.
- By default, all commands will use "openai.gpt-4.1-nano" as the model.