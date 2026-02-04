"""
Mika-Bot - Extensible QQ Bot with LLM Integration.

Main entry point for the application.
"""

import asyncio
import signal
import sys
from pathlib import Path

from core.config import load_config, get_config
from core.event_bus import get_event_bus, Event
from core.plugin_manager import PluginManager
from adapters.llm.factory import LLMManager
from adapters.im.factory import IMManager
from adapters.im.base import IncomingMessage
from web.admin import AdminServer


async def main():
    """Main application entry point."""
    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("Error: config.yaml not found. Copy config.yaml.example to config.yaml")
        sys.exit(1)
    
    config = load_config(config_path)
    print("Configuration loaded")
    
    # Initialize event bus
    event_bus = get_event_bus()
    
    # Initialize LLM manager
    llm_config = config.get_section("llm")
    llm_manager = LLMManager(llm_config)
    print(f"LLM providers available: {llm_manager.available_providers}")
    
    # Message handler callback
    async def on_message(message: IncomingMessage):
        """Handle incoming messages from any IM platform."""
        print(f"[{message.platform}] {message.author.name}: {message.content}")
        
        # Publish to event bus with context
        await event_bus.publish("message.received", {
            "message": message,
            "llm_manager": llm_manager
        }, source="im_adapter")
    
    # Initialize IM manager
    im_config = config.get("im", [])
    im_manager = IMManager(im_config, on_message)
    
    # Subscribe to reply events
    async def handle_reply(event: Event):
        """Handle outgoing reply events."""
        original = event.data.get("original")
        content = event.data.get("content")
        
        if original and content:
            try:
                adapter = im_manager.get_adapter(original.platform)
                if isinstance(content, list):
                    for i, part in enumerate(content):
                        # msg_seq must start at 1
                        await adapter.reply(original, part, msg_seq=i+1)
                        # Add a small delay between bubbles for natural effect
                        await asyncio.sleep(0.8)
                else:
                    await adapter.reply(original, content)
            except Exception as e:
                print(f"Failed to send reply: {e}")
    
    event_bus.subscribe("message.reply", handle_reply)
    
    # Initialize plugin manager
    plugin_manager = PluginManager(event_bus)
    
    # Load plugins from config
    plugin_names = config.get("plugins", [])
    plugin_configs = config.get("plugin_configs", {})
    await plugin_manager.load_plugins(plugin_names, plugin_configs)
    print(f"Plugins loaded: {plugin_manager.loaded_plugins}")
    
    # Connect to IM platforms
    await im_manager.connect_all()
    print(f"Connected to: {im_manager.connected_platforms}")
    
    # Start admin panel
    admin_config = config.get("admin", {"port": 8080, "password": "admin"})
    admin_server = AdminServer(admin_config, {
        "llm_manager": llm_manager,
        "llm_providers": llm_manager.available_providers,
        "im_platforms": im_manager.connected_platforms,
        "plugins": plugin_manager.loaded_plugins,
        "event_bus": event_bus
    })
    await admin_server.start()
    
    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        print("\nShutting down...")
        shutdown_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    print("Bot is running. Press Ctrl+C to stop.")
    
    # Keep running until shutdown
    await shutdown_event.wait()
    
    # Cleanup
    await admin_server.stop()
    await im_manager.disconnect_all()
    await plugin_manager.unload_all()
    print("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
