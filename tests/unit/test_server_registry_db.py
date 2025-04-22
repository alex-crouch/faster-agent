"""
Tests for the ServerRegistry functionality to load configurations from SQLite database.
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from mcp_agent.mcp_server_registry import ServerRegistry


class TestServerRegistryDB(unittest.TestCase):
    """Test cases for loading MCP server configurations from a SQLite database."""

    def setUp(self):
        """Set up a temporary SQLite database for testing."""
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        # Create the testing database schema
        self._create_test_db()

    def tearDown(self):
        """Clean up after test."""
        os.unlink(self.temp_db_path)

    def _create_test_db(self):
        """Create test database schema and insert sample data."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
        CREATE TABLE mcp_servers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            transport TEXT DEFAULT 'stdio',
            command TEXT,
            args TEXT,
            read_timeout_seconds INTEGER,
            read_transport_sse_timeout_seconds INTEGER,
            url TEXT,
            headers TEXT,
            api_key TEXT,
            env TEXT,
            roots_table TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE server_roots (
            id INTEGER PRIMARY KEY,
            server_name TEXT NOT NULL,
            uri TEXT NOT NULL,
            name TEXT,
            server_uri_alias TEXT
        )
        """)

        # Insert sample data
        cursor.execute("""
        INSERT INTO mcp_servers (
            name, description, transport, command, args, env, roots_table
        ) VALUES (
            'test_server', 
            'Test server from DB', 
            'stdio', 
            'python', 
            '["test_server.py", "--flag"]', 
            '{"ENV_VAR": "value"}', 
            'server_roots'
        )
        """)

        cursor.execute("""
        INSERT INTO mcp_servers (
            name, description, transport, url, headers, api_key
        ) VALUES (
            'test_sse', 
            'SSE server from DB', 
            'sse', 
            'https://example.com/mcp', 
            '{"Content-Type": "application/json"}',
            'test-api-key'
        )
        """)

        cursor.execute("""
        INSERT INTO server_roots (server_name, uri, name) 
        VALUES ('test_server', 'file:///test/path', 'test_root')
        """)

        conn.commit()
        conn.close()

    def test_load_registry_from_db(self):
        """Test loading server registry from SQLite database."""
        # Initialize registry with the test database
        registry = ServerRegistry(db_path=self.temp_db_path)

        # Check that servers were loaded from the database
        self.assertIn("test_server", registry.registry)
        self.assertIn("test_sse", registry.registry)

        # Check specific server settings
        test_server = registry.registry["test_server"]
        self.assertEqual(test_server.name, "test_server")
        self.assertEqual(test_server.description, "Test server from DB")
        self.assertEqual(test_server.transport, "stdio")
        self.assertEqual(test_server.command, "python")
        self.assertEqual(test_server.args, ["test_server.py", "--flag"])
        self.assertEqual(test_server.env, {"ENV_VAR": "value"})

        # Check SSE server configuration
        test_sse = registry.registry["test_sse"]
        self.assertEqual(test_sse.name, "test_sse")
        self.assertEqual(test_sse.transport, "sse")
        self.assertEqual(test_sse.url, "https://example.com/mcp")
        self.assertEqual(test_sse.headers, {"Content-Type": "application/json"})
        self.assertIsNotNone(test_sse.auth)
        self.assertEqual(test_sse.auth.api_key, "test-api-key")

        # Check roots
        self.assertIsNotNone(test_server.roots)
        self.assertEqual(len(test_server.roots), 1)
        self.assertEqual(test_server.roots[0].uri, "file:///test/path")
        self.assertEqual(test_server.roots[0].name, "test_root")

    def test_registry_merge(self):
        """Test merging servers from database with config-provided servers."""
        # Create a registry with both config and db servers
        from mcp_agent.config import Settings, MCPSettings, MCPServerSettings

        # Define a server in config
        config = Settings(
            mcp=MCPSettings(
                servers={
                    "yaml_server": MCPServerSettings(
                        name="yaml_server",
                        description="YAML config server",
                        transport="stdio",
                        command="echo",
                        args=["hello"],
                    )
                }
            )
        )

        # Initialize registry with both sources
        registry = ServerRegistry(config=config, db_path=self.temp_db_path)

        # Check that servers from both sources are present
        self.assertIn("yaml_server", registry.registry)
        self.assertIn("test_server", registry.registry)
        self.assertIn("test_sse", registry.registry)

        # Verify correct settings for each
        self.assertEqual(registry.registry["yaml_server"].description, "YAML config server")
        self.assertEqual(registry.registry["test_server"].description, "Test server from DB")

    def test_db_override_config(self):
        """Test that database configurations override YAML configurations with the same name."""
        from mcp_agent.config import Settings, MCPSettings, MCPServerSettings

        # Define a server in config with same name as in DB
        config = Settings(
            mcp=MCPSettings(
                servers={
                    "test_server": MCPServerSettings(
                        name="test_server",
                        description="YAML config version",
                        transport="stdio",
                        command="different",
                        args=["args"],
                    )
                }
            )
        )

        # Initialize registry with both sources
        registry = ServerRegistry(config=config, db_path=self.temp_db_path)

        # Check that the database version overrides the config
        self.assertEqual(registry.registry["test_server"].description, "Test server from DB")
        self.assertEqual(registry.registry["test_server"].command, "python")

    def test_nonexistent_database(self):
        """Test handling of nonexistent database file."""
        # Use a path that definitely doesn't exist
        nonexistent_path = str(Path(self.temp_db_path).parent / "nonexistent.db")

        # Should not raise an exception, just log a warning
        registry = ServerRegistry(db_path=nonexistent_path)

        # Check that no servers were loaded (empty dict)
        self.assertEqual(len(registry.registry), 0)

    def test_invalid_json_in_db(self):
        """Test handling of invalid JSON in database fields."""
        # Create a database with invalid JSON
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()

        # Insert a server with invalid JSON in args and env
        cursor.execute("""
        INSERT INTO mcp_servers (
            name, args, env
        ) VALUES (
            'invalid_json', 
            'not valid json', 
            '{also not valid json}'
        )
        """)

        conn.commit()
        conn.close()

        # Should not raise an exception, should handle gracefully
        registry = ServerRegistry(db_path=self.temp_db_path)

        # The server should still be loaded with null values for invalid fields
        self.assertIn("invalid_json", registry.registry)
        self.assertIsNone(registry.registry["invalid_json"].args)
        self.assertIsNone(registry.registry["invalid_json"].env)


if __name__ == "__main__":
    unittest.main()
