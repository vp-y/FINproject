from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from websocket.manager import manager


router = APIRouter()


@router.websocket("/ws/agents/{session_id}")
async def agent_websocket(
    websocket: WebSocket,
    session_id: str,
):

    await manager.connect(
        session_id,
        websocket
    )

    try:

        while True:

            data = await websocket.receive_text()

            print(
                "WebSocket received:",
                session_id,
                data
            )

    except WebSocketDisconnect:

        manager.disconnect(
            session_id
        )
