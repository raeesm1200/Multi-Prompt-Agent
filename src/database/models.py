"""
Database models and schemas for agent configurations
"""
from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


class AgentEdge(BaseModel):
    """Edge configuration for agent handoffs"""
    name: str = Field(..., min_length=1, max_length=100, description="Tool name for handoff")
    description: str = Field(..., min_length=1, max_length=500, description="Tool description")
    action: str = Field(..., pattern="^(handoff|action)$", description="Action type")
    target_agent: str = Field(..., min_length=1, max_length=100, description="Target agent name")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tool name format"""
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Tool name must be a valid identifier')
        return v


class AgentConfig(BaseModel):
    """Individual agent configuration"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    instructions: str = Field(..., min_length=10, max_length=10000, description="Agent instructions")
    on_enter_prompt: str = Field(..., min_length=1, max_length=1000, description="Entry prompt")
    tools: List[Dict] = Field(default_factory=list, description="Agent tools")
    edges: List[AgentEdge] = Field(default_factory=list, description="Handoff edges")
    
    @field_validator('name')
    @classmethod
    def validate_agent_name(cls, v):
        """Validate agent name format"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('Agent name must be a valid identifier starting with a letter')
        return v
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        """Validate instructions content"""
        prohibited_keywords = ['execute', 'eval', '__import__', 'subprocess']
        if any(keyword in v.lower() for keyword in prohibited_keywords):
            raise ValueError('Instructions contain prohibited keywords')
        return v.strip()


class CustomerSchema(BaseModel):
    """Complete customer schema containing multiple agents"""
    customer_id: str = Field(..., min_length=1, max_length=50, description="Unique customer identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Customer name")
    description: str = Field(..., min_length=1, max_length=1000, description="Customer description")
    agents: List[AgentConfig] = Field(..., min_length=1, max_length=20, description="Agent configurations")
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v):
        """Validate customer ID format"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Customer ID can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('agents')
    @classmethod
    def validate_agent_uniqueness(cls, v):
        """Ensure agent names are unique within customer"""
        names = [agent.name for agent in v]
        if len(names) != len(set(names)):
            raise ValueError('Agent names must be unique within a customer')
        return v
    
    @field_validator('agents')
    @classmethod
    def validate_edge_targets(cls, v):
        """Ensure all edge targets reference valid agents"""
        agent_names = {agent.name for agent in v}
        for agent in v:
            for edge in agent.edges:
                if edge.target_agent not in agent_names:
                    raise ValueError(f'Edge target "{edge.target_agent}" not found in agent list')
        return v
