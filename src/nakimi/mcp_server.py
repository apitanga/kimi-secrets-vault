"""
MCP Server for Nakimi.

Exposes all plugin commands as MCP tools over stdio transport.
Usage: nakimi serve
"""

import logging
import sys
from typing import Any

import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from nakimi.core.plugin import PluginCommand, PluginError, PluginManager

logger = logging.getLogger(__name__)


def plugin_command_to_input_schema(cmd: PluginCommand) -> dict:
    """Convert PluginCommand.args to JSON Schema for MCP inputSchema."""
    properties = {}
    required = []
    for arg_name, help_text, is_required in cmd.args:
        properties[arg_name] = {
            "type": "string",
            "description": help_text,
        }
        if is_required:
            required.append(arg_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def tool_name_from_command(full_command: str) -> str:
    """Convert 'gmail.unread' to 'gmail_unread' (dots not allowed in MCP tool names)."""
    return full_command.replace(".", "_")


def command_from_tool_name(tool_name: str) -> str:
    """Convert 'gmail_unread' back to 'gmail.unread'."""
    return tool_name.replace("_", ".", 1)


def build_tools(plugin_manager: PluginManager) -> list[types.Tool]:
    """Build MCP Tool list from all registered plugin commands."""
    tools = []
    for full_command in plugin_manager.list_commands():
        _, cmd = plugin_manager._commands[full_command]
        tool = types.Tool(
            name=tool_name_from_command(full_command),
            description=cmd.description,
            inputSchema=plugin_command_to_input_schema(cmd),
        )
        tools.append(tool)
    return tools


def create_server(plugin_manager: PluginManager) -> Server:
    """Create and configure the MCP server with all plugin tools."""
    server = Server("nakimi")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return build_tools(plugin_manager)

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        full_command = command_from_tool_name(name)
        args_dict = arguments or {}

        try:
            if full_command not in plugin_manager._commands:
                raise PluginError(f"Unknown command: {full_command}")

            _, cmd = plugin_manager._commands[full_command]

            result = await anyio.to_thread.run_sync(
                lambda: cmd.handler(**{k: v for k, v in args_dict.items()})
            )

            text = str(result) if result else "OK"
            return [types.TextContent(type="text", text=text)]

        except PluginError as e:
            return [types.TextContent(type="text", text=f"Error: {e}")]
        except Exception as e:
            logger.exception("Unexpected error executing %s", full_command)
            return [types.TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_async():
    """Main async entry point for the MCP server."""
    from nakimi.cli.main import load_secrets

    logger.info("Loading secrets...")
    try:
        secrets = load_secrets()
    except PluginError as e:
        print(f"Failed to load secrets: {e}", file=sys.stderr)
        sys.exit(1)

    manager = PluginManager(secrets)
    manager.discover_plugins()

    loaded = manager.list_plugins()
    if not loaded:
        print(
            "Warning: No plugins loaded. Check your secrets configuration.",
            file=sys.stderr,
        )
    else:
        print(f"Loaded plugins: {', '.join(loaded)}", file=sys.stderr)
        print(
            f"Available tools: {', '.join(manager.list_commands())}",
            file=sys.stderr,
        )

    server = create_server(manager)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run_server():
    """Synchronous entry point for MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    anyio.run(run_async)
