"""
Unit tests for database models and validation
"""
import pytest
from pydantic import ValidationError

from src.database.models import AgentConfig, AgentEdge, CustomerSchema


class TestAgentEdge:
    """Test AgentEdge model validation"""
    
    def test_valid_edge(self):
        """Test creating a valid edge"""
        edge = AgentEdge(
            name="test_tool",
            description="Test tool description",
            action="handoff",
            target_agent="TestAgent"
        )
        assert edge.name == "test_tool"
        assert edge.action == "handoff"
    
    def test_invalid_tool_name(self):
        """Test invalid tool name validation"""
        with pytest.raises(ValidationError):
            AgentEdge(
                name="123invalid",  # Can't start with number
                description="Test",
                action="handoff",
                target_agent="TestAgent"
            )
    
    def test_invalid_action(self):
        """Test invalid action validation"""
        with pytest.raises(ValidationError):
            AgentEdge(
                name="test_tool",
                description="Test",
                action="invalid_action",  # Must be 'handoff' or 'action'
                target_agent="TestAgent"
            )


class TestAgentConfig:
    """Test AgentConfig model validation"""
    
    def test_valid_agent(self):
        """Test creating a valid agent"""
        agent = AgentConfig(
            name="TestAgent",
            instructions="You are a helpful test agent for testing purposes.",
            on_enter_prompt="Hello! I'm a test agent."
        )
        assert agent.name == "TestAgent"
        assert len(agent.tools) == 0
        assert len(agent.edges) == 0
    
    def test_invalid_agent_name(self):
        """Test invalid agent name validation"""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="123Invalid",  # Can't start with number
                instructions="Test instructions",
                on_enter_prompt="Test prompt"
            )
    
    def test_prohibited_instructions(self):
        """Test instructions with prohibited keywords"""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="TestAgent",
                instructions="You should execute this command: rm -rf /",  # Contains 'execute'
                on_enter_prompt="Test prompt"
            )


class TestCustomerSchema:
    """Test CustomerSchema model validation"""
    
    def test_valid_customer(self):
        """Test creating a valid customer"""
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
    
    def test_duplicate_agent_names(self):
        """Test validation fails with duplicate agent names"""
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
        
        with pytest.raises(ValidationError):
            CustomerSchema(
                customer_id="test_customer",
                name="Test Customer",
                description="A test customer",
                agents=[agent1, agent2]
            )
    
    def test_invalid_edge_target(self):
        """Test validation fails with invalid edge target"""
        edge = AgentEdge(
            name="test_tool",
            description="Test tool",
            action="handoff",
            target_agent="NonExistentAgent"  # Target doesn't exist
        )
        
        agent = AgentConfig(
            name="TestAgent",
            instructions="Test instructions.",
            on_enter_prompt="Hello!",
            edges=[edge]
        )
        
        with pytest.raises(ValidationError):
            CustomerSchema(
                customer_id="test_customer",
                name="Test Customer",
                description="A test customer",
                agents=[agent]
            )
