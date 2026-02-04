"""
Admin Server - REST API backend for Mika-Bot WebUI.
"""

import asyncio
import hashlib
import json
import secrets
import os
import psutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from aiohttp import web

# Session store (in-memory)
_sessions: Dict[str, dict] = {}

def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_session(request: web.Request) -> bool:
    """Check if request has valid session."""
    session_id = request.cookies.get("session")
    if session_id and session_id in _sessions:
        return True
    return False

class AdminServer:
    """
    REST API Admin Server.
    Serves JSON API for the React frontend and static assets.
    """
    
    def __init__(self, config: Dict[str, Any], app_context: Dict[str, Any] = None):
        self.config = config
        self.port = config.get("port", 8080)
        self.password_hash = None
        if config.get("password"):
            self.password_hash = hash_password(config.get("password"))
        self.app_context = app_context or {}
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._password_file = Path("admin_password.hash")
        self._load_password()
        
        # Determine static files location (frontend build)
        self.static_dir = Path(__file__).parent / "dist"
    
    def _load_password(self):
        """Load password from file if exists."""
        if self._password_file.exists():
            self.password_hash = self._password_file.read_text().strip()
    
    def _save_password(self, password_hash: str):
        """Save password hash to file."""
        self._password_file.write_text(password_hash)
        self.password_hash = password_hash
    
    def _needs_setup(self) -> bool:
        """Check if first-time setup is needed."""
        return self.password_hash is None

    async def start(self) -> None:
        """Start the admin server."""
        self._app = web.Application()
        self._setup_routes()
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await self._site.start()
        
        print(f"Admin API running at http://0.0.0.0:{self.port}")

    async def stop(self) -> None:
        """Stop the admin server."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()

    def _setup_routes(self) -> None:
        """Setup API and Static routes."""
        r = self._app.router
        
        # === Auth API ===
        r.add_post("/api/login", self._api_login)
        r.add_post("/api/logout", self._api_logout)
        r.add_get("/api/check-auth", self._api_check_auth)
        r.add_post("/api/setup", self._api_setup)
        
        # === System API ===
        r.add_get("/api/status", self._api_status)
        r.add_get("/api/system", self._api_system_stats)
        
        # === Config API ===
        r.add_get("/api/config", self._api_get_config)
        r.add_post("/api/config", self._api_save_config)
        
        # === WebSocket ===
        r.add_get("/ws", self._handle_websocket)
        
        # === Static Files (Frontend) ===
        # If dist folder exists, serve it
        if self.static_dir.exists():
            r.add_static("/assets", self.static_dir / "assets")
            # Serve index.html for all other routes (SPA)
            r.add_get("/{path:.*}", self._serve_index)
        else:
            r.add_get("/", self._serve_placeholder)

    # ==================== Handlers ====================

    async def _serve_index(self, request: web.Request) -> web.StreamResponse:
        """Serve index.html for SPA."""
        return web.FileResponse(self.static_dir / "index.html")

    async def _serve_placeholder(self, request: web.Request) -> web.Response:
        """Placeholder when frontend is not built."""
        return web.Response(text="Mika-Bot API Server. Frontend not built.", content_type="text/plain")

    async def _check_auth_middleware(self, request: web.Request):
        """Helper to verify auth for API calls."""
        if self._needs_setup():
            raise web.HTTPUnauthorized(reason="Setup required")
        if not verify_session(request):
            raise web.HTTPUnauthorized(reason="Invalid session")

    # ==================== API Implementation ====================

    async def _api_login(self, request: web.Request) -> web.Response:
        if self._needs_setup():
            return web.json_response({"error": "Setup required", "setup_needed": True}, status=403)
        
        try:
            data = await request.json()
            password = data.get("password", "")
        except:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        if hash_password(password) == self.password_hash:
            session_id = secrets.token_hex(32)
            _sessions[session_id] = {"created": datetime.now()}
            response = web.json_response({"success": True})
            response.set_cookie("session", session_id, httponly=True, max_age=86400, samesite="Strict")
            return response
        
        return web.json_response({"error": "Invalid password"}, status=401)

    async def _api_logout(self, request: web.Request) -> web.Response:
        session_id = request.cookies.get("session")
        if session_id and session_id in _sessions:
            del _sessions[session_id]
        response = web.json_response({"success": True})
        response.del_cookie("session")
        return response

    async def _api_check_auth(self, request: web.Request) -> web.Response:
        """Check if user is authenticated and if setup is needed."""
        if self._needs_setup():
            return web.json_response({"authenticated": False, "setup_needed": True})
        return web.json_response({"authenticated": verify_session(request), "setup_needed": False})

    async def _api_setup(self, request: web.Request) -> web.Response:
        if not self._needs_setup():
            return web.json_response({"error": "Already setup"}, status=403)
        
        try:
            data = await request.json()
            password = data.get("password", "")
        except:
             return web.json_response({"error": "Invalid JSON"}, status=400)

        if len(password) < 4:
            return web.json_response({"error": "Password too short"}, status=400)
            
        self._save_password(hash_password(password))
        
        # Auto login
        session_id = secrets.token_hex(32)
        _sessions[session_id] = {"created": datetime.now()}
        response = web.json_response({"success": True})
        response.set_cookie("session", session_id, httponly=True, max_age=86400, samesite="Strict")
        return response

    async def _api_status(self, request: web.Request) -> web.Response:
        await self._check_auth_middleware(request)
        return web.json_response({
            "status": "online",
            "llm_providers": self.app_context.get("llm_providers", []),
            "im_platforms": self.app_context.get("im_platforms", []),
            "plugins": self.app_context.get("plugins", [])
        })

    async def _api_system_stats(self, request: web.Request) -> web.Response:
        await self._check_auth_middleware(request)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking
        load_avg = list(os.getloadavg())
        
        # Memory
        mem = psutil.virtual_memory()
        memory = {
            "total": mem.total / (1024 * 1024),
            "used": mem.used / (1024 * 1024),
            "free": mem.available / (1024 * 1024),
            "percent": mem.percent
        }
        
        # Swap
        swap = psutil.swap_memory()
        swap_info = {
            "total": swap.total / (1024 * 1024),
            "used": swap.used / (1024 * 1024),
            "free": swap.free / (1024 * 1024),
            "percent": swap.percent
        }
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total / (1024 * 1024 * 1024),
            "used": disk.used / (1024 * 1024 * 1024),
            "free": disk.free / (1024 * 1024 * 1024),
            "percent": disk.percent
        }
        
        return web.json_response({
            "cpu_percent": cpu_percent,
            "load_avg": load_avg,
            "memory": memory,
            "swap": swap_info,
            "disk": disk_info
        })

    async def _api_get_config(self, request: web.Request) -> web.Response:
        await self._check_auth_middleware(request)
        
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            # Filter out sensitive fields if needed, but for admin it's usually fine
            return web.json_response(config)
        return web.json_response({})

    async def _api_save_config(self, request: web.Request) -> web.Response:
        await self._check_auth_middleware(request)
        
        try:
            data = await request.json()
            config_path = Path("config.yaml")
            
            # Simple validation or merging logic could go here
            # For now, we trust the admin input logic (frontend will handle structure)
            
            with open(config_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    # ==================== WebSocket ====================

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        if not verify_session(request):
            return web.Response(status=401)
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data.get("type") == "message":
                        content = data.get("content", "")
                        
                        llm_manager = self.app_context.get("llm_manager")
                        if llm_manager:
                            try:
                                response = await llm_manager.chat(content)
                                await ws.send_json({"type": "message", "content": response, "sender": "bot"})
                            except Exception as e:
                                await ws.send_json({"type": "message", "content": f"Error: {e}", "sender": "bot"})
                        else:
                            await ws.send_json({"type": "message", "content": "LLM not configured", "sender": "bot"})
                except json.JSONDecodeError:
                    continue
        return ws
