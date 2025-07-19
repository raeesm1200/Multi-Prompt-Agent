"""
LiveKit utilities for room and token management
"""
import sys
from datetime import timedelta
from pathlib import Path

from livekit import api

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.config.logging import get_logger

logger = get_logger(__name__)


async def create_room(room_name: str):
    """Create a LiveKit room"""
    lkapi = api.LiveKitAPI(
        url=config.LIVEKIT_URL,
        api_key=config.LIVEKIT_API_KEY,
        api_secret=config.LIVEKIT_API_SECRET,
    )
    
    room = await lkapi.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            empty_timeout=300,
            max_participants=10,
        )
    )
    
    logger.info(f"Room created: {room.name}")
    await lkapi.aclose()
    return room


def generate_token(room_name: str, user_identity: str = None, user_name: str = None):
    """Generate LiveKit access token"""
    token = api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET) \
        .with_identity(user_identity) \
        .with_name(user_name) \
        .with_ttl(timedelta(hours=1)) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
    
    jwt_token = token.to_jwt()
    logger.info(f"Generated new token for {user_name} in room {room_name}")
    logger.debug(f"Token preview: {jwt_token[:50]}...")
    
    return jwt_token
