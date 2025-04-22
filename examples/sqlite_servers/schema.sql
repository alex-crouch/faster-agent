-- MCP Server Configurations Schema

-- Main table for storing MCP server configurations
CREATE TABLE mcp_servers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    transport TEXT NOT NULL DEFAULT 'stdio',
    command TEXT,
    args TEXT,  -- JSON array as string
    read_timeout_seconds INTEGER,
    read_transport_sse_timeout_seconds INTEGER DEFAULT 300,
    url TEXT,
    headers TEXT,  -- JSON object as string
    api_key TEXT,
    env TEXT,  -- JSON object as string
    roots_table TEXT  -- Reference to a table containing roots for this server
);

-- Table for storing root directories for filesystem servers
CREATE TABLE server_roots (
    id INTEGER PRIMARY KEY,
    server_name TEXT NOT NULL,
    uri TEXT NOT NULL,
    name TEXT,
    server_uri_alias TEXT,
    FOREIGN KEY(server_name) REFERENCES mcp_servers(name)
);

-- Insert sample server configurations

-- Example stdio server: everything
INSERT INTO mcp_servers (
    name, description, transport, command, args
) VALUES (
    'everything',
    'exercise all the features of the MCP protocol',
    'stdio',
    'npx',
    '["-y", "@modelcontextprotocol/server-everything"]'
);

-- Example stdio server: fetch
INSERT INTO mcp_servers (
    name, description, transport, command, args
) VALUES (
    'fetch',
    'HTTP fetch server',
    'stdio',
    'uvx',
    '["mcp-server-fetch"]'
);

-- -- Example SSE server
-- INSERT INTO mcp_servers (
--     name, description, transport, url, headers, api_key
-- ) VALUES (
--     'remote-fs',
--     'Remote filesystem server over SSE',
--     'sse',
--     'https://example.com/mcp/filesystem',
--     '{"Authorization": "Bearer ${MCP_FS_TOKEN}"}',
--     'secret-api-key-12345'
-- );

-- -- Add roots for the filesystem server
-- INSERT INTO server_roots (server_name, uri, name) 
-- VALUES ('filesystem', 'file:///home/user/projects', 'projects');

-- INSERT INTO server_roots (server_name, uri, name) 
-- VALUES ('filesystem', 'file:///home/user/documents', 'docs');