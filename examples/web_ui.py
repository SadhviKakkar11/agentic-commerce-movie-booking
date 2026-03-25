"""
Interactive web interface (requires Flask server running)
Run the backend first: python -m backend.app
Then run this: python examples/web_ui.py
"""
from flask import Flask, render_template_string, request, jsonify
from agent.agent import MovieBookingAgent
import json

app = Flask(__name__)

# Store agents per user session
agents = {}

def get_agent(user_id):
    """Get or create agent for user"""
    if user_id not in agents:
        agents[user_id] = MovieBookingAgent(user_id=user_id)
    return agents[user_id]

# Simple HTML template for the web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Movie Ticket Booking Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 800px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 90vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .message.user {
            justify-content: flex-end;
        }
        .message.assistant {
            justify-content: flex-start;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 10px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 0;
        }
        .message.assistant .message-content {
            background: white;
            border: 1px solid #ddd;
            border-bottom-left-radius: 0;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #ddd;
            background: white;
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 25px;
            padding: 10px 15px;
            font-size: 14px;
            outline: none;
        }
        .input-area input:focus {
            border-color: #667eea;
        }
        .input-area button {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 10px 25px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }
        .input-area button:hover {
            background: #764ba2;
        }
        .loading {
            text-align: center;
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Movie Ticket Booking Agent</h1>
            <p>Powered by Claude AI</p>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hi! I'm your movie booking assistant. How can I help you today?
                    <br><br>
                    I can help you:
                    • Search for movies by genre or rating
                    • Find theatres in your city
                    • Check available shows and prices
                    • Book tickets for you
                </div>
            </div>
        </div>
        <div class="input-area">
            <input 
                type="text" 
                id="userInput" 
                placeholder="Type your message here..."
                autocomplete="off"
            >
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const userId = 'user_' + Math.random().toString(36).substr(2, 9);
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show loading
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant';
            loadingDiv.innerHTML = '<div class="message-content loading">Claude is thinking...</div>';
            document.getElementById('chatArea').appendChild(loadingDiv);
            document.getElementById('chatArea').scrollTop = document.getElementById('chatArea').scrollHeight;
            
            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, message: message})
            })
            .then(r => r.json())
            .then(data => {
                loadingDiv.remove();
                addMessage(data.response, 'assistant');
            })
            .catch(e => {
                loadingDiv.remove();
                addMessage('Error: ' + e, 'assistant');
            });
        }
        
        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            messageDiv.innerHTML = '<div class="message-content">' + text.replace(/\\n/g, '<br>') + '</div>';
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        document.getElementById('userInput').onkeypress = function(e) {
            if (e.key === 'Enter') sendMessage();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_id = data.get('user_id', 'user_default')
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        agent = get_agent(user_id)
        response = agent.chat(message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Web UI running on http://localhost:5001")
    print("Make sure the backend API is running on http://localhost:5000")
    app.run(debug=True, port=5001)
