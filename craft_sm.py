from transitions import Machine
import ollama
from sm_utils import STATE_DESCRIPTIONS_DICT, SYSTEM_MESSAGE_TEMPLATE, extract_trigger, get_tools_with_triggers

def craft_call_llm(messages, tools=[]):
    response_dict = ollama.chat(
            model='llama3.1:8b',
            messages=messages,
            options={'temperature': 0},
            tools=tools
        )
    return response_dict

class ToolCraftingProcess:
    states = [
        'requirement_proposal', 
        'review', 
        'refinement', 
        'information_collection', 
        'script_design', 
        'verification', 
        'iteration', 
        'decision_point', 
        'final_review', 
        'completion', 
        'end'
    ]

    def __init__(self):
        self.max_iterations = 5
        self.iteration_count = 0
        self.message = self.init_message()


        self.transitions = [
            {'trigger': 'propose_design', 'source': 'requirement_proposal', 'dest': 'review'},
            {'trigger': 'approve_design', 'source': 'review', 'dest': 'information_collection'},
            {'trigger': 'refine_design', 'source': 'review', 'dest': 'refinement'},
            {'trigger': 'approve_design', 'source': 'refinement', 'dest': 'information_collection'},
            {'trigger': 'refine_design', 'source': 'refinement', 'dest': 'refinement'},
            {'trigger': 'collect_information', 'source': 'information_collection', 'dest': 'script_design'},
            {'trigger': 'test_script', 'source': 'script_design', 'dest': 'verification'},
            {'trigger': 'verify_results', 'source': 'verification', 'dest': 'decision_point', 'conditions': 'results_met_expectations'},
            {'trigger': 'verify_results', 'source': 'verification', 'dest': 'iteration', 'unless': 'results_met_expectations'},
            {'trigger': 'iterate', 'source': 'iteration', 'dest': 'decision_point', 'conditions': ['results_met_expectations', 'max_iterations_reached']},
            {'trigger': 'iterate', 'source': 'iteration', 'dest': 'script_design', 'unless': 'results_met_expectations'},
            {'trigger': 'decide', 'source': 'decision_point', 'dest': 'final_review', 'conditions': 'finalize'},
            {'trigger': 'decide', 'source': 'decision_point', 'dest': 'script_design', 'unless': 'finalize'},
            {'trigger': 'approve_tool', 'source': 'final_review', 'dest': 'completion'},
            {'trigger': 'refine_tool', 'source': 'final_review', 'dest': 'iteration'},
            {'trigger': 'complete', 'source': 'completion', 'dest': 'end'},
            {'trigger': 'new_requirement', 'source': 'end', 'dest': 'requirement_proposal'}
        ]

        # Initialize the state machine
        self.machine = Machine(model=self, states=ToolCraftingProcess.states, transitions=self.transitions, initial='requirement_proposal')



    def results_met_expectations(self):
        # Check if the results meet expectations
        return True

    def max_iterations_reached(self):
        return self.iteration_count >= self.max_iterations

    def finalize(self):
        # Logic to finalize the tool
        return True

    def continue_refining(self):
        # Logic to continue refining the tool
        return True
    
    def get_state_message(self):
        return self.message
    
    def init_message(self):
        self.message = "What tool do you want to craft?"

    
    def process_interaction(self, user_message, message_history=[]):
        system_message = self.get_system_message()
        state_info = STATE_DESCRIPTIONS_DICT[self.state]
        
        # Construct messages for LLM
        messages = [
            # {"role": "system", "content": system_message}
        ]
        
        # Add history
        messages.extend(message_history)
        
        # Construct state-specific context and user message
        # state_context = f"Current state: {self.state}\nTask: {state_info['description']}\n\n"
        state_context = ""
        
        # Format the prompt if it's the iteration state
        if self.state == 'iteration':
            formatted_prompt = state_info['prompt'].format(
                iteration_count=self.iteration_count,
                max_iterations=self.max_iterations
            )
        else:
            formatted_prompt = state_info['prompt']

        tools = get_tools_with_triggers(state_info['action_type'], self.get_available_judgements())
        print(tools)
        
        full_user_message = system_message + "\n\nUser's message: " + user_message
        
        # Add the new user message with state context
        messages.append({"role": "user", "content": full_user_message})

        # Call LLM and get response
        response_dict = craft_call_llm(messages, tools)

        
        # Process the LLM's response based on the action type
        if state_info['action_type'] == 'classification':
            trigger = response_dict['tool_calls'][0]['function']['arguments']['trigger']
            trigger = extract_trigger(trigger)
            if trigger in self.get_triggers():
                # send the trigger.
                getattr(self, trigger)()
                # Need to call the function recursively to get the next system message.
                # the message history is the same while transitioning to the next state.
                return self.process_interaction(user_message, message_history)
            else:
                raise ValueError(f"Invalid decision for current state: {decision}")
        else:
            llm_response = response_dict['message']['content']
            # Process task-based states
            if self.state == 'requirement_proposal':
                self.propose_design()
            elif self.state == 'refinement':
                self.refined_design = llm_response
                self.approve_design()
            elif self.state == 'information_collection':
                self.collected_info = llm_response
                self.collect_information()
            elif self.state == 'script_design':
                self.script = llm_response
                self.test_script()
            elif self.state == 'iteration':
                self.iteration_plan = llm_response
                self.iteration_count += 1
                if self.results_met_expectations() and self.max_iterations_reached():
                    self.iterate()
                elif not self.results_met_expectations():
                    self.iterate()
                else:
                    raise ValueError("Unexpected state in iteration")
            elif self.state == 'completion':
                self.final_summary = llm_response
                self.complete()

        # Update message history
        message_history.append({"role": "assistant", "content": llm_response})
        
        return llm_response
        
    def get_triggers(self):
            state = self.state  # Get the current state of the machine
            triggers = [t['trigger'] for t in self.transitions if t['source'] == state]  # Extract triggers for the current state
            return triggers
    
    def get_system_message(self):
        available_actions = ', '.join(self.get_available_judgements())
        state_info = STATE_DESCRIPTIONS_DICT[self.state]
        
        return SYSTEM_MESSAGE_TEMPLATE.format(
            current_state=self.state,
            state_description=state_info['description'],
            available_actions=available_actions,
            action_type=state_info['action_type'],
            expected_behavior=state_info['expected_behavior'],
            response_format=state_info['response_format']
        )

    def get_state_description(self):
        return STATE_DESCRIPTIONS_DICT[self.state]['description']