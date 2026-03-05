import re

from agents import Runner
from agents.exceptions import AgentsException, ModelBehaviorError
from openai.types.responses import ResponseTextDeltaEvent

from app.agent_logger import AgentLogger
from app.base import EventType, LocalContext, PromptRequest, StreamResponse
from app.config import get_settings
from app.custom_agents import get_code_gen_agent
from app.logger import logger

# for fault injection
FAULT_RE = re.compile(r"^\s*\[!FAULT\s+([A-Za-z0-9_]+)\s*\]\s*", re.I)
settings = get_settings()


def _extract_fault(prompt: str) -> str | None:
    m = FAULT_RE.match(prompt or "")
    return m.group(1) if m else None


def _maybe_inject_fault(prompt: str) -> None:
    if not settings.debug:
        return
    fault = _extract_fault(prompt)
    if not fault:
        return
    fault = fault.strip()
    if fault == "ModelBehaviorError":
        raise ModelBehaviorError("debug: ModelBehaviorError fault injection")
    elif fault == "AgentsException":
        raise AgentsException("debug: AgentsException fault injection")
    else:
        raise Exception("debug: Exception fault injection")


# function gen_code
async def gen_code(request: PromptRequest, context: LocalContext):
    logger.debug("gen_code called")
    try:
        _maybe_inject_fault(request.prompt)
        code_gen_agent = get_code_gen_agent()
        result = Runner.run_streamed(
            starting_agent=code_gen_agent,
            input=request.prompt,
            context=context,
            max_turns=context.max_turns,
            hooks=AgentLogger(),
        )
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    # print(f"token: {event.data.delta}")
                    # delta_text = event.data.delta
                    # yield delta_text
                    pass
            elif event.type == "agent_updated_stream_event":
                logger.debug(f"Agent updated: {event.new_agent.name}")
                agent_name = event.new_agent.name
                yield StreamResponse(
                    event=EventType.AGENT_UPDATE, payload={"agent_name": agent_name}
                ).to_json_line()
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    logger.debug("Event: tool_call_item")
                elif event.item.type == "tool_call_output_item":
                    logger.debug(f"Event: tool_call_output_item : {event.item.output}")
                elif event.item.type == "message_output_item":
                    logger.debug("Event: message_output_item")
                    if context.response:
                        # logger.debug(f"context code: {context.response.code}")
                        yield StreamResponse(
                            event=EventType.CODE,
                            payload={
                                "language": "tsx",
                                "code": context.response.code,
                                "file_path": context.gen_code_filepath,
                            },
                        ).to_json_line()
                else:
                    pass

    except ModelBehaviorError as e:
        logger.error(f"ModelBehaviorError: {e}")
        raise

    except AgentsException as e:
        logger.error(f"AgentsException error: {e}")
        logger.debug(f"name: {e.__class__.__name__}, detail: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"name: {e.__class__.__name__}, detail: {str(e)}")
        raise
