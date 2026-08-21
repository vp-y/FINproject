from websocket.manager import manager


async def emit_event(
    session_id: str,
    event: dict,
):

    await manager.send_event(
        session_id,
        event
    )
