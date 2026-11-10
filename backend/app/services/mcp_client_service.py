
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI

load_dotenv()

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8001/mcp",
)


async def generate_with_mcp(prompt: str, model: str) -> str:
    """Let OpenAI select and execute tools exposed by the MCP server."""

    client = AsyncOpenAI()

    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Discover tools from the MCP server.
            tool_result = await session.list_tools()

            openai_tools = []

            for tool in tool_result.tools:
                schema = tool.model_dump(by_alias=True)

                openai_tools.append({
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": schema.get("inputSchema", {}),
                    "strict": False,
                })

            input_items = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

            # Give the model opportunities to call tools and use their results.
            for _ in range(6):
                response = await client.responses.create(
                    model=model,
                    input=input_items,
                    tools=openai_tools,
                )

                calls = [
                    item for item in response.output
                    if item.type == "function_call"
                ]

                if not calls:
                    return response.output_text

                # Preserve the model's tool-call items for the next request.
                input_items.extend(response.output)

                for call in calls:
                    try:
                        arguments = json.loads(call.arguments)

                        result = await session.call_tool(
                            call.name,
                            arguments=arguments,
                        )

                        if result.isError:
                            output = {
                                "error": "MCP tool execution failed",
                                "details": [
                                    getattr(item, "text", "")
                                    for item in result.content
                                ],
                            }
                        else:
                            output = [
                                getattr(item, "text", str(item))
                                for item in result.content
                            ]

                    except Exception as exc:
                        output = {
                            "error": str(exc),
                            "tool": call.name,
                        }

                    input_items.append({
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(output),
                    })

            raise RuntimeError(
                "Maximum MCP tool-call rounds reached."
            )
