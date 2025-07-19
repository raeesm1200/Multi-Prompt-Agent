"""
FastAPI Server for Multi-Agent System
Provides REST API for agent schema management and session control
"""
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.config.logging import get_logger, setup_logging
from src.database import CustomerSchema, db_manager
from src.api.livekit_utils import create_room, generate_token

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System API",
    description="Controls multi-agent voice sessions and manages agent schemas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Redis connection
redis_client = redis.Redis(
    host=config.REDIS_HOST, 
    port=config.REDIS_PORT, 
    db=config.REDIS_DB, 
    decode_responses=True
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and validate config on startup"""
    config.validate_required()
    await db_manager.init_database()


@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    await db_manager.close()


@app.get("/customers")
async def get_all_customers():
    """Get all customer schemas"""
    try:
        customers = await db_manager.get_all_customers()
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get a specific customer schema"""
    try:
        customer = await db_manager.collection.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        customer['_id'] = str(customer['_id'])
        return customer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/customers")
async def create_customer(customer: CustomerSchema):
    """Create a new customer schema"""
    try:
        customer_id = await db_manager.create_customer(customer)
        return {"message": "Customer created successfully", "id": customer_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.put("/customers/{customer_id}")
async def update_customer(customer_id: str, customer: CustomerSchema):
    """Update an existing customer schema"""
    try:
        await db_manager.update_customer(customer_id, customer)
        return {"message": "Customer updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete a customer schema"""
    try:
        await db_manager.delete_customer(customer_id)
        return {"message": "Customer deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/start-session")
async def start_session(
    request: Request,
    customer_id: str = "customer_1", 
    user_name: str = "Guest"
):
    """Start a new agent session"""
    # Basic input validation
    if not customer_id or len(customer_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid customer_id")
    
    if not user_name or len(user_name) > 100:
        raise HTTPException(status_code=400, detail="Invalid user_name")
    
    # Verify customer exists
    try:
        customer = await db_manager.collection.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    except Exception as e:
        logger.error(f"Database error during customer lookup: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    room_name = f"room-{uuid.uuid4()}"
    user_identity = f"user-{uuid.uuid4()}"

    try:
        await create_room(room_name)
        token = generate_token(room_name, user_identity, user_name)
        
        # Create start command with unique session ID
        session_key = f"session:{room_name}:{user_identity}"
        redis_client.hset(session_key, mapping={
            "action": "start_session",
            "customer_id": customer_id,
        })

        logger.info(f"Sent start_session command for customer: {customer_id}, user: {user_name}")

        return {
            "status": "command_sent",
            "room_name": room_name,
            "user_identity": user_identity,
            "user_name": user_name,
            "room_token": token,
            "message": f"Session start command sent for customer: {customer_id}",
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@app.get("/queue-status")
async def queue_status():
    """Check Redis queue status"""
    queue_length = redis_client.llen("session_commands")
    
    return {
        "queue_length": queue_length,
        "redis_connected": redis_client.ping()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database health
        db_health = await db_manager.health_check()
        
        # Check Redis health
        try:
            redis_ping = redis_client.ping()
            redis_health = {"status": "healthy", "connected": redis_ping}
        except Exception as e:
            redis_health = {"status": "unhealthy", "error": str(e)}
        
        overall_status = "healthy" if (
            db_health["status"] == "healthy" and 
            redis_health["status"] == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": "2025-07-17T05:00:00Z",  # You could use datetime.utcnow()
            "services": {
                "database": db_health,
                "redis": redis_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Welcome endpoint"""
    return {"message": "Multi-Agent System API", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    
    # Test connections
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        logger.error("Make sure Redis Docker container is running: docker-compose up -d")
    
    logger.info("Starting FastAPI Server with MongoDB and Redis")
    logger.info(f"API: http://{config.API_HOST}:{config.API_PORT}")
    logger.info(f"Docs: http://{config.API_HOST}:{config.API_PORT}/docs")
    logger.info(f"Start session: http://{config.API_HOST}:{config.API_PORT}/start-session?user_name=John")
    logger.info(f"Queue status: http://{config.API_HOST}:{config.API_PORT}/queue-status")
    logger.info(f"Agent schemas: http://{config.API_HOST}:{config.API_PORT}/schemas")
    logger.info("Start databases with: docker-compose up -d")
    
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
