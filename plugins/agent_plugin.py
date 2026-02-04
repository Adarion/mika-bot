"""
Agent Plugin - Provides agent/tool-calling capabilities.
"""

from typing import Any, Callable, Dict, List, Optional
import json

from core.event_bus import Event
from core.plugin_manager import BasePlugin


class Tool:
    """Represents a callable tool for the agent."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        self.name = name
        self.description = description
        self.parameters = parameters  # JSON Schema format
        self.handler = handler
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class AgentPlugin(BasePlugin):
    """
    Agent plugin that provides tool-calling capabilities.
    
    Config:
        max_iterations: Maximum tool call iterations (default: 5).
        system_prompt: System prompt for the agent.
    """
    
    def __init__(self, event_bus, config: Dict[str, Any]):
        super().__init__(event_bus, config)
        self._tools: Dict[str, Tool] = {}
        self.max_iterations = config.get("max_iterations", 5)
    
    async def on_load(self) -> None:
        """Register event handlers and built-in tools."""
        self.subscribe("agent.invoke", self.handle_agent_invoke)
        
        # Register built-in tools
        self.register_tool(
            name="get_current_time",
            description="Get the current date and time",
            parameters={"type": "object", "properties": {}},
            handler=self._tool_get_time
        )
        
        print(f"AgentPlugin loaded with {len(self._tools)} tools")
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Register a new tool."""
        self._tools[name] = Tool(name, description, parameters, handler)
    
    async def handle_agent_invoke(self, event: Event) -> None:
        """Handle agent invocation requests."""
        message = event.data.get("message")
        llm_manager = event.data.get("llm_manager")
        system_prompt = event.data.get("system_prompt", self.config.get(
            "system_prompt",
            "You are a helpful assistant with access to tools. Use them when needed."
        ))
        
        if not message or not llm_manager:
            return
        
        try:
            response = await self.run_agent(
                query=message.content,
                llm_manager=llm_manager,
                system_prompt=system_prompt
            )
            
            await self.publish("message.reply", {
                "original": message,
                "content": response
            })
            
        except Exception as e:
            print(f"AgentPlugin error: {e}")
            await self.publish("message.reply", {
                "original": message,
                "content": f"Agent error: {e}"
            })
    
    async def run_agent(
        self,
        query: str,
        llm_manager,
        system_prompt: str
    ) -> str:
        """Run the agent loop with tool calling."""
        from adapters.llm.base import Message
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=query)
        ]
        
        tools = [tool.to_openai_format() for tool in self._tools.values()]
        
        for iteration in range(self.max_iterations):
            # Get adapter and call with tools
            adapter = llm_manager.get_adapter()
            response = await adapter.chat(
                messages=messages,
                tools=tools if tools else None
            )
            
            # Check for tool calls
            if response.tool_calls:
                # Execute each tool call
                for tool_call in response.tool_calls:
                    func_name = tool_call.get("function", {}).get("name")
                    func_args = tool_call.get("function", {}).get("arguments", "{}")
                    
                    if func_name in self._tools:
                        try:
                            args = json.loads(func_args) if isinstance(func_args, str) else func_args
                            result = await self._tools[func_name].handler(**args)
                        except Exception as e:
                            result = f"Error: {e}"
                    else:
                        result = f"Unknown tool: {func_name}"
                    
                    # Add tool result to messages
                    messages.append(Message(
                        role="assistant",
                        content="",
                        tool_calls=[tool_call]
                    ))
                    messages.append(Message(
                        role="tool",
                        content=str(result),
                        tool_call_id=tool_call.get("id", "unknown")
                    ))
            else:
                # No tool calls, return the response
                return response.content
        
        return "Agent reached maximum iterations without a final response."
    
    # Built-in tools
    async def _tool_get_time(self) -> str:
        """Get current time."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def available_tools(self) -> List[str]:
        """List available tool names."""
        return list(self._tools.keys())
