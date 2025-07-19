import sys
from pathlib import Path

from livekit.agents import Agent, RunContext, function_tool

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.logging import get_logger

logger = get_logger(__name__)

def agent_factory(agent_list):
    """
    Create agent classes from a list of agent definitions
    
    Args:
        agent_list: List of agent definitions (previously schema["agents"])
    
    Returns:
        dict: Map of agent names to agent classes
    """
    agent_map = {}
    # First pass: create empty slots for all agents by name
    for agent_def in agent_list:
        agent_map[agent_def["name"]] = None

    # Second pass: define classes with dynamic tools
    for agent_def in agent_list:
        name = agent_def["name"]
        instructions = agent_def.get("instructions", "")
        on_enter_prompt = agent_def.get("on_enter_prompt", "")
        tools = []

        # Process regular tools (empty for now, but ready for future use)
        for tool_spec in agent_def.get("tools", []):
            # Future: Add regular tool processing here
            pass

        # Create handoff tools from edges
        for edge_spec in agent_def.get("edges", []):
            tool_name = edge_spec["name"]
            description = edge_spec.get("description", "")
            action = edge_spec.get("action")
            target_agent = edge_spec.get("target_agent")  # Now a single string

            def create_handoff_tool(_action=action, _target=target_agent, _name=tool_name, _desc=description, _agent_map=agent_map):
                if _action == "handoff" and _target:
                    # Each edge now has a single specific target agent
                    schema = {
                        "type": "function",
                        "name": _name,
                        "description": f"{_desc}. Will handoff to: {_target}",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    
                    async def handler(raw_arguments: dict[str, object], context: RunContext):
                        if _target not in _agent_map or _agent_map[_target] is None:
                            return f"Error: Target agent {_target} not found"
                        new_agent = _agent_map[_target]()
                        logger.info(f"Handoff: {name} → {_target}")
                        return new_agent  # This triggers the handoff in LiveKit
                        
                else:
                    # Skip non-handoff tools for now
                    return "I can't do that right now."
                
                return function_tool(handler, raw_schema=schema)

            # Append the tool created with raw schema (only if it's not None)
            tool = create_handoff_tool()
            if tool is not None:
                tools.append(tool)

        # Define the agent class with tools and on_enter
        def make_agent_class(_name=name, _instructions=instructions, _on_enter_prompt=on_enter_prompt, _tools=tools):
            async def on_enter(self):
                if self._on_enter_prompt:
                    await self.session.say(self._on_enter_prompt)

            def __init__(self):
                super(cls, self).__init__(instructions=_instructions, tools=_tools)
                self._on_enter_prompt = _on_enter_prompt

            cls = type(
                _name,  # The actual class name
                (Agent,),
                {
                    "__init__": __init__,
                    "on_enter": on_enter,
                }
            )
            return cls


        agent_map[name] = make_agent_class()

    return agent_map