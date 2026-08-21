from fastapi import WebSocket


class ConnectionManager:
    """Session-scoped, not broadcast — each analysis session gets routed
    only to the WebSocket connection that opened it (see Step 4.14:
    a global broadcast would leak one user's portfolio analysis to
    every other connected client)."""

    def __init__(self):

        self.connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ):

        await websocket.accept()

        self.connections[
            session_id
        ] = websocket

    def disconnect(
        self,
        session_id: str,
    ):

        self.connections.pop(
            session_id,
            None
        )

    async def send_event(
        self,
        session_id: str,
        event: dict,
    ):

        websocket = self.connections.get(
            session_id
        )

        if websocket:

            await websocket.send_json(
                event
            )


manager = ConnectionManager()
