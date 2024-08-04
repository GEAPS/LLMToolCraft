from flask import Flask, request, render_template, jsonify, session
from flask_socketio import SocketIO, emit
from collections import deque, defaultdict
import ollama
import uuid

from craft import create_craft_blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace 'your_secret_key' with a secure key
socketio = SocketIO(app, ping_interval=25000, ping_timeout=60000)
craft_bp = create_craft_blueprint(app, socketio)
app.register_blueprint(craft_bp, url_prefix='/craft')

clipboard_queue = deque(maxlen=5)
chat_histories = defaultdict(list)  # Store chat histories

@app.before_request
def ensure_session():
    if 'session' not in session:
        session['session'] = str(uuid.uuid4())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    session_id = session['session']  # Use the session cookie to identify users
    prompt = request.form['prompt']
    
    # Replace placeholders with actual clipboard content
    for i in range(len(clipboard_queue)):
        prompt = prompt.replace(f'\\clipboard+{i+1}', clipboard_queue[-(i+1)])
    
    # Add the user prompt to the chat history
    chat_histories[session_id].append({'role': 'user', 'content': prompt})
    
    # Start streaming the response from the local model
    def generate_response():
        messages = chat_histories[session_id]  # Use the chat history
        stream = ollama.chat(
            model='codellama:13b',
            messages=messages,
            stream=True,
            options={'temperature': 0}
        )
        
        response_chunks = []
        for chunk in stream:
            content = chunk['message']['content']
            response_chunks.append(content)
            print(content)
            socketio.emit('response_chunk', {'chunk': content})
        
        # Combine all response chunks into a single response
        full_response = ''.join(response_chunks)
        
        # Update chat history with unified AI response
        chat_histories[session_id].append({'role': 'assistant', 'content': full_response})
        # print(full_response)
        socketio.emit('response_complete')

    socketio.start_background_task(generate_response)
    return jsonify({'status': 'streaming'})

@app.route('/add_text', methods=['POST'])
def add_text():
    text = request.form['text']
    clipboard_queue.append(text)
    socketio.emit('update_clipboard', list(clipboard_queue))
    return jsonify({'status': 'success'})

@app.route('/clear_queue', methods=['POST'])
def clear_queue():
    clipboard_queue.clear()
    socketio.emit('update_clipboard', list(clipboard_queue))
    return jsonify({'status': 'success'})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session_id = session['session']
    if session_id in chat_histories:
        del chat_histories[session_id]
    return jsonify({'status': 'success'})



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
