<p align="center">
<a href="https://pypi.org/project/fast-agent-mcp/"><img src="https://img.shields.io/pypi/v/fast-agent-mcp?color=%2334D058&label=pypi" /></a>
<a href="#"><img src="https://github.com/evalstate/fast-agent/actions/workflows/main-checks.yml/badge.svg" /></a>
<a href="https://github.com/evalstate/fast-agent/issues"><img src="https://img.shields.io/github/issues-raw/evalstate/fast-agent" /></a>
<a href="https://discord.gg/xg5cJ7ndN6"><img src="https://img.shields.io/discord/1358470293990936787" alt="discord" /></a>
<img alt="Pepy Total Downloads" src="https://img.shields.io/pepy/dt/fast-agent-mcp?label=pypi%20%7C%20downloads"/>
<a href="https://github.com/evalstate/fast-agent-mcp/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/fast-agent-mcp" /></a>
</p>

## faster Changes
> [!TIP]
> SQL database support
> In your fastagent.config.yaml (config file) supply a database uri to read MCP server list from an SQL3 database.
> Documentation site is in production here : https://fast-agent.ai. Feel free to feed back what's helpful and what's not. There is also an LLMs.txt [here](https://fast-agent.ai/llms.txt)

**`fast-agent`** enables you to create and interact with sophisticated Agents and Workflows in minutes. It is the first framework with complete, end-to-end tested MCP Feature support including Sampling. Model support is comprehensive with native support for Anthropic, OpenAI and Google as well as Azure, Ollama, Deepseek and dozens of others via TensorZero.

![multi_model_trim](https://github.com/user-attachments/assets/c8bf7474-2c41-4ef3-8924-06e29907d7c6)

The simple declarative syntax lets you concentrate on composing your Prompts and MCP Servers to [build effective agents](https://www.anthropic.com/research/building-effective-agents).

`fast-agent` is multi-modal, supporting Images and PDFs for both Anthropic and OpenAI endpoints via Prompts, Resources and MCP Tool Call results. The inclusion of passthrough and playback LLMs enable rapid development and test of Python glue-code for your applications.

> [!IMPORTANT]
>
> `fast-agent` The fast-agent documentation repo is here: https://github.com/evalstate/fast-agent-docs. Please feel free to submit PRs for documentation, experience reports or other content you think others may find helpful. All help and feedback warmly received.

### Agent Application Development

Prompts and configurations that define your Agent Applications are stored in simple files, with minimal boilerplate, enabling simple management and version control.

Chat with individual Agents and Components before, during and after workflow execution to tune and diagnose your application. Agents can request human input to get additional context for task completion.

Simple model selection makes testing Model <-> MCP Server interaction painless. You can read more about the motivation behind this project [here](https://llmindset.co.uk/resources/fast-agent/)

![2025-03-23-fast-agent](https://github.com/user-attachments/assets/8f6dbb69-43e3-4633-8e12-5572e9614728)

## Get started:

Start by installing the [uv package manager](https://docs.astral.sh/uv/) for Python. Then:

```bash
uv pip install fast-agent-mcp          # install fast-agent!
fast-agent go                          # start an interactive session
fast-agent go https://hf.co/mcp        # with a remote MCP
fast-agent go --model=generic.qwen2.5  # use ollama qwen 2.5
fast-agent setup                       # create an example agent and config files
uv run agent.py                        # run your first agent
uv run agent.py --model=o3-mini.low    # specify a model
fast-agent quickstart workflow  # create "building effective agents" examples
```

Other quickstart examples include a Researcher Agent (with Evaluator-Optimizer workflow) and Data Analysis Agent (similar to the ChatGPT experience), demonstrating MCP Roots support.

> [!TIP]
> Windows Users - there are a couple of configuration changes needed for the Filesystem and Docker MCP Servers - necessary changes are detailed within the configuration files.

### Basic Agents

Defining an agent is as simple as:

```python
otel:
  enabled: true # Enable or disable OpenTelemetry

database: "./examples/sqlite_servers/mcp_servers.db"

mcp:
  servers:
```

> [!TIP]
> qdrant database support
> In your fastagent.config.yaml (config file) supply a database url to read MCP server list from a qdrant database.
```python
otel:
  enabled: true # Enable or disable OpenTelemetry

qdrant_url: "http://localhost:6333"

mcp:
  servers:
```

## fast caught up
> [!TIP]
> Streamable HTTP Support

## other files

rag_search.py: Searches qdrant database for relevant MCP servers.

tool_assignment.py: Adds tools to JSON agent description file based on requested tools.

kernel_compose.py: Generates agent file from a JSON agent description file.
