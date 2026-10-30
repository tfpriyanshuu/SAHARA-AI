"""Server-Sent Events (SSE) Manager for Live Dashboard Sync.
Emits typed real-time events to connected Care Coordinators:
- checkin_status_changed
- turn_added
- checkin_completed
- urgent_flag
- senior_rescored
- device_health_changed
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        # Maps client_queue -> dict(coordinator_id=..., created_at=...)
        self._subscribers: Dict[asyncio.Queue, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, coordinator_id: Optional[int] = None) -> asyncio.Queue:
        """Subscribe a new SSE client connection with optional coordinator filter."""
        q = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[q] = {
                "coordinator_id": coordinator_id
            }
        logger.info(f"SSE client connected. Active subscribers: {len(self._subscribers)}")
        return q

    async def unsubscribe(self, q: asyncio.Queue):
        """Unsubscribe when client disconnects."""
        async with self._lock:
            if q in self._subscribers:
                del self._subscribers[q]
        logger.info(f"SSE client disconnected. Active subscribers: {len(self._subscribers)}")

    async def broadcast(
        self,
        event_type: str,
        data: Dict[str, Any],
        senior_id: Optional[str] = None,
        coordinator_id: Optional[int] = None
    ):
        """Broadcast typed SSE event to relevant connected clients."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        raw_msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        async with self._lock:
            dead_queues = []
            for q, info in self._subscribers.items():
                client_coord = info.get("coordinator_id")
                # Scoping: if coordinator_id specified, only deliver if matches or if client has no filter
                if coordinator_id is not None and client_coord is not None and client_coord != coordinator_id:
                    continue

                try:
                    q.put_nowait(raw_msg)
                except asyncio.QueueFull:
                    dead_queues.append(q)
                except Exception as e:
                    logger.warning(f"Failed to deliver SSE event: {e}")
                    dead_queues.append(q)

            for dq in dead_queues:
                if dq in self._subscribers:
                    del self._subscribers[dq]


# Global Singleton Instance
sse_manager = SSEManager()

