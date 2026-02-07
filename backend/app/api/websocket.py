"""WebSocket endpoint for real-time AI Council orchestration updates."""

import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from fastapi.exceptions import WebSocketException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import verify_token
from app.core.database import get_db
from app.services.websocket_manager import websocket_manager
from app.models.user import User
from app.models.request import Request
from app.models.response import Response
from app.services.cloud_ai.circuit_breaker import get_circuit_breaker
from app.services.provider_health_checker import get_health_checker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{request_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    request_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time orchestration updates.
    
    Args:
        websocket: WebSocket connection
        request_id: Unique identifier for the request
        token: JWT authentication token from query parameter
        
    Requirements:
        - 19.1: Establish WebSocket Session when request is submitted
        - 19.6: Validate authentication token from query parameter
    """
    # Validate authentication token
    payload = verify_token(token)
    if not payload:
        logger.warning(f"Invalid token for WebSocket connection to request {request_id}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired authentication token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning(f"No user_id in token for WebSocket connection to request {request_id}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid token payload"
        )
    
    # Connect the WebSocket
    try:
        await websocket_manager.connect(request_id, websocket, user_id)
        logger.info(f"WebSocket connected: request_id={request_id}, user_id={user_id}")
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Receive messages from client (e.g., acknowledgments, heartbeat responses)
                data = await websocket.receive_json()
                
                # Handle message acknowledgments
                if data.get("type") == "ack":
                    message_id = data.get("message_id")
                    if message_id:
                        await websocket_manager.acknowledge_message(request_id, message_id)
                        logger.debug(f"Message {message_id} acknowledged for request {request_id}")
                
                # Handle heartbeat responses
                elif data.get("type") == "heartbeat_response":
                    # Update last_heartbeat timestamp
                    if request_id in websocket_manager.connection_metadata:
                        from datetime import datetime
                        websocket_manager.connection_metadata[request_id]["last_heartbeat"] = datetime.utcnow()
                        logger.debug(f"Heartbeat response received for request {request_id}")
                
                # Handle reconnection requests
                elif data.get("type") == "reconnect":
                    logger.info(f"Reconnection requested for request {request_id}")
                    # Replay queued messages
                    await websocket_manager._replay_queued_messages(request_id)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: request_id={request_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket connection for request {request_id}: {e}")
        finally:
            # Clean up connection
            await websocket_manager.disconnect(request_id)
            logger.info(f"WebSocket cleanup completed for request {request_id}")
            
    except Exception as e:
        logger.error(f"Error establishing WebSocket connection for request {request_id}: {e}")
        raise


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket manager status.
    
    Returns:
        Status information about active WebSocket connections
    """
    return {
        "active_connections": websocket_manager.get_active_connection_count(),
        "status": "operational"
    }


@router.websocket("/ws/monitoring")
async def monitoring_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time monitoring data updates.
    
    Sends monitoring data every 30 seconds to connected admin clients.
    Requires admin role for access.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token from query parameter
        
    Requirements:
        - 12.9: Auto-refresh monitoring data every 30 seconds
        - 12.9: Use WebSocket for real-time updates
    """
    # Validate authentication token
    payload = verify_token(token)
    if not payload:
        logger.warning("Invalid token for monitoring WebSocket connection")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired authentication token"
        )
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    if not user_id or user_role != "admin":
        logger.warning(f"Non-admin user attempted monitoring WebSocket: user_id={user_id}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Admin role required for monitoring"
        )
    
    # Accept the WebSocket connection
    await websocket.accept()
    logger.info(f"Monitoring WebSocket connected: user_id={user_id}")
    
    try:
        # Send initial monitoring data immediately
        await _send_monitoring_data(websocket)
        
        # Keep connection alive and send updates every 30 seconds
        while True:
            try:
                # Wait for 30 seconds or until client sends a message
                await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                # If client sends a message, send fresh data immediately
                await _send_monitoring_data(websocket)
                
            except asyncio.TimeoutError:
                # 30 seconds elapsed, send monitoring update
                await _send_monitoring_data(websocket)
                
    except WebSocketDisconnect:
        logger.info(f"Monitoring WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"Error in monitoring WebSocket for user {user_id}: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"Monitoring WebSocket cleanup completed for user {user_id}")


async def _send_monitoring_data(websocket: WebSocket):
    """
    Collect and send monitoring data through WebSocket.
    
    Args:
        websocket: WebSocket connection to send data through
    """
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Calculate 24 hours ago
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        # Count total registered users
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        # Count requests in last 24 hours
        requests_last_24h = (
            db.query(func.count(Request.id))
            .filter(Request.created_at >= twenty_four_hours_ago)
            .scalar() or 0
        )
        
        # Calculate average response time
        avg_response_time_result = (
            db.query(func.avg(Response.execution_time))
            .join(Request, Response.request_id == Request.id)
            .filter(Request.created_at >= twenty_four_hours_ago)
            .filter(Request.status == "completed")
            .scalar()
        )
        average_response_time = float(avg_response_time_result) if avg_response_time_result else 0.0
        
        # Calculate total cost in last 24 hours
        total_cost_result = (
            db.query(func.sum(Response.total_cost))
            .join(Request, Response.request_id == Request.id)
            .filter(Request.created_at >= twenty_four_hours_ago)
            .scalar()
        )
        total_cost_last_24h = float(total_cost_result) if total_cost_result else 0.0
        
        # Calculate success rate
        total_requests_24h = (
            db.query(func.count(Request.id))
            .filter(Request.created_at >= twenty_four_hours_ago)
            .filter(Request.status.in_(["completed", "failed"]))
            .scalar() or 0
        )
        
        successful_requests_24h = (
            db.query(func.count(Request.id))
            .filter(Request.created_at >= twenty_four_hours_ago)
            .filter(Request.status == "completed")
            .scalar() or 0
        )
        
        success_rate = (
            (successful_requests_24h / total_requests_24h) 
            if total_requests_24h > 0 
            else 1.0
        )
        
        # Count active WebSocket connections
        active_websockets = websocket_manager.get_active_connection_count()
        
        # Get provider health status
        health_checker = get_health_checker()
        health_statuses = await health_checker.check_all_providers()
        
        provider_health = {}
        for provider, status_obj in health_statuses.items():
            provider_health[provider] = {
                "status": status_obj.status,
                "last_check": status_obj.last_check.isoformat(),
                "response_time_ms": status_obj.response_time_ms,
                "error_message": status_obj.error_message
            }
        
        # Get circuit breaker states
        circuit_breaker = get_circuit_breaker()
        providers = ["groq", "together", "openrouter", "huggingface"]
        
        circuit_breakers = {}
        for provider in providers:
            stats = circuit_breaker.get_stats(provider)
            circuit_breakers[provider] = {
                "state": stats["state"],
                "failure_count": stats["failure_count"],
                "timeout": stats["timeout"]
            }
        
        # Send monitoring data
        monitoring_data = {
            "type": "monitoring_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "total_users": total_users,
                "requests_last_24h": requests_last_24h,
                "average_response_time": average_response_time,
                "total_cost_last_24h": total_cost_last_24h,
                "success_rate": success_rate,
                "active_websockets": active_websockets,
                "provider_health": provider_health,
                "circuit_breakers": circuit_breakers
            }
        }
        
        await websocket.send_json(monitoring_data)
        logger.debug("Monitoring data sent via WebSocket")
        
    except Exception as e:
        logger.error(f"Error collecting monitoring data: {e}")
        # Send error message
        await websocket.send_json({
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Error collecting monitoring data"
        })
    finally:
        db.close()
