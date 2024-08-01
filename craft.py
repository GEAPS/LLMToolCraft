from flask import Blueprint, request, jsonify, session
from collections import defaultdict
from craft_sm import ToolCraftingProcess
import subprocess
import time

def create_craft_blueprint(app, socketio):
    craft_bp = Blueprint('craft', __name__)

    tool_crafting_histories = defaultdict(list)
    tool_processes = {}

    @craft_bp.before_request
    def initialize_tool_process():
        session_id = session.get('session')
        if session_id not in tool_processes:
            tool_processes[session_id] = ToolCraftingProcess()

    @craft_bp.route('/craft-tools', methods=['POST'])
    def craft_tools():
        session_id = session['session']
        user_message = request.json.get('prompt')
        
        if session_id not in tool_processes:
            tool_processes[session_id] = ToolCraftingProcess()
        
        process = tool_processes[session_id]
        
        def generate_tool_response():
            with app.app_context():
                llm_response = process.process_interaction(user_message, message_history=tool_crafting_histories[session_id])
                # llm_response = "Hello World"
                time.sleep(0.5)
                state_description = process.get_state_description()
                socketio.emit('tool_response', {'response': llm_response, 'state': state_description})
        
        socketio.start_background_task(generate_tool_response)
        return jsonify({'response': "Processing...", 'state': 'crafting'})

    @craft_bp.route('/execute-script', methods=['POST'])
    def execute_script():
        session_id = session['session']
        script = request.json.get('script')
        
        process = tool_processes[session_id]
        
        tool_crafting_histories[session_id].append({'role': 'user', 'content': script})
        
        def execute_script_response():
            with app.app_context():
                try:
                    result = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
                    execution_result = result.stdout if result.returncode == 0 else result.stderr
                    
                    tool_crafting_histories[session_id].append({'role': 'assistant', 'content': execution_result})
                    
                    process.test_script()
                    
                    state_message = get_current_state_message(process)
                    socketio.emit('execution_response', {'result': execution_result, 'state': state_message})
                except Exception as e:
                    error_message = str(e)
                    
                    tool_crafting_histories[session_id].append({'role': 'assistant', 'content': error_message})
                    
                    state_message = get_current_state_message(process)
                    socketio.emit('execution_response', {'result': error_message, 'state': state_message})
        
        socketio.start_background_task(execute_script_response)
        return jsonify({'status': 'executing'})

    @craft_bp.route('/clear_craft_history', methods=['POST'])
    def clear_history():
        session_id = session['session']
        if session_id in tool_crafting_histories:
            del tool_crafting_histories[session_id]
        if session_id in tool_processes:
            del tool_processes[session_id]
        print("hello world")
        return jsonify({'status': 'success'})

    def get_current_state_message(process):
        # Implement this function to get the current state message
        return "Current State"  # Placeholder

    return craft_bp