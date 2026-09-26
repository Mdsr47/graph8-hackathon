import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.sse_manager import sse_manager

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("/live")
async def live_event_stream():
    """
    Server-Sent Events (SSE) stream.
    Delivers real-time telemetry on decisions, events, approvals, and replies.
    """
    async def event_generator():
        queue = await sse_manager.subscribe()
        try:
            # Yield initial connection confirmation
            yield "event: connected\ndata: {\"status\": \"connected\", \"message\": \"SSE Live Stream Active\"}\n\n"
            
            while True:
                try:
                    # Wait for next event with a 15-second heartbeat timeout
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep HTTP connection alive
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
