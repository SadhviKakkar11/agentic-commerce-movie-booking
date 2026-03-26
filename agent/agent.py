"""
Main Claude agent for movie ticket booking
Supports both direct Anthropic API and AWS Bedrock
"""
import anthropic
import boto3
import json
from datetime import datetime
from .config import (
    USE_BEDROCK, ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    AWS_REGION, BEDROCK_MODEL_ID, DEBUG
)
from .tools import TOOLS, process_tool_call
from .prompts import SYSTEM_PROMPT


class MovieBookingAgent:
    """Main agent for movie ticket booking"""
    
    def __init__(self, user_id="user_123"):
        """Initialize the agent"""
        self.user_id = user_id
        self.conversation_history = []
        # Inject today's date so Claude can correctly resolve "this Sunday", "tomorrow", etc.
        today = datetime.now()
        date_context = (
            f"\nTODAY'S DATE: {today.strftime('%A, %Y-%m-%d')} (use this to resolve relative dates like 'this Sunday', 'tomorrow', etc.)\n"
        )
        self.system_prompt = date_context + SYSTEM_PROMPT
        
        # Initialize API client
        if USE_BEDROCK:
            self._init_bedrock()
        else:
            self._init_anthropic()
    
    def _init_anthropic(self):
        """Initialize Anthropic API client"""
        self.client_type = "anthropic"
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL
        if DEBUG:
            print(f"✅ Initialized Anthropic client with model: {self.model}")
    
    def _init_bedrock(self):
        """Initialize AWS Bedrock client"""
        self.client_type = "bedrock"
        self.client = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        self.model = BEDROCK_MODEL_ID
        if DEBUG:
            print(f"✅ Initialized Bedrock client with model: {self.model}")
    
    def chat(self, user_message):
        """
        Send a message to Claude and get a response
        Handles tool use automatically
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if DEBUG:
            print(f"\n📝 User: {user_message}")
        
        # Get response from Claude
        response = self._get_claude_response()
        
        # Process the response (handle tool calls)
        while self._should_handle_tool_use(response):
            response = self._handle_tool_use(response)
        
        # Extract the final text response
        final_response = self._extract_text_response(response)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response
    
    def _get_claude_response(self):
        """Get response from Claude API or Bedrock"""
        if self.client_type == "anthropic":
            return self._get_anthropic_response()
        else:
            return self._get_bedrock_response()
    
    def _get_anthropic_response(self):
        """Get response from direct Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            tools=TOOLS,
            messages=self.conversation_history
        )
        return response
    
    def _get_bedrock_response(self):
        """Get response from AWS Bedrock"""
        # Format message for Bedrock
        messages = self.conversation_history.copy()
        
        system_prompt_obj = {
            "type": "text",
            "text": self.system_prompt
        }
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": [system_prompt_obj],
            "tools": TOOLS,
            "messages": messages
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model,
                body=json.dumps(request_body)
            )
            
            # Parse Bedrock response
            response_body = json.loads(response['body'].read())
            return response_body
        except Exception as e:
            print(f"❌ Bedrock API Error: {e}")
            raise
    
    def _should_handle_tool_use(self, response):
        """Check if response contains tool use"""
        if self.client_type == "anthropic":
            return hasattr(response, 'stop_reason') and response.stop_reason == "tool_use"
        else:
            # Bedrock format
            return any(block.get('type') == 'tool_use' for block in response.get('content', []))
    
    def _handle_tool_use(self, response):
        """Handle tool use in Claude's response"""
        tool_results = []
        
        # Extract tool calls from response
        tool_calls = self._extract_tool_calls(response)
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_input = tool_call['input']
            tool_use_id = tool_call['id']
            
            if DEBUG:
                print(f"\n🔧 Calling tool: {tool_name}")
                print(f"   Input: {json.dumps(tool_input, indent=2)[:200]}...")
            
            # Execute the tool
            tool_result = process_tool_call(tool_name, tool_input)
            
            if DEBUG:
                print(f"   Result: {json.dumps(tool_result, indent=2)[:200]}...")
            
            if self.client_type == "anthropic":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(tool_result)
                })
            else:
                # Bedrock format
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(tool_result)
                })
        
        # Add assistant message and tool results to history
        if self.client_type == "anthropic":
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
        else:
            self.conversation_history.append({
                "role": "assistant",
                "content": response.get('content', [])
            })
        
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })
        
        # Get next response from Claude
        return self._get_claude_response()
    
    def _extract_tool_calls(self, response):
        """Extract tool calls from response based on API type"""
        tool_calls = []
        
        if self.client_type == "anthropic":
            for block in response.content:
                if hasattr(block, 'type') and block.type == "tool_use":
                    tool_calls.append({
                        'id': block.id,
                        'name': block.name,
                        'input': block.input
                    })
        else:
            # Bedrock format
            for block in response.get('content', []):
                if block.get('type') == 'tool_use':
                    tool_calls.append({
                        'id': block.get('id'),
                        'name': block.get('name'),
                        'input': block.get('input')
                    })
        
        return tool_calls
    
    def _extract_text_response(self, response):
        """Extract text content from Claude's response"""
        if self.client_type == "anthropic":
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
        else:
            # Bedrock format
            for block in response.get('content', []):
                if block.get('type') == 'text':
                    return block.get('text', '')
        
        return "No response generated"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self):
        """Get conversation history"""
        return self.conversation_history


def run_agent_loop(user_id="user_123"):
    """Run an interactive agent loop for testing"""
    agent = MovieBookingAgent(user_id=user_id)
    
    print("🎬 Movie Ticket Booking Agent")
    print("=" * 50)
    print(f"API Provider: {'AWS Bedrock' if USE_BEDROCK else 'Direct Anthropic API'}")
    print("Type 'exit' to quit, 'clear' to clear history")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("History cleared")
                continue
            
            print("\n🤖 Claude:", end=" ", flush=True)
            response = agent.chat(user_input)
            print(response)
        
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            continue


if __name__ == "__main__":
    run_agent_loop()
