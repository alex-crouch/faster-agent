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
