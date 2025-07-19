"""
Multi-Agent Voice AI Worker
Main worker process that handles voice conversations with agent handoffs
"""
import asyncio
import sys
from pathlib import Path

import redis
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import (
    cartesia,
    deepgram,
    groq,  # Groq for LLM
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.config.logging import get_logger, setup_logging
from src.database import db_manager
from src.agents.agent_factory import agent_factory

logger = get_logger(__name__)


# Redis connection
redis_client = redis.Redis(
    host=config.REDIS_HOST, 
    port=config.REDIS_PORT, 
    db=config.REDIS_DB, 
    decode_responses=True
)


async def entrypoint(ctx: agents.JobContext):
    """
    Multi-Agent STT-LLM-TTS Pipeline (RetellAI style)
    
    Features:
    - Multiple specialized agents with different personalities
    - Smooth handoffs between agents
    - Consent collection workflow
    - Technical specialist routing
    - Redis-based API control
    """
    
    # Initialize database
    await db_manager.init_database()
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        logger.error("Make sure Redis Docker container is running!")
        return
    
    logger.info("Waiting for Redis commands...")
    logger.info(f"Call API: http://{config.API_HOST}:{config.API_PORT}/start-session?user_name=John")

    await ctx.connect()
    logger.info("Connected to room")
    
    # Now wait for participant to join
    participant = await ctx.wait_for_participant()
    logger.debug(f"Participant joined: {participant}")
    
    room_name = ctx.room.name
    user_identity = participant.identity

    session_key = f"session:{room_name}:{user_identity}"
    command = redis_client.hgetall(session_key)
    logger.info(f"Received command: {command}")

    # Get agent schema from database
    agent_schema = await db_manager.get_customer(command["customer_id"])
    first_agent = agent_schema[0]['name']  # First agent in schema
    
    # Create agent classes from schema
    agent_classes = agent_factory(agent_schema)
    logger.info(f"Agent classes created: {list(agent_classes.keys())}")
    
    initial_agent = agent_classes[first_agent]()
    logger.info(f"Starting with agent: {initial_agent.__class__.__name__}")
    logger.debug(f"Agent instructions: {initial_agent.instructions[:100]}...")

    if command:
        logger.info(f"Processing command: {command}")
        
        if command["action"] == "start_session":
            session = AgentSession(
                # Speech-to-Text: Deepgram Nova-3 model with multi-language support
                stt=deepgram.STT(model="nova-3", language="multi"),
                
                # Large Language Model: Groq LLaMA-3 (fast and cost-effective)
                llm=groq.LLM(model="llama-3.1-8b-instant"),
                
                # Text-to-Speech: Cartesia Sonic-2 with a natural voice
                tts=cartesia.TTS(
                    model="sonic-2", 
                    voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"  # Natural female voice
                ),
                
                # Voice Activity Detection: Silero VAD
                vad=silero.VAD.load(),
                
                # Turn detection for managing conversation flow
                turn_detection=MultilingualModel(),
            )
            await session.start(
                room=ctx.room,
                agent=initial_agent,  # Start with first agent from schema
                room_input_options=RoomInputOptions(
                    # Enhanced noise cancellation (LiveKit Cloud only)
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )

            logger.info(f"Room created: {ctx.room}")
            logger.info("Multi-Agent Voice AI System Started")
            logger.info(f"Starting with {first_agent} agent")


if __name__ == "__main__":
    try:
        from src.config.logging import setup_logging
    except ImportError:
        from ..config.logging import setup_logging
    
    # Setup logging before starting
    setup_logging()
    
    # Validate configuration before starting
    config.validate_required()
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
