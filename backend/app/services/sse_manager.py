import asyncio
import json
import logging
from typing import Set, Dict, Any

logger = logging.getLogger("sse_manager")

class SSEManager:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"[SSE] Client connected. Total subscribers: {len(self.subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"[SSE] Client disconnected. Total subscribers: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcasts an SSE message to all connected clients."""
        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        if not self.subscribers:
            return

        dead_queues = []
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except Exception as e:
                logger.warning(f"[SSE] Failed to send to queue: {e}")
                dead_queues.append(queue)

        for dq in dead_queues:
            self.unsubscribe(dq)

sse_manager = SSEManager()
