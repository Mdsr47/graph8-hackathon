import os
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
    is_serverless = any(os.environ.get(k) for k in ("VERCEL", "VERCEL_ENV", "AWS_LAMBDA_FUNCTION_NAME"))

    async def event_generator():
        queue = await sse_manager.subscribe()
        try:
            # Yield initial connection confirmation
            yield "event: connected\ndata: {\"status\": \"connected\", \"message\": \"SSE Live Stream Active\"}\n\n"
            
            # On serverless, limit stream duration to prevent Vercel 10s lambda timeout
            max_loops = 4 if is_serverless else None
            loops = 0

            while max_loops is None or loops < max_loops:
                loops += 1
                try:
                    timeout_val = 2.0 if is_serverless else 15.0
                    msg = await asyncio.wait_for(queue.get(), timeout=timeout_val)
                    yield msg
                except asyncio.TimeoutError:
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
