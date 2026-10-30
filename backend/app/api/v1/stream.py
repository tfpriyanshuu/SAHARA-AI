import asyncio
import logging
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional

from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def stream_events(
    request: Request,
    coordinator_id: Optional[int] = Query(None, description="Filter events for specific coordinator")
):
    """
    Server-Sent Events (SSE) live stream endpoint for Care Coordinator Dashboard.
    Emits typed real-time events:
    - checkin_status_changed (ringing, answered, declined, missed, completed)
    - turn_added (per-turn voice transcript, cues, audio)
    - checkin_completed (summary, incremental rescore)
    - urgent_flag (acute symptoms, pinned to top)
    - senior_rescored (dynamic priority update)
    - device_health_changed (battery, permissions, heartbeat)
    """
    queue = await sse_manager.subscribe(coordinator_id=coordinator_id)

    async def event_generator():
        try:
            # Send initial connected banner
            yield f"event: connected\ndata: {{\"status\": \"CONNECTED\", \"coordinator_id\": {coordinator_id or 'null'}}}\n\n"
            
            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break

                try:
                    # Wait up to 15s for next event, else send keepalive comment
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await sse_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

