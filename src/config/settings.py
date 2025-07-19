"""
Configuration management for the multi-agent system
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration with validation"""
    
    def __init__(self):
        """Initialize configuration by reading environment variables"""
        # LiveKit Configuration
        self.LIVEKIT_URL: Optional[str] = os.getenv('LIVEKIT_URL')
        self.LIVEKIT_API_KEY: Optional[str] = os.getenv('LIVEKIT_API_KEY')
        self.LIVEKIT_API_SECRET: Optional[str] = os.getenv('LIVEKIT_API_SECRET')
        
        # Database Configuration
        self.MONGODB_URL: str = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
        self.REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Redis Configuration
        self.REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
        self.REDIS_DB: int = int(os.getenv('REDIS_DB', 0))
        
        # API Configuration
        self.API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
        self.API_PORT: int = int(os.getenv('API_PORT', 8000))
        
        # Agent Configuration
        self.DEFAULT_SCHEMA_ID: str = os.getenv('DEFAULT_SCHEMA_ID', 'customer_1')
        
        # Security Configuration
        self.MAX_REQUESTS_PER_MINUTE: int = 60
        self.MAX_SESSION_DURATION_HOURS: int = 2
        
        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate_required(self):
        """Validate that required configuration is present"""
        required_vars = [
            ('LIVEKIT_URL', self.LIVEKIT_URL),
            ('LIVEKIT_API_KEY', self.LIVEKIT_API_KEY),
            ('LIVEKIT_API_SECRET', self.LIVEKIT_API_SECRET)
        ]
        
        missing = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing.append(var_name)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.API_HOST in ['localhost', '127.0.0.1', '0.0.0.0'] and self.API_PORT == 8000
    
    def get_redis_url(self) -> str:
        """Get complete Redis URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Global config instance
config = Config()
