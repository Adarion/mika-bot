"""
QQ IM Adapter - Adapter for QQ Bot using qq-botpy SDK.
Supports group chat and private (C2C) messages.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import botpy
from botpy import logging
from botpy.message import GroupMessage, C2CMessage

from .base import BaseIMAdapter, Channel, IncomingMessage, OutgoingMessage, User

# Enable debug logging
_log = logging.get_logger()


class QQBotClient(botpy.Client):
    """Internal QQ bot client."""
    
    def __init__(self, adapter: "QQAdapter", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adapter = adapter
    
    async def on_ready(self):
        _log.info(f"QQ Bot connected as {self.robot.name}")
        self.adapter._connected = True
    
    async def on_group_at_message_create(self, message: GroupMessage):
        """Handle @mention messages in QQ group chats."""
        _log.info(f"[Group] Received message from {message.author.member_openid}: {message.content}")
        await self._handle_group_message(message)
    
    async def on_c2c_message_create(self, message: C2CMessage):
        """Handle private/direct messages."""
        _log.info(f"[C2C] Received message from {message.author.user_openid}: {message.content}")
        await self._handle_c2c_message(message)
    
    async def _handle_group_message(self, message: GroupMessage):
        """Convert QQ group message to IncomingMessage and dispatch."""
        try:
            # Build user
            author = User(
                id=message.author.member_openid,
                name=message.author.member_openid[:8],  # No username available
                raw={"member_openid": message.author.member_openid}
            )
            
            # Build channel
            channel = Channel(
                id=message.group_openid,
                name="QQ Group",
                type="group",
                raw={"group_openid": message.group_openid}
            )
            
            # Build incoming message
            incoming = IncomingMessage(
                id=message.id,
                content=message.content.strip() if message.content else "",
                author=author,
                channel=channel,
                timestamp=datetime.now(),
                mentions_bot=True,
                platform="qq",
                raw={"message": message, "type": "group"}
            )
            
            # Dispatch to adapter's callback
            await self.adapter.on_message(incoming)
            
        except Exception as e:
            _log.error(f"Error handling group message: {e}")
    
    async def _handle_c2c_message(self, message: C2CMessage):
        """Convert QQ C2C message to IncomingMessage and dispatch."""
        try:
            # Build user
            author = User(
                id=message.author.user_openid,
                name=message.author.user_openid[:8],
                raw={"user_openid": message.author.user_openid}
            )
            
            # Build channel (use user_openid as channel for C2C)
            channel = Channel(
                id=message.author.user_openid,
                name="Private Chat",
                type="private",
                raw={"user_openid": message.author.user_openid}
            )
            
            # Build incoming message
            incoming = IncomingMessage(
                id=message.id,
                content=message.content.strip() if message.content else "",
                author=author,
                channel=channel,
                timestamp=datetime.now(),
                mentions_bot=True,
                platform="qq",
                raw={"message": message, "type": "c2c"}
            )
            
            # Dispatch to adapter's callback
            await self.adapter.on_message(incoming)
            
        except Exception as e:
            _log.error(f"Error handling C2C message: {e}")


class QQAdapter(BaseIMAdapter):
    """
    QQ IM Adapter using qq-botpy.
    Supports group chat and private (C2C) messages.
    
    Config:
        app_id: QQ Bot App ID.
        secret: QQ Bot Secret.
    """
    
    def __init__(self, config: Dict[str, Any], on_message: Callable[[IncomingMessage], Any]):
        super().__init__(config, on_message)
        self.platform_name = "qq"
        self._client: Optional[QQBotClient] = None
        self._connected = False
        self._task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """Connect to QQ using qq-botpy."""
        # Intents for group and C2C messages
        intents = botpy.Intents(
            public_messages=True,  # For group messages
            direct_message=True    # For C2C messages
        )
        
        self._client = QQBotClient(adapter=self, intents=intents)
        
        app_id = self.config.get("app_id")
        secret = self.config.get("secret")
        
        if not app_id or not secret:
            raise ValueError("QQ adapter requires app_id and secret in config")
        
        # Start the bot in a background task
        self._task = asyncio.create_task(
            self._client.start(appid=app_id, secret=secret)
        )
        
        # Wait for connection
        await asyncio.sleep(3)
    
    async def disconnect(self) -> None:
        """Disconnect from QQ."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._connected = False
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send a message to a channel."""
        # Not implemented for direct sending
        return False
    
    async def reply(self, original: IncomingMessage, content: str, **kwargs) -> bool:
        """Reply to a message."""
        if not self._client or "message" not in original.raw:
            return False
        
        try:
            msg_type = original.raw.get("type")
            message = original.raw["message"]
            msg_seq = kwargs.get("msg_seq", 1)  # Default to 1 if not provided
            
            if msg_type == "group":
                # Reply to group message
                await message._api.post_group_message(
                    group_openid=original.channel.id,
                    msg_type=0,  # Text
                    msg_id=message.id,
                    content=content,
                    msg_seq=msg_seq
                )
            elif msg_type == "c2c":
                # Reply to C2C message
                await message._api.post_c2c_message(
                    openid=original.author.id,
                    msg_type=0,  # Text
                    msg_id=message.id,
                    content=content,
                    msg_seq=msg_seq
                )
            
            _log.info(f"Replied to {msg_type}: {content[:50]}...")
            return True
            
        except Exception as e:
            _log.error(f"Failed to reply: {e}")
            return False

    
    @property
    def is_connected(self) -> bool:
        return self._connected
