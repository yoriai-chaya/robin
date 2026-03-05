from typing import Any

from agents import Agent, RunContextWrapper, RunHooks, Tool

from app.logger import logger


class AgentLogger(RunHooks):
    def __init__(self):
        self.turn_idx = 0

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.turn_idx += 1
        logger.log("AGENT", f"[TURN {self.turn_idx}] agent_start: {agent.name}")

    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool: Tool
    ) -> None:
        logger.log(
            "AGENT", f"[TURN {self.turn_idx}] tool_start: {agent.name}.{tool.name}"
        )

    async def on_handoff(self, context: RunContextWrapper, from_agent, to_agent):
        logger.log(
            "AGENT",
            f"[TURN {self.turn_idx}] on_handoff: {from_agent.name} -> {to_agent.name}",
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        logger.log(
            "AGENT", f"[TURN {self.turn_idx}] tool_end: {agent.name}.{tool.name}"
        )
        logger.trace(f"[TURN {self.turn_idx}] result: {result}")

    async def on_agent_end(
        self, context: RunContextWrapper, agent: Agent, output: Any
    ) -> None:
        logger.log("AGENT", f"[TURN {self.turn_idx}] agent_end: {agent.name}")
        logger.debug(f"[TURN {self.turn_idx}] output_type: {type(output)}")
        logger.trace(f"[TURN {self.turn_idx}] output: {output}")
