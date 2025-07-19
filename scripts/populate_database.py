"""
Database Population Script - Populate MongoDB with useful agent schemas
Run this after starting the databases with docker-compose up -d

This script populates the database with the original agent schemas that were 
hardcoded in the multi_agent.py file, making them available for testing.
"""
import asyncio
import logging
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import CustomerSchema, db_manager

# Setup basic logging for script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Customer schemas with nested agents
CUSTOMERS = {
    "customer_1": {
        "customer_id": "customer_1",
        "name": "TechCorp Solutions",
        "description": "Technology company with consent collection and technical support workflow",
        "agents": [
            {
                "name": "ConsentCollector",
                "instructions": """You are a professional voice AI agent for call consent collection. 
                Ask for recording consent clearly and wait for a clear yes/no response. 
                If they agree, use the consent_given tool to handoff to another agent.
                Be polite and professional.
                After consent, you will transfer to either HelpfulAssistant or TechnicalSpecialist based on user needs.""",
                "on_enter_prompt": "Hello! Before we begin, may I record this call for quality assurance purposes?",
                "tools": [],
                "edges": [
                    {
                        "name": "consent_to_helper",
                        "description": "User gave consent and wants general assistance or casual conversation",
                        "action": "handoff",
                        "target_agent": "HelpfulAssistant"
                    },
                    {
                        "name": "consent_to_specialist", 
                        "description": "User gave consent and immediately has technical questions or programming needs",
                        "action": "handoff",
                        "target_agent": "TechnicalSpecialist"
                    }
                ]
            },
            {
                "name": "HelpfulAssistant",
                "instructions": """You are a helpful and friendly AI assistant. 
                Answer questions, provide information, and assist with various tasks. 
                Keep responses conversational and natural for voice interaction.
                If the user has complex technical questions, transfer them to the TechnicalSpecialist.""",
                "on_enter_prompt": "Thank you for your consent. How can I help you today?",
                "tools": [],
                "edges": [
                    {
                        "name": "transfer_to_specialist",
                        "description": "Transfer to a specialist when user has complex technical questions about programming, troubleshooting, or needs detailed technical explanations",
                        "action": "handoff", 
                        "target_agent": "TechnicalSpecialist"
                    }
                ]
            },
            {
                "name": "TechnicalSpecialist", 
                "instructions": """You are a technical specialist AI assistant.
                Help with complex technical questions, programming, troubleshooting, and detailed explanations.
                Provide accurate, detailed technical information while keeping it understandable.
                If the user asks general non-technical questions, transfer them back to the HelpfulAssistant.""",
                "on_enter_prompt": "I'm a technical specialist. What technical question can I help you with?",
                "tools": [],
                "edges": [
                    {
                        "name": "back_to_general",
                        "description": "Transfer back to general assistant when user has non-technical questions or general conversation",
                        "action": "handoff",
                        "target_agent": "HelpfulAssistant"
                    }
                ]
            }
        ]
    },
    
    "customer_2": {
        "customer_id": "customer_2",
        "name": "RetailPro Inc",
        "description": "Retail company with sales and support agents plus demonstration flow",
        "agents": [
            {
                "name": "SalesAgent",
                "instructions": "You are a sales representative for RetailPro Inc. Help customers understand products, pricing, and make purchases. Provide excellent customer service and guide them through their buying journey. If technical issues arise, transfer to support.",
                "on_enter_prompt": "Hi! I'm your sales representative from RetailPro Inc. I'm here to help you find the perfect solution for your needs.",
                "tools": [],
                "edges": [
                    {
                        "name": "transfer_to_support",
                        "description": "Transfer to technical support for technical issues or troubleshooting",
                        "action": "handoff",
                        "target_agent": "SupportAgent"
                    }
                ]
            },
            {
                "name": "SupportAgent", 
                "instructions": "You are a technical support agent for RetailPro Inc. Help customers with technical issues, troubleshooting, and provide detailed assistance. Be patient and thorough in your explanations. You can transfer back to sales for purchasing questions.",
                "on_enter_prompt": "Hello! I'm from RetailPro technical support. How can I help you today with your technical questions?",
                "tools": [],
                "edges": [
                    {
                        "name": "back_to_sales",
                        "description": "Transfer back to sales for purchasing or product information questions",
                        "action": "handoff",
                        "target_agent": "SalesAgent"
                    }
                ]
            },
            {
                "name": "Alice",
                "instructions": "You are Alice, a demo assistant for RetailPro Inc. When users ask about technical topics, music, or need specialized help, hand them off to Bob for demonstration purposes.",
                "on_enter_prompt": "Hi! I'm Alice from RetailPro. I can help with general questions. For technical topics or music, I'll connect you with Bob.",
                "tools": [],
                "edges": [
                    {
                        "name": "handoff_to_bob",
                        "description": "Hand off to Bob for technical questions or music topics demo",
                        "action": "handoff",
                        "target_agent": "Bob"
                    }
                ]
            },
            {
                "name": "Bob",
                "instructions": "You are Bob, a technical expert and music enthusiast at RetailPro Inc. Help users with technical questions and music recommendations for demo purposes. You can hand back to Alice for general topics.",
                "on_enter_prompt": "Hello! I'm Bob from RetailPro. I specialize in technical topics and music. How can I help you today?",
                "tools": [],
                "edges": [
                    {
                        "name": "handoff_to_alice",
                        "description": "Hand off to Alice for general questions",
                        "action": "handoff",
                        "target_agent": "Alice"
                    }
                ]
            }
        ]
    }
}

async def main():
    logger.info("AI Agent Customer Database Population Script")
    logger.info("=" * 50)
    
    try:
        # Initialize database connection
        await db_manager.init_database()
        logger.info("Connected to MongoDB")
        
        # Check existing customers
        existing_customers = await db_manager.get_all_customers()
        existing_ids = {customer['customer_id'] for customer in existing_customers}
        
        logger.info(f"Found {len(existing_customers)} existing customers:")
        for customer in existing_customers:
            logger.info(f"  - {customer['customer_id']}: {customer['name']}")
        
        # Populate each customer
        logger.info(f"Populating {len(CUSTOMERS)} customer schemas...")
        
        for customer_data in CUSTOMERS.values():
            customer_id = customer_data["customer_id"]
            
            if customer_id in existing_ids:
                logger.warning(f"Customer '{customer_id}' already exists, skipping...")
                continue
                
            try:
                # Create CustomerSchema object and insert
                customer = CustomerSchema(**customer_data)
                await db_manager.create_customer(customer)
                logger.info(f"Added customer: {customer_id} ({customer_data['name']})")
                
            except Exception as e:
                logger.error(f"Failed to add customer '{customer_id}': {e}")
        
        # Display final state
        logger.info("=" * 50)
        logger.info("Customer database population complete!")
        
        final_customers = await db_manager.get_all_customers()
        logger.info(f"Total customers in database: {len(final_customers)}")
        
        for customer in final_customers:
            agents_count = len(customer['agents'])
            logger.info(f"  {customer['customer_id']}: {customer['name']} ({agents_count} agents)")
            for agent in customer['agents']:
                edges_count = len(agent.get('edges', []))
                logger.info(f"    {agent['name']} ({edges_count} handoff options)")
        
        logger.info("Ready to test! Use these customer schemas with the FastAPI server:")
        logger.info("  http://localhost:8000/start-session?customer_id=customer_1&user_name=TestUser")
        logger.info("  http://localhost:8000/start-session?customer_id=customer_2&user_name=TestUser")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
