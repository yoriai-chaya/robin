from typing import Awaitable, Callable

from agents import ItemHelpers, Runner

from app.agent_logger import AgentLogger
from app.base import (
    AgentResult,
    AgentResultPayload,
    AgentUpdatePayload,
    DonePayload,
    DoneStatus,
    EventType,
    LocalContext,
    SystemError,
)
from app.config import Settings
from app.custom_agents import get_place_files_agent
from app.logger import logger

SSEEventCallable = Callable[[str, dict], Awaitable[str]]


async def handle_place_files(
    prompt: str,
    context: LocalContext,
    settings: Settings,
    sse_event: SSEEventCallable,
):
    category = context.category
    logger.info(f"[{category}]: PlaceFiles Handler Called")

    try:
        final_payload = DonePayload(
            status=DoneStatus.COMPLETED, message="PlaceFiles completed"
        )
        place_files_agent = get_place_files_agent()
        result = Runner.run_streamed(
            starting_agent=place_files_agent,
            input=prompt,
            context=context,
            max_turns=context.max_turns,
            hooks=AgentLogger(),
        )
        async for event in result.stream_events():
            if event.type == "agent_updated_stream_event":
                logger.debug(f"Agent updated: {event.new_agent.name}")
                agent_name = event.new_agent.name
                agent_update_payload = AgentUpdatePayload(agent_name=agent_name)
                yield await sse_event(
                    EventType.AGENT_UPDATE, agent_update_payload.model_dump()
                )
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    logger.debug("Event: tool_call_item")
                elif event.item.type == "tool_call_output_item":
                    logger.debug(f"Event: tool_call_output_item : {event.item.output}")
                    output = event.item.output
                    if isinstance(output, AgentResult):
                        place_files_result = output.result
                        place_files_error_detail = output.error_detail
                        logger.debug(
                            f"place_files_result: {place_files_result}, place_files_error_detail: {place_files_error_detail}"
                        )
                        if place_files_result:
                            agent_result_payload = AgentResultPayload(
                                result=True, error_detail=""
                            )
                            yield await sse_event(
                                EventType.AGENT_RESULT,
                                agent_result_payload.model_dump(),
                            )
                        else:
                            agent_result_payload = AgentResultPayload(
                                result=False, error_detail=place_files_error_detail
                            )
                            yield await sse_event(
                                EventType.AGENT_RESULT,
                                agent_result_payload.model_dump(),
                            )
                            final_payload = DonePayload(
                                status=DoneStatus.FAILED, message="PlaceFiles Failed"
                            )

                elif event.item.type == "message_output_item":
                    logger.debug("Event: message_output_item")
                    logger.debug(
                        f"Message Output:\n {ItemHelpers.text_message_output(event.item)}"
                    )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"name: {e.__class__.__name__}, detail: {str(e)}")
        error_payload = SystemError(error="Unexpected error", detail=str(e))
        yield await sse_event(EventType.SYSTEM_ERROR, error_payload.model_dump())
        final_payload = DonePayload(
            status=DoneStatus.FAILED, message="place files error occurred"
        )

    logger.info(f"[{category}]: PlaceFiles Handler Completed")
    yield await sse_event(EventType.DONE, final_payload.model_dump())
