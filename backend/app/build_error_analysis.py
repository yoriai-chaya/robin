from agents import Runner
from agents.exceptions import AgentsException, ModelBehaviorError

from app.agent_logger import AgentLogger
from app.base import (
    BuildErrorAnalyzerResult,
    EventType,
    FunctionResult,
    LocalContext,
    StreamResponse,
)
from app.custom_agents import get_build_error_analyzer_agent
from app.logger import logger
from app.prompt_parser import load_agents_prompt, require_str


# function analyze_build_error
async def analyze_build_error(context: LocalContext, build_result: FunctionResult):
    logger.debug("analyze_build_error called")

    builderror_detail = build_result.detail
    if builderror_detail is None:
        raise ValueError("build_result.detail must not be None")
    agents_prompt = load_agents_prompt()
    build_error_analyzer_template_prompt = require_str(
        data=agents_prompt, key="prompt_build_error_analyzer"
    )
    filled_prompt = build_error_analyzer_template_prompt.format(
        build_error_log=builderror_detail
    )
    logger.debug(f"filled_prompt: {filled_prompt}")
    try:
        build_error_ayalyzer_agent = get_build_error_analyzer_agent()
        result = Runner.run_streamed(
            starting_agent=build_error_ayalyzer_agent,
            input=filled_prompt,
            context=context,
            max_turns=context.max_turns,
            hooks=AgentLogger(),
        )
        async for event in result.stream_events():
            if event.type == "raw_response_event":
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
                else:
                    pass

        final: BuildErrorAnalyzerResult = result.final_output
        logger.trace(f"final: {final}")
        yield StreamResponse(
            event=EventType.ANALYZER_RESULT, payload=final.model_dump()
        ).to_json_line()

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
