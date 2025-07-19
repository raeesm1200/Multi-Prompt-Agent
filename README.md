# Multi-Prompt Agent Implementation

**Hiring Project: Dynamic Multi-Prompt Agent Architecture using LiveKit**

## Demo Video

🎥 **[Watch the Live Demo](https://www.loom.com/share/744bb44859234feca149a0866f070b36)**

*7-minute walkthrough demonstrating:*
- *Architecture overview and design decisions*
- *JSON schema structure and validation*
- *Live API demonstrations with real agent configurations*
- *Extension points for adding new agent types*

---

## Objective

This project demonstrates the implementation of a dynamic, modular multi-prompt agent system inspired by Retell AI's architecture, built using the LiveKit library. The system supports multiple customers with custom configurations and allows prompt content and logic to be dynamically injected based on input.

## Business Use Case

The multi-prompt agent system is designed to handle complex conversational flows where:
- Different customers have unique agent configurations and behavior patterns
- Agents can dynamically switch between different prompts based on conversation context
- The system supports handoffs between specialized agents within a customer's workflow
- Real-time voice interactions are managed through LiveKit's infrastructure

## Architecture Overview

### Core Components

```
src/
├── agents/           # Dynamic agent logic and factory patterns
│   ├── agent_factory.py     # Runtime agent class creation
│   └── multi_agent.py       # LiveKit voice assistant worker
├── api/              # REST API and LiveKit integration
│   ├── livekit_utils.py     # Room management and token handling
│   └── simple_fastapi.py    # Customer schema API endpoints
├── config/           # Configuration management
│   ├── settings.py          # Environment variables and defaults
│   └── logging.py           # Centralized logging setup
├── database/         # Data persistence layer
│   ├── connection.py        # MongoDB async operations
│   └── models.py            # Pydantic V2 data models and validation
└── scripts/          # Database population utilities
```

### Key Design Principles

1. **Dynamic Configuration**: Agent behavior is defined through JSON schemas stored in MongoDB
2. **Modular Architecture**: Clean separation between voice processing, API layer, and data persistence
3. **Runtime Flexibility**: Agent classes are created dynamically based on customer configurations
4. **Scalable Design**: Supports multiple customers with isolated agent configurations

## JSON Schema Design

The system uses a hierarchical JSON schema structure:

### CustomerSchema
- Represents a complete customer configuration
- Contains multiple specialized agents
- Validates agent name uniqueness and edge target consistency

### AgentConfig
- Defines individual agent behavior and prompts
- Supports dynamic instruction sets and entry prompts
- Includes validation for secure prompt content

### AgentEdge
- Represents transitions between agents
- Supports both "handoff" (agent switching) and "action" (tool execution)
- Validates target agent existence within customer scope

**Example JSON Structure:**
```json
{
  "customer_id": "healthcare_clinic",
  "name": "HealthCare Assistant",
  "description": "Multi-agent system for patient intake and support",
  "agents": [
    {
      "name": "IntakeAgent",
      "instructions": "You are a medical intake specialist...",
      "on_enter_prompt": "Hello! I'll help you with your appointment.",
      "tools": ["appointment_booking", "insurance_verification"],
      "edges": [
        {
          "name": "transfer_to_specialist",
          "description": "Transfer to medical specialist",
          "action": "handoff",
          "target_agent": "SpecialistAgent"
        }
      ]
    },
    {
      "name": "SpecialistAgent",
      "instructions": "You are a medical specialist assistant...",
      "on_enter_prompt": "I'm here to help with your medical questions.",
      "tools": ["medical_lookup", "prescription_check"],
      "edges": []
    }
  ]
}
```

## Implementation Highlights

### Dynamic Agent Creation
The `AgentFactory` class creates agent instances at runtime based on JSON configurations:
- Validates agent configurations against business rules
- Supports prompt injection and dynamic instruction sets
- Manages agent lifecycle and state transitions

### LiveKit Integration
- Real-time voice processing using LiveKit's infrastructure
- Session management with proper room creation and cleanup
- Token-based authentication for secure access

### Data Validation
- Pydantic V2 models with custom field validators
- Business logic constraints (naming conventions, prohibited keywords)
- Cross-reference validation for agent edges and targets

## Quick Start

### 1. Environment Setup
```bash
# Clone and setup
git clone <repository>
cd ai-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Service Dependencies
```bash
# Start MongoDB and Redis
docker-compose up -d

# Verify services are running
docker ps
```

### 3. Database Population
```bash
# Populate with sample customer schemas
python scripts/populate_database.py
```

### 4. Run the System
```bash
# Start FastAPI server (Terminal 1)
python src/api/simple_fastapi.py

# Start LiveKit agent worker (Terminal 2) (development mode)
python src/agents/multi_agent.py dev
```

## API Usage

### Customer Management
```bash
# List all customers
curl http://localhost:8000/customers

# Create new customer schema
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d @customer_schema.json

# Start voice session
curl -X POST http://localhost:8000/start-session \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "healthcare_clinic", "user_name": "Guest"}'
```

## Testing

Comprehensive test suite with **100% success rate**:

```bash
# Run all tests
python run_tests.py --type all

# Run model validation tests only  
python run_tests.py --type models
```

**Test Coverage:**
- ✅ JSON Schema validation and business rules
- ✅ Dynamic agent configuration loading
- ✅ API endpoint functionality
- ✅ Database operations and error handling
- ✅ Integration testing for complete workflows

## Configuration

### Environment Variables
Create `.env` file:
```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_secret

# Database Configuration  
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ai_agent_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Thought Process & Design Decisions

### 1. **Schema-First Approach**
Chose JSON schemas as the primary configuration method to enable:
- Non-technical users to modify agent behavior
- Runtime configuration changes without code deployment
- Easy A/B testing of different prompt strategies

### 2. **Agent Factory Pattern**
Implemented dynamic class creation to support:
- Runtime instantiation of agents based on configurations
- Memory-efficient handling of multiple customer schemas
- Isolation between different customer environments

### 3. **Validation-Heavy Design**
Used Pydantic V2 for comprehensive validation because:
- Multi-prompt systems are complex and error-prone
- Early validation prevents runtime failures during voice sessions
- Business rules enforcement ensures system reliability

### 4. **Async-First Architecture**
Built with async/await throughout for:
- Non-blocking I/O operations with MongoDB and Redis
- Concurrent handling of multiple voice sessions
- Scalable performance under load

## Assumptions Made

1. **Voice-Primary Interface**: System designed for voice interactions via LiveKit
2. **MongoDB for Flexibility**: NoSQL chosen for schema evolution and complex nested structures  
3. **Single-Tenant Per Session**: Each voice session operates within one customer's agent ecosystem
4. **Real-Time Requirements**: Low-latency agent switching for natural conversation flow
5. **Security-Conscious**: Input validation and sanitization to prevent prompt injection attacks

## Testing & Extension Guidelines

### Adding New Agent Types
1. Define new validation rules in `src/database/models.py`
2. Add agent creation logic to `src/agents/agent_factory.py`  
3. Create comprehensive tests in `tests/test_models.py`

### Extending Prompt Logic
1. Modify `AgentConfig` model to support new prompt types
2. Update `multi_agent.py` to handle new prompt patterns
3. Add integration tests for new conversation flows

### Custom Customer Requirements
1. Create customer-specific validation rules
2. Implement custom agent behaviors in the factory
3. Add database migration scripts for schema updates

## Production Considerations

- **Monitoring**: Add logging for agent transitions and prompt effectiveness
- **Caching**: Implement Redis caching for frequently accessed schemas
- **Scaling**: Deploy multiple agent workers for load distribution
- **Security**: Implement authentication for schema modification endpoints

---

*This implementation demonstrates clean, professional, and scalable architecture suitable for production multi-prompt agent systems.*
