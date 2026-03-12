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
        self.target_event = None # Stores the last event to reply to
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load config from self.config (AstrBot managed)
        self.mc_host = self.config.get("mc_host", "127.0.0.1")
        self.mc_port = self.config.get("mc_port", 25565)
        self.mindserver_url = f"http://{self.config.get('mindserver_host', '127.0.0.1')}:{self.config.get('mindserver_port', 8076)}"
        self.agent_name = self.config.get("agent_name", "MindBot")
        
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

    # Removed _load_config and _save_config as we use AstrBot's config system now

    async def _get_llm_config(self):
        """Construct LLM config from plugin configuration"""
        # 1. Base Config
        config = {
            "env": os.environ.copy(),
            "model": self.config.get("llm_model", "gpt-4"),
            "provider_type": self.config.get("llm_api", "openai"),
            "api_url": self.config.get("llm_url", "")
        }
        
        # 2. API Key Injection
        api_key = self.config.get("llm_api_key", "")
        if api_key:
            # Inject into common env vars to cover most SDKs
            config["env"]["OPENAI_API_KEY"] = api_key
            config["env"]["DOUBAO_API_KEY"] = api_key
            config["env"]["DEEPSEEK_API_KEY"] = api_key
            config["env"]["ANTHROPIC_API_KEY"] = api_key
            config["env"]["GOOGLE_API_KEY"] = api_key
            config["env"]["GROK_API_KEY"] = api_key
            # Also generic ones if needed by specific providers
            config["env"]["API_KEY"] = api_key
            logger.info(f"Using configured API Key for {config['provider_type']}")
        else:
            logger.warning("No API Key configured in plugin settings. Attempting to use system environment or fallback.")
            
        return config

    @filter.command("mcserver")
    async def mcserver(self, event: AstrMessageEvent, address: str = ""):
        """Set Minecraft Server Address (host:port)"""
        if not address:
            yield event.plain_result(f"Current Server: {self.mc_host}:{self.mc_port}\nUsage: /mcserver host:port (e.g. 127.0.0.1:25565)")
            return
            
        parts = address.split(":")
        self.mc_host = parts[0]
        if len(parts) > 1:
            try:
                self.mc_port = int(parts[1])
            except ValueError:
                yield event.plain_result("❌ Invalid port number.")
                return
        else:
            self.mc_port = 25565 # default
            
        # Update config in memory (Persistent saving depends on AstrBot implementation)
        # Typically users should use WebUI to configure persistent settings
        self.config["mc_host"] = self.mc_host
        self.config["mc_port"] = self.mc_port
        
        yield event.plain_result(f"✅ Minecraft Server set to: {self.mc_host}:{self.mc_port}\n(Note: Please update config in WebUI for persistence)")

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

        mindserver_port = str(self.config.get('mindserver_port', 8076))
        try:
            # Use asyncio subprocess for non-blocking IO
            self.process = await asyncio.create_subprocess_exec(
                'node', script_path, '--mindserver_port', mindserver_port,
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
                
                settings = {
                    "profile": profile_data,
                    "host": self.mc_host,
                    "port": self.mc_port,
                    "auth": "offline"
                }
                
                def on_create_callback(response):
                    logger.info(f"Agent creation response: {response}")

                await self.sio.emit('create-agent', settings, callback=on_create_callback)
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
            logger.info(f"{prefix} {line.decode().strip()}")

    @filter.command("mcstop")
    async def mcstop(self, event: AstrMessageEvent):
        """Stop the Mindcraft server"""
        if self.sio.connected:
            await self.sio.disconnect()
        
        if self.process:
            try:
                # On Windows, terminate() might not kill the entire process tree (node + children)
                # We can try to use taskkill to be sure, or just terminate.
                self.process.terminate()
                # Wait with timeout to avoid hanging
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Process did not exit in time, forcing kill.")
                    self.process.kill()
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

