"""
Enhanced AWS Operations Agent with Easy/Customize modes
Supports comprehensive AWS actions and intelligent conversation flow
"""
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# AgentCore imports
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.types import ConversationMessage, ToolUse, ToolResult

# Shared imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agent_shared.config import get_config
from agent_shared.memory import MemoryManager
from agent_shared.mcp import MCPClient

logger = logging.getLogger(__name__)

class EnhancedAWSAgent:
    def __init__(self):
        self.config = get_config()
        self.memory_manager = MemoryManager()
        self.mcp_client = MCPClient()
        self.conversation_state = {}
        
    async def process_message(self, message: str, user_id: str = "default") -> str:
        """Process user message with enhanced AWS operations"""
        try:
            # Initialize conversation state for user
            if user_id not in self.conversation_state:
                self.conversation_state[user_id] = {
                    'pending_confirmations': {},
                    'context': {},
                    'last_action': None
                }
            
            # Check for confirmation responses
            if message.upper() in ['CONFIRM', 'YES', 'Y']:
                return await self._handle_confirmation(user_id, True)
            elif message.upper() in ['CANCEL', 'NO', 'N']:
                return await self._handle_confirmation(user_id, False)
            
            # Parse intent and determine action
            intent = await self._parse_intent(message)
            
            if intent['type'] == 'create_resource':
                return await self._handle_resource_creation(intent, user_id)
            elif intent['type'] == 'manage_resource':
                return await self._handle_resource_management(intent, user_id)
            elif intent['type'] == 'query_resources':
                return await self._handle_resource_query(intent, user_id)
            elif intent['type'] == 'cost_optimization':
                return await self._handle_cost_optimization(intent, user_id)
            elif intent['type'] == 'security_action':
                return await self._handle_security_action(intent, user_id)
            else:
                return await self._handle_general_query(message, user_id)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return f"❌ Sorry, I encountered an error: {str(e)}"
    
    async def _parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse user message to determine intent and extract parameters"""
        message_lower = message.lower()
        
        # Resource creation patterns
        create_patterns = {
            'ec2': ['create ec2', 'launch instance', 'new instance', 'create instance'],
            'lambda': ['create lambda', 'new function', 'create function'],
            'rds': ['create database', 'create rds', 'new database'],
            's3': ['create bucket', 'new bucket', 'create s3'],
            'vpc': ['create vpc', 'new vpc'],
            'alb': ['create load balancer', 'create alb', 'new load balancer']
        }
        
        # Management patterns
        manage_patterns = {
            'start': ['start', 'turn on', 'power on'],
            'stop': ['stop', 'turn off', 'power off', 'shut down'],
            'restart': ['restart', 'reboot'],
            'delete': ['delete', 'remove', 'terminate'],
            'scale': ['scale up', 'scale down', 'increase capacity', 'decrease capacity']
        }
        
        # Check for creation intent
        for resource_type, patterns in create_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return {
                    'type': 'create_resource',
                    'resource_type': resource_type,
                    'original_message': message
                }
        
        # Check for management intent
        for action, patterns in manage_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return {
                    'type': 'manage_resource',
                    'action': action,
                    'original_message': message
                }
        
        # Check for cost optimization
        if any(word in message_lower for word in ['cost', 'expensive', 'unused', 'optimize', 'save money']):
            return {
                'type': 'cost_optimization',
                'original_message': message
            }
        
        # Check for security actions
        if any(word in message_lower for word in ['security', 'public', 'access', 'permissions', 'vulnerable']):
            return {
                'type': 'security_action',
                'original_message': message
            }
        
        # Default to query
        return {
            'type': 'query_resources',
            'original_message': message
        }
    
    async def _handle_resource_creation(self, intent: Dict[str, Any], user_id: str) -> str:
        """Handle resource creation with Easy/Customize mode selection"""
        resource_type = intent['resource_type']
        
        # Ask for mode selection
        mode_question = f"""
🚀 **Creating {resource_type.upper()} Resource**

Choose your setup approach:

🟢 **EASY MODE** (30-60 seconds)
- Smart defaults based on common use cases
- Minimal questions, maximum automation
- Production-ready with best practices

🔧 **CUSTOMIZE MODE** (2-5 minutes)  
- Full control over all configurations
- Detailed questions for each setting
- Tailored to your exact requirements

Which would you prefer? (Type 'easy' or 'customize')
"""
        
        # Store pending creation in conversation state
        self.conversation_state[user_id]['pending_creation'] = {
            'resource_type': resource_type,
            'original_message': intent['original_message']
        }
        
        return mode_question
    
    async def _handle_mode_selection(self, mode: str, user_id: str) -> str:
        """Handle mode selection and proceed with resource creation"""
        pending = self.conversation_state[user_id].get('pending_creation')
        if not pending:
            return "❌ No pending resource creation found. Please start over."
        
        resource_type = pending['resource_type']
        
        if mode.lower() == 'easy':
            return await self._handle_easy_mode_creation(resource_type, user_id)
        elif mode.lower() == 'customize':
            return await self._handle_customize_mode_creation(resource_type, user_id)
        else:
            return "Please type 'easy' or 'customize' to proceed."
    
    async def _handle_easy_mode_creation(self, resource_type: str, user_id: str) -> str:
        """Handle easy mode resource creation"""
        purpose_questions = {
            'ec2': "What's the purpose of this EC2 instance? (web_server, database, development, api_server, general)",
            'lambda': "What should this Lambda function do? (image_processing, api_endpoint, data_processing, scheduled_task, general)",
            'rds': "What type of application will use this database? (ecommerce, analytics, development, production, general)",
            's3': "What will you store in this S3 bucket? (static_website, data_backup, logs, media_storage, general)"
        }
        
        question = purpose_questions.get(resource_type, "What's the purpose of this resource?")
        
        # Store the mode and resource type
        self.conversation_state[user_id]['creation_mode'] = 'easy'
        self.conversation_state[user_id]['creation_resource'] = resource_type
        
        return f"🟢 **Easy Mode Selected**\n\n{question}"
    
    async def _handle_customize_mode_creation(self, resource_type: str, user_id: str) -> str:
        """Handle customize mode resource creation"""
        customize_questions = {
            'ec2': """
🔧 **EC2 Customize Mode**

I'll ask you about each configuration option:

**1. Basic Settings:**
- Instance type? (t3.micro, t3.small, t3.medium, m5.large, etc.)
- AMI? (Amazon Linux 2, Ubuntu 20.04, Windows Server 2022)
- Key pair? (existing key name or 'create-new')

**2. Networking:**
- VPC? (default, existing VPC ID, or 'create-new')
- Subnet? (public, private, or specific subnet ID)
- Security groups? (default, web-server, or custom)

**3. Storage:**
- Root volume size? (8GB, 20GB, 100GB)
- Additional volumes? (yes/no)

**4. Advanced:**
- User data script? (yes/no)
- IAM role? (none, existing role, or 'create-new')

Let's start with the instance type. What would you like?
""",
            'lambda': """
🔧 **Lambda Customize Mode**

I'll configure each setting with you:

**1. Runtime & Performance:**
- Runtime? (python3.9, nodejs18.x, java11, dotnet6)
- Memory? (128MB - 10GB)
- Timeout? (3 seconds - 15 minutes)

**2. Code & Logic:**
- What should the function do? (describe the logic)
- Environment variables? (key=value pairs)

**3. Networking & Security:**
- VPC access? (yes/no)
- Execution role? (create-new, existing role)

**4. Triggers:**
- Event sources? (S3, API Gateway, CloudWatch Events, etc.)

Let's start with the runtime. Which would you prefer?
"""
        }
        
        # Store the mode and resource type
        self.conversation_state[user_id]['creation_mode'] = 'customize'
        self.conversation_state[user_id]['creation_resource'] = resource_type
        self.conversation_state[user_id]['customize_step'] = 1
        self.conversation_state[user_id]['customize_config'] = {}
        
        return customize_questions.get(resource_type, "Let's customize your resource step by step.")
    
    async def _execute_resource_creation(self, resource_type: str, config: Dict[str, Any], user_id: str) -> str:
        """Execute the actual resource creation via MCP"""
        try:
            tool_name = f"create_{resource_type}"
            
            # Call MCP tool
            result = await self.mcp_client.call_tool(tool_name, config)
            
            if result.get('success'):
                # Store successful creation in memory
                await self.memory_manager.store_conversation(
                    user_id, 
                    f"Created {resource_type}: {result.get('message', '')}"
                )
                
                return f"✅ {result.get('message', 'Resource created successfully!')}\n\n" + \
                       self._format_creation_summary(result)
            else:
                return f"❌ Failed to create {resource_type}: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Error creating {resource_type}: {str(e)}")
            return f"❌ Error creating {resource_type}: {str(e)}"
    
    def _format_creation_summary(self, result: Dict[str, Any]) -> str:
        """Format creation result summary"""
        summary_parts = []
        
        if 'instance_id' in result:
            summary_parts.append(f"**Instance ID:** {result['instance_id']}")
        if 'function_arn' in result:
            summary_parts.append(f"**Function ARN:** {result['function_arn']}")
        if 'db_identifier' in result:
            summary_parts.append(f"**Database:** {result['db_identifier']}")
        if 'estimated_cost' in result:
            summary_parts.append(f"**Estimated Cost:** {result['estimated_cost']}")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    async def _handle_confirmation(self, user_id: str, confirmed: bool) -> str:
        """Handle user confirmation for pending actions"""
        pending = self.conversation_state[user_id].get('pending_confirmations')
        if not pending:
            return "❌ No pending actions to confirm."
        
        if confirmed:
            # Execute the pending action
            action = pending.get('action')
            params = pending.get('params', {})
            
            # Clear pending confirmation
            self.conversation_state[user_id]['pending_confirmations'] = {}
            
            # Execute the action
            result = await self.mcp_client.call_tool(action, params)
            return f"✅ Action executed: {result.get('message', 'Completed successfully')}"
        else:
            # Cancel the action
            self.conversation_state[user_id]['pending_confirmations'] = {}
            return "❌ Action cancelled."
    
    async def _handle_general_query(self, message: str, user_id: str) -> str:
        """Handle general AWS queries"""
        try:
            result = await self.mcp_client.call_tool("comprehensive_aws_query", {
                "query": message,
                "format": "detailed",
                "include_costs": True
            })
            
            return result.get('message', 'No results found.')
            
        except Exception as e:
            logger.error(f"Error handling query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"

# FastAPI app for AgentCore Runtime
app = BedrockAgentCoreApp()
agent = EnhancedAWSAgent()

@app.message_handler
async def handle_message(message: ConversationMessage) -> str:
    """Handle incoming messages"""
    user_id = message.metadata.get('user_id', 'default')
    return await agent.process_message(message.content, user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)