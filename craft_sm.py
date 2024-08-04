from transitions import Machine
import ollama
from sm_utils import STATE_DESCRIPTIONS_DICT, SYSTEM_MESSAGE_TEMPLATE, extract_trigger, get_tools_with_triggers

def craft_call_llm(messages, tools=[]):
    response_dict = ollama.chat(
            model='llama3.1:70b',
            messages=messages,
            options={'temperature': 0},
            tools=tools
        )
    return response_dict

class ToolCraftingProcess:
    states = [
        'requirement_proposal',  # Includes information collection
        'review', 
        'proposal_refinement',
        'script_design_and_execution',
        'script_execution_evaluation',
        'script_analysis_and_refinement',
        'finalize_success',
        'finalize_timeup',
        'final_review',
        'end'
    ]

    def __init__(self):
        self.max_iterations = 5
        self.iteration_count = 0
        self.message = self.init_message()

        self.transitions = [
            {'trigger': 'propose_design', 'source': 'requirement_proposal', 'dest': 'review'},
            {'trigger': 'refine_design', 'source': 'review', 'dest': 'proposal_refinement'}, 
            {'trigger': 'propose_refined_design', 'source': 'proposal_refinement', 'dest': 'review'}, 
            {'trigger': 'implement_design', 'source': 'review', 'dest': 'script_design_and_execution'},
            {'trigger': 'eval_script', 'source': 'script_design_and_execution', 'dest': 'script_execution_evaluation'},
            {'trigger': 'results_met_expectations', 'source': 'script_execution_evaluation', 'dest': 'finalize_success'},
            {'trigger': 'results_not_met_expectations', 'source': 'script_execution_evaluation', 'dest': 'script_analysis_and_refinement'},
            {'trigger': 'iterate', 'source': 'script_analysis_and_refinement', 'dest': 'finalize_timeup', 'conditions': 'max_iterations_reached'},
            {'trigger': 'iterate', 'source': 'script_analysis_and_refinement', 'dest': 'script_design_and_execution', 'unless': 'max_iterations_reached'},
            {'trigger': 'summarize_development', 'source': 'finalize_success', 'dest': 'final_review'},
            {'trigger': 'summarize_development', 'source': 'finalize_timeup', 'dest': 'final_review'},
            {'trigger': 'refine_tool', 'source': 'final_review', 'dest': 'script_design_and_execution'},
            {'trigger': 'end_tool_crafting', 'source': 'final_review', 'dest': 'end'},
            {'trigger': 'new_project', 'source': 'end', 'dest': 'requirement_proposal'}
        ]

        # Initialize the state machine
        self.machine = Machine(model=self, states=ToolCraftingProcess.states, transitions=self.transitions, initial='requirement_proposal')
        
        self.evaluation_status = 'result_met_expectations'



    def is_timeup_or_satisfactory(self):
        # Check if the results meet expectations
        return self.evaluation_status == 'result_met_expectations' or self.iteration_count >= self.max_iterations

    def max_iterations_reached(self):
        return self.iteration_count >= self.max_iterations

    def clear_iteration_count(self):
        self.iteration_count = 0

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

    
    def extract_and_save_scripts(self, llm_response):
        # Extract the scripts from the LLM response.
        # Save the scripts.
        # Return the scripts.
        pass
        return "The scripts", "The execution commands"
    
    def execute_scripts(self, execution_commands):
        # Execute the scripts.
        # Return the outcome.
        return "The execution's results: Beijing's temperature is 35 celcicus degree."

    
    def process_interaction(self, user_message, message_history=[]):
        system_message = self.get_system_message()
        state_info = STATE_DESCRIPTIONS_DICT[self.state]
        
        # Construct messages for LLM
        messages = [{"role": "system", "content": system_message}]
        
        # Add history
        messages.extend(message_history)
        
        tools = get_tools_with_triggers(state_info['action_type'], self.get_triggers())
        print(tools)

        # "\n\nUser's message: " + 
        full_user_message = user_message
        
        # Add the new user message with state context
        messages.append({"role": "user", "content": full_user_message})

        # Call LLM and get response
        response_dict = craft_call_llm(messages, tools)

        # Process the LLM's response based on the action type
        if state_info['action_type'] == 'classification':
            trigger = response_dict['message']['tool_calls'][0]['function']['arguments']['trigger']
            trigger = extract_trigger(trigger)
            if trigger in self.get_triggers():
                # Execute the trigger
                print(self.state, trigger)
                getattr(self, trigger)()
                # Recursively call to get the next system message
                # If it is a classification task, the user_message will be passed to the next stage.
                # For example, the feedback to the refinement.
                return self.process_interaction(user_message, message_history)
            else:
                raise ValueError(f"Invalid trigger for current state: {trigger}")
        else:  # action_type is 'task'
            llm_response = response_dict['message']['content']
            print("###################################", self.state, llm_response)

            # Update message history
            # The message history is only updated during 'task' action_type
            message_history.append({"role": "user", "content": full_user_message})
            message_history.append({"role": "assistant", "content": llm_response})
                
            # Process task-based states
            if self.state == 'requirement_proposal':
                self.propose_design()
            elif self.state == 'proposal_refinement':
                self.propose_refined_design()
            elif self.state == 'script_design_and_execution':
                self.iteration_count += 1
                # This will return the design.
                scripts, execution_commands = self.extract_and_save_scripts(llm_response)
                # This will execute the codes.
                execution_outcome = self.execute_scripts(execution_commands)
                # This will enter the scrip_execution_evaluation state, and no need to return to the user.
                self.eval_script()
                # This will enter the evaluation to decide the next state.
                return self.process_interaction(execution_outcome, message_history)
            elif self.state == 'script_analysis_and_refinement':
                # This stage will make analysis based on the exection outcome followed by the evaluation state.
                self.iterate()
            elif self.state == 'finalize_success' or self.state == 'finalize_timeup':
                # This state presents the user the summary of the experiment.
                # Will go to the final review stage to see the user's sentiment based on the summary.
                self.clear_iteration_count()
                self.summarize_development()
            elif self.state == 'end':
                # This state is handled by classification, but included for completeness
                pass
            else:
                raise ValueError(f"Unexpected state: {self.state}")
        
        return llm_response
        
    def get_triggers(self):
            state = self.state  # Get the current state of the machine
            triggers = [t['trigger'] for t in self.transitions if t['source'] == state]  # Extract triggers for the current state
            return triggers
    
    def get_system_message(self):
        available_actions = ', '.join(self.get_triggers())
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