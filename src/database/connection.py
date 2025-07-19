"""
Database connection and operations for MongoDB
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError, ServerSelectionTimeoutError

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.logging import get_logger

from .models import CustomerSchema

logger = get_logger(__name__)


class DatabaseManager:
    """Manages MongoDB connections and operations with retry logic"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017", max_retries: int = 3):
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
    
    async def connect(self) -> bool:
        """Connect to MongoDB with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    maxPoolSize=50,
                    minPoolSize=5
                )
                
                # Test the connection
                await self.client.admin.command('ping')
                
                self.db = self.client.customers
                self.collection = self.db.schemas
                
                logger.info(f"Connected to MongoDB on attempt {attempt + 1}")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to connect to MongoDB after all retries")
                    raise ConnectionError("Unable to connect to MongoDB")
        
        return False
    
    async def init_database(self):
        """Initialize MongoDB with sample agent schemas"""
        if self.client is None:
            await self.connect()
        
        try:
            # Create index for customer_id to ensure uniqueness
            await self.collection.create_index([("customer_id", ASCENDING)], unique=True)
            count = await self.collection.count_documents({})
            logger.info(f"MongoDB initialized with {count} existing customers")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def get_customer(self, customer_id: str) -> List[dict]:
        """Get customer schema by ID with error handling"""
        if self.collection is None:
            raise ConnectionError("Database not connected")
        
        try:
            customer = await self.collection.find_one({"customer_id": customer_id})
            if customer:
                logger.info(f"Loaded customer: {customer['name']} ({len(customer['agents'])} agents)")
                return customer['agents']
            else:
                logger.warning(f"Customer {customer_id} not found, using default customer_1")
                default_customer = await self.collection.find_one({"customer_id": "customer_1"})
                return default_customer['agents'] if default_customer else []
        except Exception as e:
            logger.error(f"Database error in get_customer: {e}")
            return []
    
    async def get_all_customers(self) -> List[dict]:
        """Get all customer schemas with pagination support"""
        if self.collection is None:
            raise ConnectionError("Database not connected")
        
        customers = []
        try:
            async for customer in self.collection.find({}).limit(100):  # Limit for safety
                customer['_id'] = str(customer['_id'])
                customers.append(customer)
            return customers
        except Exception as e:
            logger.error(f"Database error in get_all_customers: {e}")
            raise
    
    async def create_customer(self, customer: CustomerSchema) -> str:
        """Create a new customer schema with validation"""
        if self.collection is None:
            raise ConnectionError("Database not connected")
        
        try:
            # Additional validation before insertion
            customer_dict = customer.dict()
            
            # Check for existing customer
            existing = await self.collection.find_one({"customer_id": customer.customer_id})
            if existing:
                raise DuplicateKeyError(f"Customer {customer.customer_id} already exists")
            
            result = await self.collection.insert_one(customer_dict)
            logger.info(f"Created customer: {customer.customer_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            raise ValueError(f"Customer {customer.customer_id} already exists")
        except Exception as e:
            logger.error(f"Database error in create_customer: {e}")
            raise
    
    async def update_customer(self, customer_id: str, customer: CustomerSchema) -> bool:
        """Update an existing customer schema"""
        if self.collection is None:
            raise ConnectionError("Database not connected")
        
        try:
            result = await self.collection.replace_one(
                {"customer_id": customer_id}, 
                customer.dict()
            )
            if result.matched_count == 0:
                raise ValueError(f"Customer {customer_id} not found")
            
            logger.info(f"Updated customer: {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Database error in update_customer: {e}")
            raise
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer schema"""
        if self.collection is None:
            raise ConnectionError("Database not connected")
        
        try:
            # Prevent deletion of default customers
            if customer_id in ['customer_1', 'customer_2']:
                raise ValueError("Cannot delete default customer schemas")
            
            result = await self.collection.delete_one({"customer_id": customer_id})
            if result.deleted_count == 0:
                raise ValueError(f"Customer {customer_id} not found")
            
            logger.info(f"Deleted customer: {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Database error in delete_customer: {e}")
            raise
    
    async def health_check(self) -> dict:
        """Check database health and return status"""
        try:
            if self.client is None:
                return {"status": "disconnected", "error": "No database connection"}
            
            # Ping the database
            await self.client.admin.command('ping')
            
            # Get collection stats
            stats = await self.db.command("collStats", "schemas")
            
            return {
                "status": "healthy",
                "connection": "active",
                "documents": stats.get("count", 0),
                "storage_size": stats.get("storageSize", 0)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'client') and self.client:
            self.client.close()
            logger.info("Database connection closed")
            self.client = None
            self.db = None
            self.collection = None


# Global database instance
db_manager = DatabaseManager()
