from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import socketio
import asyncio
import os
import sys
import json
import signal

@register("mindcraft_controller", "Hanshu", "Mindcraft Controller", "1.0.0")
class MindcraftPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.sio = socketio.AsyncClient()
        self.process = None
        self.connected = False
        self.mindserver_url = "http://localhost:8080"
        self.target_event = None # Stores the last event to reply to
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.agent_name = "doubao"
        
        # Socket.IO Event Handlers
        @self.sio.on('connect')
        async def on_connect():
            logger.info("Connected to MindServer")
            self.connected = True

        @self.sio.on('disconnect')
        async def on_disconnect():
            logger.info("Disconnected from MindServer")
            self.connected = False

        @self.sio.on('bot-output')
        async def on_bot_output(agent_name, message):
            logger.info(f"Bot output from {agent_name}: {message}")
            if self.target_event:
                # Send the bot's message back to the user
                # We use the stored event to send a message to the same conversation
                # Since we can't yield here (it's a callback), we use the event's context or platform API if available.
                # In AstrBot, we might not be able to directly 'yield' from a callback.
                # We usually need to use the context to send a message.
                # Assuming AstrMessageEvent has a way to send, or we use the provider.
                # For simplicity in this template, we'll try to use the provider from the context if possible,
                # or just log if we can't easily send async.
                # However, typically plugins are reactive. 
                # Let's try to use the event object to send a message if it supports it, 
                # or use the context's messaging capabilities.
                
                # Note: AstrBot's API for proactive messaging might vary. 
                # We will try to use the session/conversation ID from the target_event.
                try:
                    # This is a best-effort guess at the API based on common bot framework patterns
                    # If AstrBot supports sending via context:
                    # await self.context.send_message(self.target_event.unified_msg_origin, f"[{agent_name}] {message}")
                    pass 
                    # Since I don't have the full AstrBot send API in the prompt, I will implement a placeholder
                    # that logs it. The user can adapt the send logic.
                    logger.info(f"Should send to user: [{agent_name}] {message}")
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")

    async def _get_llm_config(self):
        """Extract LLM config from AstrBot's loaded provider"""
        config = {
            "env": os.environ.copy(),
            "model": "gpt-4", # default fallback
            "provider_type": "openai", # default
            "api_url": None
        }
        
        # Try to get the provider
        provider = None
        provider_id = self.config.get("llm_provider_id")
        if provider_id:
            provider = self.context.get_provider_by_id(provider_id)
        
        if not provider and hasattr(self.context, "get_all_providers"):
            providers = self.context.get_all_providers()
            if providers:
                provider = providers[0]
        
        if provider:
            logger.info(f"Using LLM Provider: {type(provider).__name__}")
            cfg = getattr(provider, "config", {})
            
            # 1. API Key
            api_key = cfg.get("api_key") or cfg.get("access_key") or cfg.get("token")
            if api_key:
                logger.info("Successfully extracted API Key.")
                config["env"]["DOUBAO_API_KEY"] = api_key
                config["env"]["OPENAI_API_KEY"] = api_key
                config["env"]["DEEPSEEK_API_KEY"] = api_key
            
            # 2. Base URL
            api_url = cfg.get("api_url") or cfg.get("base_url") or cfg.get("endpoint")
            if api_url:
                config["api_url"] = api_url
            
            # 3. Model Name
            model_name = cfg.get("model")
            if model_name:
                config["model"] = model_name
                
            # 4. Provider Type Mapping
            p_name = type(provider).__name__.lower()
            if "doubao" in p_name:
                config["provider_type"] = "doubao"
            elif "deepseek" in p_name:
                config["provider_type"] = "deepseek"
            elif "openai" in p_name:
                config["provider_type"] = "openai"
            elif "ollama" in p_name:
                config["provider_type"] = "ollama"
                
        return config

    @filter.command("mcinstall")
    async def mcinstall(self, event: AstrMessageEvent):
        """Install dependencies (npm install)"""
        yield event.plain_result("📦 Checking and installing dependencies...")
        
        node_modules_path = os.path.join(self.root_dir, 'node_modules')
        if os.path.exists(node_modules_path):
            yield event.plain_result("✅ node_modules already exists. Skipping install.")
            return

        try:
            # Use shell=True for Windows to find npm
            process = await asyncio.create_subprocess_shell(
                'npm install',
                cwd=self.root_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                yield event.plain_result("✅ npm install completed successfully.")
            else:
                yield event.plain_result(f"❌ npm install failed:\n{stderr.decode()}")
        except Exception as e:
            yield event.plain_result(f"❌ Error running npm install: {e}")

    @filter.command("mcstart")
    async def mcstart(self, event: AstrMessageEvent):
        """Start the Mindcraft server and Agent"""
        if self.process:
            yield event.plain_result("⚠️ Mindcraft is already running.")
            return

        self.target_event = event # Update target for replies
        yield event.plain_result("🚀 Starting Mindcraft Server...")

        # 1. Prepare Environment & Config
        llm_config = await self._get_llm_config()
        
        # 2. Start Node.js Process
        script_path = os.path.join(self.root_dir, 'src', 'mindcraft-py', 'init-mindcraft.js')
        if not os.path.exists(script_path):
             yield event.plain_result(f"❌ Could not find script at {script_path}")
             return

        try:
            # Use asyncio subprocess for non-blocking IO
            self.process = await asyncio.create_subprocess_exec(
                'node', script_path, '--mindserver_port', '8080',
                cwd=self.root_dir,
                env=llm_config["env"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Start a task to log stdout (optional, prevents buffer filling)
            asyncio.create_task(self._log_stream(self.process.stdout, "[Node]"))
            asyncio.create_task(self._log_stream(self.process.stderr, "[Node Error]"))

            yield event.plain_result("✅ Node.js process started. Connecting to MindServer...")
            
            # 3. Connect Socket.IO
            await asyncio.sleep(3) # Wait for server to boot
            try:
                await self.sio.connect(self.mindserver_url)
                yield event.plain_result("✅ Connected to MindServer.")
                
                # 4. Create Agent with Dynamic Profile
                # Instead of loading from file, we construct it from Python config
                profile_data = {
                    "name": self.agent_name,
                    "model": {
                        "api": llm_config["provider_type"],
                        "model": llm_config["model"]
                    }
                }
                
                # Inject custom URL if present (critical for Doubao/Local LLMs)
                if llm_config["api_url"]:
                    profile_data["model"]["url"] = llm_config["api_url"]
                
                logger.info(f"Creating agent with config: {profile_data}")
                
                settings = {"profile": profile_data}
                await self.sio.emit('create-agent', settings)
                yield event.plain_result(f"🤖 Agent '{self.agent_name}' creation requested using {llm_config['provider_type']} model.")

            except Exception as e:
                yield event.plain_result(f"❌ Failed to connect to MindServer: {e}")
                # Cleanup if connection fails?
                # await self.mcstop(event)

        except Exception as e:
            yield event.plain_result(f"❌ Failed to start process: {e}")

    async def _log_stream(self, stream, prefix):
        while True:
            line = await stream.readline()
            if not line:
                break
            # logger.info(f"{prefix} {line.decode().strip()}")

    @filter.command("mcstop")
    async def mcstop(self, event: AstrMessageEvent):
        """Stop the Mindcraft server"""
        if self.sio.connected:
            await self.sio.disconnect()
        
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
                self.process = None
                yield event.plain_result("🛑 Mindcraft server stopped.")
            except Exception as e:
                yield event.plain_result(f"⚠️ Error stopping process: {e}")
        else:
            yield event.plain_result("Mindcraft is not running.")

    @filter.command("mc")
    async def mc_chat(self, event: AstrMessageEvent, message: str = ""):
        """Chat with the bot or send commands"""
        if not self.sio.connected:
            yield event.plain_result("❌ Mindcraft is not connected. Use /mcstart first.")
            return

        if not message:
            yield event.plain_result("Usage: /mc [message]")
            return

        self.target_event = event # Update target to reply to this conversation
        
        # Try to send
        try:
            # The server expects 'send-message' event
            await self.sio.emit('send-message', self.agent_name, {
                "from": event.get_sender_name() or "User",
                "message": message
            })
            
            yield event.plain_result(f"Sent to {self.agent_name}: {message}")
            
        except Exception as e:
            yield event.plain_result(f"❌ Failed to send message: {e}")

