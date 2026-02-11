"""
Unit tests for mcp_server.py - MCP server bridge.
"""

import pytest
from nakimi.core.plugin import Plugin, PluginCommand, PluginError, PluginManager

# Skip all tests if mcp package is not installed
mcp_server = pytest.importorskip("nakimi.mcp_server")


# --- Test helper ---


class SamplePlugin(Plugin):
    """Minimal plugin for testing."""

    PLUGIN_NAME = "sample"

    @property
    def description(self):
        return "Sample plugin for tests"

    def _validate_secrets(self):
        pass

    def get_commands(self):
        return [
            PluginCommand("hello", "Say hello", self.cmd_hello, []),
            PluginCommand(
                "greet",
                "Greet someone",
                self.cmd_greet,
                [("name", "Person to greet", True)],
            ),
            PluginCommand(
                "search",
                "Search things",
                self.cmd_search,
                [
                    ("query", "Search query", True),
                    ("limit", "Max results", False),
                ],
            ),
        ]

    def cmd_hello(self):
        return "Hello!"

    def cmd_greet(self, name):
        return f"Hello, {name}!"

    def cmd_search(self, query, limit="10"):
        return f"Searching '{query}' (limit {limit})"


def _make_manager():
    """Create a PluginManager with SamplePlugin registered."""
    manager = PluginManager({"sample": {"key": "val"}})
    manager.register_plugin(SamplePlugin, {"key": "val"})
    return manager


# --- Tests ---


class TestPluginCommandToInputSchema:
    """Test JSON Schema generation from PluginCommand args."""

    def test_no_args(self):
        cmd = PluginCommand("hello", "Say hello", lambda: None, [])
        schema = mcp_server.plugin_command_to_input_schema(cmd)
        assert schema == {"type": "object", "properties": {}}

    def test_required_arg(self):
        cmd = PluginCommand(
            "greet",
            "Greet",
            lambda n: None,
            [("name", "Person to greet", True)],
        )
        schema = mcp_server.plugin_command_to_input_schema(cmd)
        assert schema["properties"]["name"] == {
            "type": "string",
            "description": "Person to greet",
        }
        assert schema["required"] == ["name"]

    def test_optional_arg(self):
        cmd = PluginCommand(
            "list",
            "List items",
            lambda l: None,
            [("limit", "Max results", False)],
        )
        schema = mcp_server.plugin_command_to_input_schema(cmd)
        assert "limit" in schema["properties"]
        assert "required" not in schema

    def test_mixed_args(self):
        cmd = PluginCommand(
            "search",
            "Search",
            lambda q, l: None,
            [
                ("query", "Search query", True),
                ("limit", "Max results", False),
            ],
        )
        schema = mcp_server.plugin_command_to_input_schema(cmd)
        assert len(schema["properties"]) == 2
        assert schema["required"] == ["query"]

    def test_multiple_required(self):
        cmd = PluginCommand(
            "send",
            "Send message",
            lambda t, s, b: None,
            [
                ("to", "Recipient", True),
                ("subject", "Subject", True),
                ("body", "Body", True),
            ],
        )
        schema = mcp_server.plugin_command_to_input_schema(cmd)
        assert schema["required"] == ["to", "subject", "body"]


class TestToolNameConversion:
    """Test tool name conversion between MCP and plugin formats."""

    def test_dot_to_underscore(self):
        assert mcp_server.tool_name_from_command("gmail.unread") == "gmail_unread"

    def test_underscore_to_dot(self):
        assert mcp_server.command_from_tool_name("gmail_unread") == "gmail.unread"

    def test_roundtrip(self):
        original = "gmail.search"
        converted = mcp_server.tool_name_from_command(original)
        restored = mcp_server.command_from_tool_name(converted)
        assert restored == original

    def test_single_word_plugin(self):
        assert mcp_server.tool_name_from_command("calendar.events") == "calendar_events"
        assert mcp_server.command_from_tool_name("calendar_events") == "calendar.events"


class TestBuildTools:
    """Test MCP Tool list generation from PluginManager."""

    def test_correct_tool_count(self):
        manager = _make_manager()
        tools = mcp_server.build_tools(manager)
        assert len(tools) == 3

    def test_tool_names_use_underscore(self):
        manager = _make_manager()
        tools = mcp_server.build_tools(manager)
        names = {t.name for t in tools}
        assert "sample_hello" in names
        assert "sample_greet" in names
        assert "sample_search" in names

    def test_tool_descriptions(self):
        manager = _make_manager()
        tools = mcp_server.build_tools(manager)
        tool_map = {t.name: t for t in tools}
        assert tool_map["sample_hello"].description == "Say hello"
        assert tool_map["sample_greet"].description == "Greet someone"
        assert tool_map["sample_search"].description == "Search things"

    def test_tool_input_schema(self):
        manager = _make_manager()
        tools = mcp_server.build_tools(manager)
        tool_map = {t.name: t for t in tools}

        # hello has no args
        assert tool_map["sample_hello"].inputSchema == {
            "type": "object",
            "properties": {},
        }

        # greet has one required arg
        greet_schema = tool_map["sample_greet"].inputSchema
        assert "name" in greet_schema["properties"]
        assert greet_schema["required"] == ["name"]

        # search has one required, one optional
        search_schema = tool_map["sample_search"].inputSchema
        assert len(search_schema["properties"]) == 2
        assert search_schema["required"] == ["query"]

    def test_empty_manager(self):
        manager = PluginManager()
        tools = mcp_server.build_tools(manager)
        assert tools == []


class TestCreateServer:
    """Test MCP server creation."""

    def test_server_created(self):
        manager = PluginManager()
        server = mcp_server.create_server(manager)
        assert server.name == "nakimi"

    def test_server_with_plugins(self):
        manager = _make_manager()
        server = mcp_server.create_server(manager)
        assert server.name == "nakimi"
