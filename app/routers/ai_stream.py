"""WebSocket endpoint for Gemini Live API streaming proxy."""

import asyncio
import base64
import contextlib
import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from google import genai
from google.genai import types
from jose import JWTError, jwt

from app.config import get_settings
from app.routers.auth import PASSWORD_ALGORITHM, SECRET_KEY
from app.utils.metrics import AI_ERRORS_TOTAL, AI_LATENCY_SECONDS, AI_REQUESTS_TOTAL
from app.utils.user import get_user_by_username

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class GeminiLiveProxy:
    """Manages a proxied connection between client and Gemini Live API."""

    def __init__(self, websocket: WebSocket, user_id: str, username: str):
        self.websocket = websocket
        self.user_id = user_id
        self.username = username
        self.gemini_session: Any = None
        self.todos: list[dict] = []
        self._running = False
        self._session_start_time: float = 0.0  # Track session duration for latency metric

    async def authenticate_token(self, token: str) -> bool:
        """Validate JWT token and return True if valid."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
            username = payload.get("sub")
            if not username:
                return False
            # Access MongoDB client from websocket app state
            client = self.websocket.app.mongodb_client
            user = get_user_by_username(username, client)
            if not user:
                return False
            self.username = username
            self.user_id = str(user.id)
            return True
        except JWTError:
            return False

    async def start(self) -> None:
        """Start the proxy session."""
        if not settings.gemini_api_key:
            await self.websocket.send_json(
                {
                    "type": "error",
                    "message": "AI service not configured",
                }
            )
            await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            # Initialize Google GenAI client
            client = genai.Client(api_key=settings.gemini_api_key)

            # Tool definitions for todo operations
            tool_definitions = [
                types.FunctionDeclaration(
                    name="get_todos",
                    description="Get the current list of todo items.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={},
                    ),
                ),
                types.FunctionDeclaration(
                    name="create_todo",
                    description="Create a new todo item.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "title": types.Schema(
                                type=types.Type.STRING,
                                description="The title of the task",
                            ),
                            "description": types.Schema(
                                type=types.Type.STRING,
                                description="The description of the task",
                            ),
                            "priority": types.Schema(
                                type=types.Type.STRING,
                                description="Priority: low, medium, or high",
                            ),
                            "due_date": types.Schema(
                                type=types.Type.STRING,
                                description="ISO 8601 date string for the due date",
                            ),
                        },
                        required=["title"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="delete_todo",
                    description="Delete a todo item by matching its title.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "search_title": types.Schema(
                                type=types.Type.STRING,
                                description="Text to search for in the todo title",
                            ),
                        },
                        required=["search_title"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="update_todo",
                    description="Update an existing todo item found by title.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "search_title": types.Schema(
                                type=types.Type.STRING,
                                description="Text to search for to identify the task",
                            ),
                            "new_title": types.Schema(
                                type=types.Type.STRING,
                                description="The new title",
                            ),
                            "new_description": types.Schema(
                                type=types.Type.STRING,
                                description="The new description",
                            ),
                            "new_priority": types.Schema(
                                type=types.Type.STRING,
                                description="Priority: low, medium, or high",
                            ),
                            "new_due_date": types.Schema(
                                type=types.Type.STRING,
                                description="ISO 8601 date string",
                            ),
                        },
                        required=["search_title"],
                    ),
                ),
            ]

            # Connect to Gemini Live API
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                tools=[types.Tool(function_declarations=tool_definitions)],
                system_instruction="You are a helpful voice assistant managing a todo list. You can add, delete, update, and list tasks. Identify tasks by fuzzy name matching. Be concise.",
            )

            logger.info(
                f"Connecting to Gemini Live API with model: {settings.gemini_voice_model_id} for user {self.username}"
            )
            async with client.aio.live.connect(
                model=settings.gemini_voice_model_id,
                config=config,
            ) as session:
                self.gemini_session = session
                self._running = True
                self._session_start_time = time.time()  # Start tracking session duration

                # Notify client that connection is established
                await self.websocket.send_json({"type": "connected"})
                AI_REQUESTS_TOTAL.labels(status="success").inc()

                # Start bidirectional streaming
                await asyncio.gather(
                    self._forward_client_to_gemini(),
                    self._forward_gemini_to_client(),
                )

        except Exception as e:
            logger.exception("Failed to connect to Gemini Live API")
            AI_REQUESTS_TOTAL.labels(status="error").inc()
            AI_ERRORS_TOTAL.labels(error_type="connection_error").inc()
            await self.websocket.send_json(
                {
                    "type": "error",
                    "message": f"Failed to connect to AI service: {str(e)}",
                }
            )
            await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)

    async def _forward_client_to_gemini(self) -> None:
        """Forward audio from client WebSocket to Gemini."""
        chunks_count = 0
        try:
            while self._running:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.receive_json(),
                        timeout=30.0,
                    )
                except asyncio.TimeoutError:
                    continue

                msg_type = message.get("type")

                if msg_type == "audio":
                    # Forward audio data to Gemini
                    audio_data = message.get("data")
                    if audio_data and self.gemini_session:
                        chunks_count += 1
                        if chunks_count % 50 == 0:
                            logger.info(f"Forwarded {chunks_count} audio chunks to Gemini")

                        await self.gemini_session.send(
                            input={"mime_type": "audio/pcm", "data": audio_data},
                            end_of_turn=False,
                        )

                elif msg_type == "end_turn":
                    # Signal end of user turn
                    logger.info("Received end_turn signal from client -> sending to Gemini")
                    if self.gemini_session:
                        await self.gemini_session.send(input=None, end_of_turn=True)

                elif msg_type == "todos_update":
                    # Update local todos cache
                    new_todos = message.get("todos", [])
                    logger.info(f"Received todos_update: {len(new_todos)} items")
                    self.todos = new_todos

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected in client->gemini loop for {self.username}")
            self._running = False
        except Exception as e:
            logger.exception(f"Error forwarding client to Gemini: {e}")
            self._running = False

    async def _forward_gemini_to_client(self) -> None:
        """Forward responses from Gemini to client WebSocket."""
        try:
            while self._running and self.gemini_session:
                async for response in self.gemini_session.receive():
                    if not self._running:
                        break

                    # Handle server content (audio, text, etc.)
                    if response.server_content:
                        sc = response.server_content

                        # Handle interruption
                        if sc.interrupted:
                            logger.info("Gemini signaled INTERRUPTION")
                            await self.websocket.send_json({"type": "interrupted"})
                            continue

                        # Handle model turn with audio
                        if sc.model_turn and sc.model_turn.parts:
                            for part in sc.model_turn.parts:
                                if part.inline_data:
                                    # logger.debug("Received audio chunk from Gemini") # optimized out to reduce noise
                                    await self.websocket.send_json(
                                        {
                                            "type": "audio",
                                            "data": base64.b64encode(part.inline_data.data).decode(
                                                "utf-8"
                                            ),
                                            "mime_type": part.inline_data.mime_type,
                                        }
                                    )

                        # Handle turn complete
                        if sc.turn_complete:
                            logger.info("Gemini signaled Turn Complete")
                            await self.websocket.send_json({"type": "turn_complete"})

                    # Handle tool calls
                    if response.tool_call:
                        for fc in response.tool_call.function_calls:
                            logger.info(
                                f"Gemini requested tool call: {fc.name} with args: {fc.args}"
                            )
                            result = await self._handle_tool_call(fc)
                            logger.info(f"Executed tool {fc.name}, result: {result}")

                            # Send result back to Gemini
                            await self.gemini_session.send(
                                input=types.LiveClientToolResponse(
                                    function_responses=[
                                        types.FunctionResponse(
                                            id=fc.id,
                                            name=fc.name,
                                            response={"result": result},
                                        )
                                    ]
                                ),
                                end_of_turn=False,
                            )
                            # Also notify client
                            await self.websocket.send_json(
                                {
                                    "type": "tool_result",
                                    "name": fc.name,
                                    "result": result,
                                }
                            )

        except WebSocketDisconnect:
            self._running = False
        except Exception as e:
            logger.exception(f"Error forwarding Gemini to client: {e}")
            self._running = False

    async def _handle_tool_call(self, fc: Any) -> dict:
        """Handle a tool call from Gemini."""
        args = fc.args if hasattr(fc, "args") else {}
        result: dict = {"error": "Unknown tool"}

        try:
            if fc.name == "get_todos":
                result = {
                    "todos": [
                        {
                            "title": t.get("title"),
                            "priority": t.get("priority"),
                            "due_date": t.get("due_date"),
                            "description": t.get("description"),
                        }
                        for t in self.todos
                    ]
                }

            elif fc.name == "create_todo":
                # Notify frontend to create todo
                await self.websocket.send_json(
                    {
                        "type": "action",
                        "action": "create_todo",
                        "data": {
                            "title": args.get("title"),
                            "description": args.get("description", ""),
                            "priority": args.get("priority", "medium"),
                            "due_date": args.get("due_date"),
                        },
                    }
                )
                result = {"status": "success", "message": f"Created task \"{args.get('title')}\""}

            elif fc.name == "delete_todo":
                query = (args.get("search_title") or "").lower()
                matches = [t for t in self.todos if query in t.get("title", "").lower()]

                if not matches:
                    result = {"status": "error", "message": "No task found matching that name."}
                elif len(matches) > 1:
                    titles = ", ".join(t.get("title", "") for t in matches)
                    result = {
                        "status": "error",
                        "message": f"Multiple tasks found: {titles}. Please be more specific.",
                    }
                else:
                    await self.websocket.send_json(
                        {
                            "type": "action",
                            "action": "delete_todo",
                            "data": {"id": matches[0].get("id")},
                        }
                    )
                    result = {
                        "status": "success",
                        "message": f"Deleted task \"{matches[0].get('title')}\"",
                    }

            elif fc.name == "update_todo":
                query = (args.get("search_title") or "").lower()
                matches = [t for t in self.todos if query in t.get("title", "").lower()]

                if not matches:
                    result = {"status": "error", "message": "No task found matching that name."}
                elif len(matches) > 1:
                    titles = ", ".join(t.get("title", "") for t in matches)
                    result = {"status": "error", "message": f"Multiple tasks found: {titles}."}
                else:
                    todo = matches[0]
                    await self.websocket.send_json(
                        {
                            "type": "action",
                            "action": "update_todo",
                            "data": {
                                "id": todo.get("id"),
                                "title": args.get("new_title") or todo.get("title"),
                                "description": args.get("new_description")
                                or todo.get("description"),
                                "priority": args.get("new_priority") or todo.get("priority"),
                                "due_date": args.get("new_due_date") or todo.get("due_date"),
                            },
                        }
                    )
                    result = {
                        "status": "success",
                        "message": f"Updated task \"{todo.get('title')}\"",
                    }

        except Exception as e:
            result = {"status": "error", "message": str(e)}

        return result

    async def stop(self) -> None:
        """Stop the proxy session."""
        self._running = False

        # Record session latency if session was active
        if self._session_start_time > 0:
            duration = time.time() - self._session_start_time
            AI_LATENCY_SECONDS.observe(duration)
            logger.info(f"AI session duration: {duration:.2f}s")

        # TODO: Track AI token usage - Gemini Live API doesn't expose token counts
        # in real-time streaming mode. Consider using Gemini API's usage metadata
        # from non-streaming endpoints or estimate based on audio duration.

        if self.gemini_session:
            with contextlib.suppress(Exception):
                await self.gemini_session.close()


@router.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time voice streaming with Gemini Live API.

    Authentication is done via the first message which should contain a JWT token:
    {"type": "auth", "token": "<JWT token>"}

    After authentication, send audio data:
    {"type": "audio", "data": "<base64 PCM audio>"}
    """
    await websocket.accept()

    # Wait for auth message
    try:
        auth_msg = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "Authentication timeout"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
        await websocket.send_json({"type": "error", "message": "First message must be auth"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Create proxy and authenticate
    proxy = GeminiLiveProxy(websocket, "", "")
    if not await proxy.authenticate_token(auth_msg["token"]):
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.info(f"WebSocket voice stream authenticated for user {proxy.username}")

    try:
        await proxy.start()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {proxy.username}")
    finally:
        await proxy.stop()
