"""
Shared MCP Client Utilities

Provides helpers for agents to communicate with FastMCP servers via HTTP transport.
Uses FastMCP Client for proper MCP protocol communication.
"""
import asyncio
import logging
import json
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

_test_override: Optional[Callable] = None


def set_mcp_post_override(fn: Optional[Callable]) -> None:
    """Set a function to override MCP calls for testing."""
    global _test_override
    _test_override = fn


def call_mcp_tool_sync(server_url: str, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Synchronously invoke a tool on an MCP server via HTTP.

    Uses FastMCP Client for proper JSON-RPC protocol communication.
    For testing, can be overridden with set_mcp_post_override.
    """
    global _test_override

    if _test_override:
        response = _test_override(f"{server_url}/tools/{tool_name}", json=kwargs, timeout=10.0)
        response.raise_for_status()
        return response.json()

    try:
        from fastmcp import Client

        mcp_endpoint = f"{server_url}/mcp"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _call_mcp_async(mcp_endpoint, tool_name, kwargs)
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"MCP call failed: {tool_name} at {server_url} - {e}")
        raise


async def _call_mcp_async(mcp_endpoint: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Async helper to call MCP tool using FastMCP Client."""
    from fastmcp import Client

    async with Client(mcp_endpoint) as client:
        result = await client.call_tool(tool_name, arguments)

        if hasattr(result, 'structured_content') and result.structured_content is not None:
            return result.structured_content
        elif hasattr(result, 'data') and result.data is not None:
            data = result.data
            if hasattr(data, '__dict__'):
                return data.__dict__
            elif isinstance(data, dict):
                return data
            else:
                return {}
        elif hasattr(result, 'content') and result.content:
            text = result.content[0].text
            try:
                return json.loads(text)
            except (json.JSONDecodeError, IndexError, AttributeError):
                return {"result": text}
        else:
            return {}
