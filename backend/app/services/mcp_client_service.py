
import json
import os
import logging

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8001/mcp",
)


async def generate_with_mcp(prompt: str, model: str) -> str:
    """Generate an itinerary using OpenAI and MCP tools."""

    client = AsyncOpenAI()

    logger.info("Connecting to MCP server: %s", MCP_SERVER_URL)

    try:
        async with streamable_http_client(MCP_SERVER_URL) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            logger.info("MCP HTTP connection established")

            async with ClientSession(read_stream, write_stream) as session:

                await session.initialize()
                logger.info("MCP session initialized")

                # Discover MCP tools
                tool_result = await session.list_tools()

                logger.info(
                    "Available MCP tools: %s",
                    [tool.name for tool in tool_result.tools],
                )

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

                if not openai_tools:
                    raise RuntimeError("No MCP tools were discovered.")

                input_items = [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]

                # Allow the model to call MCP tools
                for round_number in range(6):

                    logger.info(
                        "Starting OpenAI tool-call round %s",
                        round_number + 1,
                    )

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
                        if not response.output_text:
                            raise RuntimeError(
                                "OpenAI returned an empty itinerary."
                            )

                        return response.output_text

                    input_items.extend(response.output)

                    for call in calls:
                        logger.info("Executing MCP tool: %s", call.name)

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

                        input_items.append({
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(output),
                        })

                raise RuntimeError(
                    "Maximum MCP tool-call rounds reached."
                )

    except Exception:
        logger.exception("MCP itinerary generation failed")
        raise
