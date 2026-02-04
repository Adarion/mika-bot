"""
Command Plugin - Handles command-style messages (e.g., /help, /ping).
"""

from typing import Any, Callable, Dict, List, Optional

from core.event_bus import Event
from core.plugin_manager import BasePlugin


import yaml
from pathlib import Path

# 默认角色 (Fallback)
PRESET_ROLES = {
    "mika": {
        "name": "Mika",
        "prompt": "You are a helpful assistant."
    }
}


class CommandPlugin(BasePlugin):
    """
    Command plugin that handles slash commands.
    
    Config:
        prefix: Command prefix (default: "/").
        commands: Dict of command configs.
    """
    
    def __init__(self, event_bus, config: Dict[str, Any]):
        super().__init__(event_bus, config)
        self._commands: Dict[str, Callable] = {}
        self.prefix = config.get("prefix", "/")
        # 用户当前角色设定
        self._user_roles: Dict[str, str] = {}
        self._available_roles = {}
    
    async def on_load(self) -> None:
        """Register event handlers and built-in commands."""
        self._load_roles_from_disk()
        
        self.subscribe("message.received", self.handle_message)
        
        # Register built-in commands
        self.register_command("help", self.cmd_help, "显示可用命令")
        self.register_command("ping", self.cmd_ping, "测试机器人是否在线")
        self.register_command("status", self.cmd_status, "查看机器人状态")
        self.register_command("memory", self.cmd_memory, "查看记忆统计")
        self.register_command("clear", self.cmd_clear, "清除当前对话记忆")
        self.register_command("role", self.cmd_role, "切换角色 (如: /role 圣园未花)")
        self.register_command("roles", self.cmd_roles, "显示可用角色列表")
        self.register_command("reload_roles", self.cmd_reload_roles, "重载角色配置")
        
        print(f"CommandPlugin loaded with prefix: {self.prefix}")

    def _load_roles_from_disk(self):
        """Load roles from data/roles.yaml."""
        roles_path = Path("data/roles.yaml")
        try:
            if roles_path.exists():
                with open(roles_path, "r", encoding="utf-8") as f:
                    self._available_roles = yaml.safe_load(f) or {}
                print(f"Loaded {len(self._available_roles)} roles from {roles_path}")
            else:
                print(f"Warning: {roles_path} not found. Using fallback.")
                self._available_roles = PRESET_ROLES
        except Exception as e:
            print(f"Error loading roles: {e}")
            self._available_roles = PRESET_ROLES

    def register_command(
        self, 
        name: str, 
        handler: Callable, 
        description: str = ""
    ) -> None:
        """Register a command handler."""
        self._commands[name.lower()] = {
            "handler": handler,
            "description": description
        }
    
    def get_user_role(self, user_id: str) -> Dict[str, str]:
        """Get current role for user."""
        role_name = self._user_roles.get(user_id, "mika")
        # Fallback to mika if role not found in available roles
        if role_name not in self._available_roles and "mika" in self._available_roles:
            role_name = "mika"
        return self._available_roles.get(role_name, PRESET_ROLES["mika"])
    
    def set_user_role(self, user_id: str, role_name: str) -> bool:
        """Set role for user. Returns True if successful."""
        # Case-insensitive search
        target = role_name.lower()
        for key in self._available_roles.keys():
            if key.lower() == target:
                self._user_roles[user_id] = key
                return True
        return False
    
    async def handle_message(self, event: Event) -> None:
        """Handle incoming messages and check for commands."""
        message = event.data.get("message")
        if not message:
            return
        
        content = message.content.strip()
        
        # Check if it's a command
        if not content.startswith(self.prefix):
            return
        
        # Parse command
        parts = content[len(self.prefix):].split(maxsplit=1)
        if not parts:
            return
        
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Execute command
        if cmd_name in self._commands:
            try:
                response = await self._commands[cmd_name]["handler"](message, args, event.data)
                if response:
                    await self.publish("message.reply", {
                        "original": message,
                        "content": response
                    })
            except Exception as e:
                print(f"Command {cmd_name} error: {e}")
                await self.publish("message.reply", {
                    "original": message,
                    "content": f"执行命令出错: {e}"
                })
        else:
            await self.publish("message.reply", {
                "original": message,
                "content": f"未知命令: {cmd_name}\n使用 {self.prefix}help 查看可用命令"
            })
    
    # ==================== Built-in Commands ====================
    
    async def cmd_help(self, message, args: str, context: Dict) -> str:
        """Show available commands."""
        lines = ["📖 可用命令:"]
        for name, info in sorted(self._commands.items()):
            desc = info.get("description", "无描述")
            lines.append(f"  {self.prefix}{name} - {desc}")
        return "\n".join(lines)
    
    async def cmd_ping(self, message, args: str, context: Dict) -> str:
        """Ping command."""
        return "🏓 Pong! 我在线哦~"
    
    async def cmd_status(self, message, args: str, context: Dict) -> str:
        """Show bot status."""
        llm_manager = context.get("llm_manager")
        
        providers = []
        if llm_manager:
            providers = llm_manager.available_providers
        
        user_id = f"{message.platform}:{message.author.id}"
        role = self.get_user_role(user_id)
        
        lines = [
            "📊 机器人状态",
            f"├ 平台: {message.platform}",
            f"├ LLM提供商: {', '.join(providers) if providers else '无'}",
            f"├ 当前角色: {role['name']}",
            f"└ 状态: ✅ 运行中"
        ]
        return "\n".join(lines)
    
    async def cmd_memory(self, message, args: str, context: Dict) -> str:
        """Show memory stats."""
        # Try to get memory manager from chat plugin
        user_id = f"{message.platform}:{message.author.id}"
        
        lines = [
            "🧠 记忆状态",
            f"├ 用户ID: {user_id[:20]}...",
            "├ 短期记忆: 已启用",
            "├ 长期记忆: SQLite",
            "└ RAG记忆: Chroma"
        ]
        
        return "\n".join(lines)
    
    async def cmd_clear(self, message, args: str, context: Dict) -> str:
        """Clear conversation memory."""
        user_id = f"{message.platform}:{message.author.id}"
        
        # Note: Actual clearing would require access to MemoryManager
        # This is a placeholder that could be connected via events
        await self.publish("memory.clear", {"user_id": user_id})
        
        return "🗑️ 已请求清除对话记忆"
    
    async def cmd_role(self, message, args: str, context: Dict) -> str:
        """Switch character role."""
        user_id = f"{message.platform}:{message.author.id}"
        
        if not args.strip():
            role = self.get_user_role(user_id)
            return f"当前角色: {role['name']}\n使用 /role <角色名> 切换角色\n使用 /roles 查看可用角色"
        
        role_name = args.strip()
        
        if self.set_user_role(user_id, role_name):
            role = self.get_user_role(user_id)
            # Publish event to update chat plugin system prompt
            await self.publish("role.changed", {
                "user_id": user_id,
                "role_name": role["name"],
                "system_prompt": role["prompt"]
            })
            return f"✨ 已切换到角色: {role['name']}"
        else:
            available = ", ".join(PRESET_ROLES.keys())
            return f"❌ 未找到角色: {role_name}\n可用角色: {available}"
    
    async def cmd_roles(self, message, args: str, context: Dict) -> str:
        """List available roles."""
        lines = ["🎭 可用角色:"]
        for name in self._available_roles.keys():
            lines.append(f"  • {name}")
        lines.append(f"\n使用 {self.prefix}role <角色名> 切换")
        return "\n".join(lines)

    async def cmd_reload_roles(self, message, args: str, context: Dict) -> str:
        """Reload roles from disk."""
        self._load_roles_from_disk()
        count = len(self._available_roles)
        return f"♻️ 已重载角色配置，当前可用角色数: {count}"
