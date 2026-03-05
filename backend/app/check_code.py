from agents import ItemHelpers, Runner

from app.base import (
    CodeCheckResult,
    EventType,
    IsCodeCheckError,
    LocalContext,
    PromptRequest,
    StreamResponse,
)
from app.custom_agents import get_code_check_agent
from app.logger import logger


async def check_gen_code(request: PromptRequest, context: LocalContext):
    logger.debug("check_gen_code called")
    file_path = context.gen_code_filepath
    code_check_agent = get_code_check_agent()
    result = Runner.run_streamed(
        starting_agent=code_check_agent,
        input=file_path,
        context=context,
        max_turns=context.max_turns,
    )

    async for event in result.stream_events():
        if event.type == "agent_updated_stream_event":
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

                output = event.item.output
                if isinstance(output, CodeCheckResult):
                    item_result = output.result
                    logger.debug(f"result: {item_result}")
                    if not item_result:
                        raise Exception(f"code check failed: {output.error_detail}")

                    eslint_result = output.eslint_result
                    logger.debug(f"eslint_result: {eslint_result}")
                    if eslint_result:
                        context.is_code_check_error = IsCodeCheckError.NO_ERROR
                        response = StreamResponse(
                            event=EventType.CHECK_RESULT,
                            payload={
                                "checker": "ESLint",
                                "result": eslint_result,
                                "rule_id": "",
                                "detail": "",
                            },
                        )
                        yield response.to_json_line()
                    else:
                        context.is_code_check_error = IsCodeCheckError.ESLINT_ERROR
                        eslint_infos = output.eslint_info or []
                        for eslint_info in eslint_infos:
                            desc = (eslint_info.description or "").strip()
                            if desc and desc not in context.add_prompts:
                                context.add_prompts.append(desc)
                            response = StreamResponse(
                                event=EventType.CHECK_RESULT,
                                payload={
                                    "checker": "ESLint",
                                    "result": eslint_result,
                                    "rule_id": eslint_info.rule_id,
                                    "detail": eslint_info.message,
                                },
                            )
                            yield response.to_json_line()
                else:
                    logger.warning(f"Unexpected output type: {type(output)}")

            elif event.item.type == "message_output_item":
                logger.debug("Event: message_output_item")
                logger.debug(
                    f"Message Output:\n {ItemHelpers.text_message_output(event.item)}"
                )
            else:
                logger.debug("Event: else / pass")
                pass
