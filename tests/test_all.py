"""
Simplified working unit tests for the AI Agent project
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.database.models import AgentConfig, AgentEdge, CustomerSchema


class TestModels:
    """Test Pydantic models and validation"""
    
    def test_agent_edge_valid(self):
        """Test creating a valid AgentEdge"""
        edge = AgentEdge(
            name="test_tool",
            description="Test tool description",
            action="handoff",
            target_agent="TestAgent"
        )
        assert edge.name == "test_tool"
        assert edge.action == "handoff"
        assert edge.target_agent == "TestAgent"
    
    def test_agent_edge_invalid_name(self):
        """Test AgentEdge with invalid name"""
        with pytest.raises(ValueError):
            AgentEdge(
                name="123invalid",  # Can't start with number
                description="Test",
                action="handoff",
                target_agent="TestAgent"
            )
    
    def test_agent_config_valid(self):
        """Test creating a valid AgentConfig"""
        agent = AgentConfig(
            name="TestAgent",
            instructions="You are a helpful test agent.",
            on_enter_prompt="Hello! I'm a test agent."
        )
        assert agent.name == "TestAgent"
        assert len(agent.tools) == 0
        assert len(agent.edges) == 0
    
    def test_agent_config_invalid_name(self):
        """Test AgentConfig with invalid name"""
        with pytest.raises(ValueError):
            AgentConfig(
                name="123Invalid",  # Can't start with number
                instructions="Test instructions",
                on_enter_prompt="Test prompt"
            )
    
    def test_agent_config_prohibited_instructions(self):
        """Test AgentConfig with prohibited keywords in instructions"""
        with pytest.raises(ValueError):
            AgentConfig(
                name="TestAgent",
                instructions="You should execute this dangerous command",  # Contains 'execute'
                on_enter_prompt="Test prompt"
            )
    
    def test_customer_schema_valid(self):
        """Test creating a valid CustomerSchema"""
        agent = AgentConfig(
            name="TestAgent",
            instructions="Test instructions for the agent.",
            on_enter_prompt="Hello!"
        )
        
        customer = CustomerSchema(
            customer_id="test_customer",
            name="Test Customer",
            description="A test customer for validation",
            agents=[agent]
        )
        assert customer.customer_id == "test_customer"
        assert len(customer.agents) == 1
        assert customer.agents[0].name == "TestAgent"
    
    def test_customer_schema_duplicate_agents(self):
        """Test CustomerSchema validation fails with duplicate agent names"""
        agent1 = AgentConfig(
            name="TestAgent",
            instructions="Test instructions 1.",
            on_enter_prompt="Hello 1!"
        )
        agent2 = AgentConfig(
            name="TestAgent",  # Duplicate name
            instructions="Test instructions 2.",
            on_enter_prompt="Hello 2!"
        )
        
        with pytest.raises(ValueError):
            CustomerSchema(
                customer_id="test_customer",
                name="Test Customer",
                description="A test customer",
                agents=[agent1, agent2]
            )


class TestConfiguration:
    """Test configuration module"""
    
    def test_config_defaults(self):
        """Test that config has default values"""
        from src.config.settings import Config
        
        config = Config()
        assert hasattr(config, 'API_HOST')
        assert hasattr(config, 'API_PORT')
        assert hasattr(config, 'REDIS_HOST')
        assert hasattr(config, 'REDIS_PORT')
        assert config.API_HOST == "0.0.0.0"
        assert config.API_PORT == 8000
    
    def test_config_environment_loading(self):
        """Test configuration from environment variables"""
        import os
        from src.config.settings import Config
        
        # Test with environment variables
        test_env = {
            'API_HOST': '127.0.0.1',
            'API_PORT': '9000'
        }
        
        with patch.dict(os.environ, test_env):
            config = Config()
            assert config.API_HOST == '127.0.0.1'
            assert config.API_PORT == 9000


class TestLogging:
    """Test logging configuration"""
    
    def test_setup_logging(self):
        """Test logging setup"""
        from src.config.logging import setup_logging, get_logger
        
        setup_logging()
        logger = get_logger("test")
        
        # Should not raise exceptions
        logger.info("Test message")
        logger.error("Test error")
        assert logger.name == "test"
    
    def test_get_different_loggers(self):
        """Test getting different named loggers"""
        from src.config.logging import get_logger
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2


class TestAPIBasics:
    """Test basic API functionality"""
    
    @pytest.fixture
    def mock_app_dependencies(self):
        """Mock app dependencies"""
        with patch('src.api.simple_fastapi.db_manager') as mock_db, \
             patch('src.api.simple_fastapi.redis_client') as mock_redis, \
             patch('src.api.simple_fastapi.config') as mock_config:
            
            # Configure basic mocks
            mock_db.init_database.return_value = None
            mock_db.close.return_value = None
            mock_db.health_check.return_value = {"status": "healthy"}
            mock_redis.ping.return_value = True
            mock_config.validate_required.return_value = None
            
            yield mock_db, mock_redis, mock_config
    
    def test_app_import(self, mock_app_dependencies):
        """Test that the FastAPI app can be imported"""
        from src.api.simple_fastapi import app
        assert app is not None
        assert hasattr(app, 'title')
        assert app.title == "Multi-Agent System API"
    
    def test_root_endpoint(self, mock_app_dependencies):
        """Test the root endpoint"""
        from src.api.simple_fastapi import app
        
        client = TestClient(app)
        # Add proper host header for TrustedHostMiddleware
        response = client.get("/", headers={"host": "localhost"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Multi-Agent System API"
        assert data["status"] == "running"


class TestDatabaseModels:
    """Test database model functionality"""
    
    def test_agent_edge_validation(self):
        """Test AgentEdge field validation"""
        # Valid edge
        edge = AgentEdge(
            name="valid_tool",
            description="A valid tool",
            action="handoff",
            target_agent="ValidAgent"
        )
        assert edge.name == "valid_tool"
        
        # Invalid action
        with pytest.raises(ValueError):
            AgentEdge(
                name="tool",
                description="Test",
                action="invalid",  # Not 'handoff' or 'action'
                target_agent="Agent"
            )
    
    def test_customer_schema_edge_validation(self):
        """Test that CustomerSchema validates edge targets"""
        # Create edge pointing to non-existent agent
        edge = AgentEdge(
            name="test_tool",
            description="Test tool",
            action="handoff",
            target_agent="NonExistentAgent"
        )
        
        agent = AgentConfig(
            name="RealAgent",
            instructions="Test instructions.",
            on_enter_prompt="Hello!",
            edges=[edge]
        )
        
        # Should fail validation because target agent doesn't exist
        with pytest.raises(ValueError):
            CustomerSchema(
                customer_id="test_customer",
                name="Test Customer",
                description="Test",
                agents=[agent]
            )


class TestIntegration:
    """Basic integration tests"""
    
    def test_model_serialization(self):
        """Test that models can be serialized"""
        agent = AgentConfig(
            name="TestAgent",
            instructions="Test instructions.",
            on_enter_prompt="Hello!"
        )
        
        customer = CustomerSchema(
            customer_id="test_customer",
            name="Test Customer",
            description="A test customer",
            agents=[agent]
        )
        
        # Should be able to serialize to dict
        data = customer.model_dump()
        assert data["customer_id"] == "test_customer"
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "TestAgent"
    
    def test_model_deserialization(self):
        """Test that models can be deserialized"""
        data = {
            "customer_id": "test_customer",
            "name": "Test Customer",
            "description": "A test customer",
            "agents": [
                {
                    "name": "TestAgent",
                    "instructions": "Test instructions.",
                    "on_enter_prompt": "Hello!",
                    "tools": [],
                    "edges": []
                }
            ]
        }
        
        customer = CustomerSchema(**data)
        assert customer.customer_id == "test_customer"
        assert len(customer.agents) == 1
        assert customer.agents[0].name == "TestAgent"


# Simple test runner for verification
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
