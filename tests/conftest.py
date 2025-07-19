"""
Shared test fixtures and configuration for pytest
"""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set test environment variables
os.environ.update({
    'MONGODB_URL': 'mongodb://localhost:27017',
    'MONGODB_DB_NAME': 'test_agents',
    'LIVEKIT_URL': 'ws://localhost:7880',
    'LIVEKIT_API_KEY': 'devkey',
    'LIVEKIT_API_SECRET': 'secret',
    'REDIS_HOST': 'localhost',
    'REDIS_PORT': '6379',
    'REDIS_DB': '0'
})


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB for testing"""
    with patch('src.database.connection.AsyncIOMotorClient') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock database and collection
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Default successful responses
        mock_collection.count_documents.return_value = 0
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test_id")
        mock_collection.replace_one.return_value = MagicMock(matched_count=1)
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        mock_instance.admin.command.return_value = {"ok": 1}
        
        yield mock_instance, mock_collection


@pytest.fixture
def mock_redis():
    """Mock Redis for testing"""
    with patch('redis.Redis') as mock_redis_class:
        mock_instance = MagicMock()
        mock_redis_class.return_value = mock_instance
        
        # Default successful responses
        mock_instance.ping.return_value = True
        mock_instance.hset.return_value = True
        mock_instance.llen.return_value = 0
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        
        yield mock_instance


@pytest.fixture
def mock_livekit():
    """Mock LiveKit utilities for testing"""
    with patch('src.api.simple_fastapi.create_room') as mock_create_room, \
         patch('src.api.simple_fastapi.generate_token') as mock_generate_token:
        
        mock_create_room.return_value = AsyncMock()
        mock_generate_token.return_value = "mock_jwt_token_12345"
        
        yield mock_create_room, mock_generate_token


@pytest.fixture
def clean_environment():
    """Clean environment for testing configuration"""
    # Store original environment
    original_env = dict(os.environ)
    
    # Remove test-specific variables
    test_vars = [
        'API_HOST', 'API_PORT', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB',
        'MONGODB_URL', 'MONGODB_DB_NAME', 'LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET'
    ]
    
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    from src.database.models import AgentConfig
    
    return AgentConfig(
        name="TestAgent",
        instructions="You are a helpful test agent for testing purposes.",
        on_enter_prompt="Hello! I'm a test agent ready to help you."
    )


@pytest.fixture
def sample_customer_schema(sample_agent_config):
    """Sample customer schema for testing"""
    from src.database.models import CustomerSchema
    
    return CustomerSchema(
        customer_id="test_customer",
        name="Test Customer Inc",
        description="A test customer schema for unit testing",
        agents=[sample_agent_config]
    )


@pytest.fixture
def multiple_customers(sample_agent_config):
    """Multiple customer schemas for testing"""
    from src.database.models import CustomerSchema, AgentConfig
    
    customers = []
    for i in range(3):
        agent = AgentConfig(
            name=f"Agent{i}",
            instructions=f"Test agent {i} instructions.",
            on_enter_prompt=f"Hello from agent {i}!"
        )
        
        customer = CustomerSchema(
            customer_id=f"customer_{i}",
            name=f"Customer {i}",
            description=f"Test customer {i}",
            agents=[agent]
        )
        customers.append(customer)
    
    return customers


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark model tests as unit tests
        if "test_models" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark integration tests
        if "TestIntegration" in str(item.cls) if hasattr(item, 'cls') else False:
            item.add_marker(pytest.mark.integration)


# Test session setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Set up test session"""
    print("\n🧪 Starting test session...")
    yield
    print("\n✅ Test session complete!")


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up logging for tests"""
    import logging
    
    # Reduce log level for tests to avoid noise
    logging.getLogger("src").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    yield
