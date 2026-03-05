import json

from agents import Runner
from agents.exceptions import AgentsException, ModelBehaviorError

from app.agent_logger import AgentLogger
from app.base import (
    AgentResult,
    BuildErrorAnalyzerResult,
    EventType,
    LocalContext,
    StreamResponse,
)
from app.custom_agents import get_build_error_fixer_agent
from app.logger import logger
from app.prompt_parser import load_agents_prompt, require_str


# function fix_code
async def fix_code(context: LocalContext, analyzer_result: BuildErrorAnalyzerResult):
    logger.debug("fix_code called")

    try:
        agents_prompt = load_agents_prompt()
        build_error_fixer_template_prompt = require_str(
            data=agents_prompt, key="prompt_build_error_fixer"
        )
        filled_prompt = build_error_fixer_template_prompt.format(
            summary=analyzer_result.summary,
            root_cause=analyzer_result.root_cause,
            files_to_fix=json.dumps(analyzer_result.files_to_fix, ensure_ascii=False),
            fix_policy=json.dumps(analyzer_result.fix_policy, ensure_ascii=False),
        )
        logger.debug(f"filled_prompt: {filled_prompt}")
        fixer_agent = get_build_error_fixer_agent()
        result = Runner.run_streamed(
            starting_agent=fixer_agent,
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

        final: AgentResult = result.final_output
        logger.debug(f"final: {final}")
        yield StreamResponse(
            event=EventType.AGENT_RESULT, payload=final.model_dump()
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
