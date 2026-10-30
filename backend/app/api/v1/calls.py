"""WebRTC Direct In-App Calling (Instagram / Snapchat style) Signaling Router.
Facilitates direct, peer-to-peer live audio calls between:
- Care Coordinator App (/coordinator/dashboard)
- Senior Citizen PWA (/senior/easy)
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body, HTTPException

from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory registry of active live calls
ACTIVE_CALLS: Dict[str, Dict[str, Any]] = {}


@router.post("/initiate")
async def initiate_live_call(payload: Dict[str, Any] = Body(...)):
    """
    Initiate a live direct in-app WebRTC call.
    Caller sends their SDP Offer and caller profile.
    Target receives incoming call ring event via SSE.
    """
    call_id = payload.get("call_id") or f"call_{int(time.time() * 1000)}"
    caller_role = payload.get("caller_role", "coordinator")  # "coordinator" or "senior"
    caller_name = payload.get("caller_name", "Anvesha Sharma (Care Coordinator)")
    senior_id = payload.get("senior_id", "SEN_001")
    sdp_offer = payload.get("sdp_offer")

    call_record = {
        "call_id": call_id,
        "caller_role": caller_role,
        "caller_name": caller_name,
        "senior_id": senior_id,
        "status": "RINGING",
        "start_time": time.time(),
        "sdp_offer": sdp_offer
    }
    ACTIVE_CALLS[call_id] = call_record

    # Broadcast direct_call_incoming event via SSE
    await sse_manager.broadcast(
        event_type="direct_call_incoming",
        data={
            "call_id": call_id,
            "caller_role": caller_role,
            "caller_name": caller_name,
            "senior_id": senior_id,
            "sdp_offer": sdp_offer,
            "timestamp": time.time()
        },
        senior_id=senior_id
    )

    logger.info(f"Direct live call initiated: {call_id} from {caller_role} ({caller_name}) to {senior_id}")
    return {"status": "RINGING", "call_id": call_id, "record": call_record}


@router.post("/answer")
async def answer_live_call(payload: Dict[str, Any] = Body(...)):
    """
    Target answers the call and returns their SDP Answer.
    """
    call_id = payload.get("call_id")
    senior_id = payload.get("senior_id", "SEN_001")
    sdp_answer = payload.get("sdp_answer")
    responder_name = payload.get("responder_name", "Krishan Singh (Senior)")

    if call_id in ACTIVE_CALLS:
        ACTIVE_CALLS[call_id]["status"] = "CONNECTED"
        ACTIVE_CALLS[call_id]["connected_at"] = time.time()
        ACTIVE_CALLS[call_id]["sdp_answer"] = sdp_answer

    # Broadcast direct_call_answered event to the caller
    await sse_manager.broadcast(
        event_type="direct_call_answered",
        data={
            "call_id": call_id,
            "senior_id": senior_id,
            "responder_name": responder_name,
            "sdp_answer": sdp_answer,
            "timestamp": time.time()
        },
        senior_id=senior_id
    )

    logger.info(f"Direct live call answered: {call_id} by {responder_name}")
    return {"status": "CONNECTED", "call_id": call_id}


@router.post("/ice")
async def exchange_ice_candidate(payload: Dict[str, Any] = Body(...)):
    """
    Exchange ICE candidate between peers.
    """
    call_id = payload.get("call_id")
    senior_id = payload.get("senior_id", "SEN_001")
    candidate = payload.get("candidate")
    sender_role = payload.get("sender_role", "coordinator")

    # Broadcast candidate to peer
    await sse_manager.broadcast(
        event_type="direct_call_ice",
        data={
            "call_id": call_id,
            "senior_id": senior_id,
            "candidate": candidate,
            "sender_role": sender_role,
            "timestamp": time.time()
        },
        senior_id=senior_id
    )
    return {"status": "ICE_FORWARDED"}


@router.post("/hangup")
async def hangup_live_call(payload: Dict[str, Any] = Body(...)):
    """
    Hang up or decline an active live call.
    """
    call_id = payload.get("call_id")
    senior_id = payload.get("senior_id", "SEN_001")
    reason = payload.get("reason", "normal_hangup")
    ended_by = payload.get("ended_by", "coordinator")

    duration = 0
    if call_id in ACTIVE_CALLS:
        call = ACTIVE_CALLS[call_id]
        call["status"] = "ENDED"
        duration = int(time.time() - call.get("connected_at", call.get("start_time", time.time())))
        call["duration_seconds"] = max(0, duration)

    # Broadcast direct_call_hangup to peer
    await sse_manager.broadcast(
        event_type="direct_call_hangup",
        data={
            "call_id": call_id,
            "senior_id": senior_id,
            "reason": reason,
            "ended_by": ended_by,
            "duration_seconds": duration,
            "timestamp": time.time()
        },
        senior_id=senior_id
    )

    logger.info(f"Direct live call ended: {call_id} by {ended_by} (duration: {duration}s)")
    return {"status": "ENDED", "call_id": call_id, "duration_seconds": duration}

