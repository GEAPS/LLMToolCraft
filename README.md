# LLMToolCraft

This project is part of the [Pervasive AI Developer Contest](https://www.hackster.io/contests/amd2023). It is actively maintained. 

**For the version prior to the submission deadline, please visit the `old` branch.**

## How to Run

### Clipboard Setup

To set up the Clipboard Queue shortcut in Ubuntu:

1. Go to System > Keyboard > View and Customize Shortcuts > Custom Shortcuts
2. Create a new shortcut with the following details:
   - Name: Clipboard Queue
   - Command: `/path/to/the/project/scripts/capture_and_send.sh`
   - Shortcut: `Alt+Q`

This enables sending selected content to the Flask App and storing it in a Python queue whenever you press `Alt+Q`.

### Launch the Web App
To start the application, run:

```bash
python run.py
```

It will run at `http://127.0.0.1:8000` by default.

## Basic Interaction with LLM

- Type `\clipboard+id` to select an item from the clipboard with the specified id.
- Use "Generate Response" to submit the query.
- "Switch to Detailed View" provides a comprehensive view.
- In Detailed View, the agent can edit each clipboard item, which updates the clipboard.

For a demonstration of basic interaction, watch this video:

[![LLMToolCraft Basic Interaction Demo](https://img.youtube.com/vi/knIjH0ysjV8/0.jpg)](https://www.youtube.com/watch?v=knIjH0ysjV8 "LLMToolCraft Basic Interaction Demo")

## Tool Craft

A state machine guides the agent through a flowchart, ensuring the LLM follows the correct procedure to craft tools. This process can be enhanced with more powerful LLMs for smoother state transitions.

### State Machine Design [Updated]

1. **Requirement Proposal** (A): The process begins with the user proposing requirements for the tool.

2. **Review** (B): The proposal is reviewed.
   - If refinement is needed: Move to Proposal Refinement (C)
   - If approved: Proceed to Script Design and Execution (D)

3. **Proposal Refinement** (C): The initial proposal is refined based on feedback.
   - After refinement: Return to Review (B)

4. **Script Design and Execution** (D): The script is designed and executed based on the approved proposal.

5. **Execution Evaluation** (E): The results of the script execution are evaluated.
   - If results met expectations: Move to Finalize Success (F)
   - If results did not meet expectations: Move to Script Analysis and Refinement (G)

6. **Script Analysis and Refinement** (G): The script is analyzed and refined based on the evaluation.
   - If max iterations not reached: Return to Script Design and Execution (D)
   - If max iterations reached: Move to Finalize Timeup (H)

7. **Finalize Success** (F) or **Finalize Timeup** (H): The process is finalized based on whether expectations were met or max iterations were reached.

8. **Final Review** (I): A final review of the tool is conducted.
   - If refinement is needed: Return to Script Design and Execution (D)
   - If approved: Move to End (J)

9. **End** (J): The tool crafting process is completed.
   - To start a new project: Return to Requirement Proposal (A)

Note: The green color of the Requirement Proposal (A) indicates the start of the process, while the red color of the End (J) signifies the completion of the process.

### State Machine Flowchart

```mermaid
flowchart TD
    A[Requirement Proposal]:::startState --> B{Review}
    B -->|Needs Refinement| C[Proposal Refinement]
    C --> B
    B -->|Approved| D[Script Design Execution]
    D --> E{Execution<br>Evaluation}
    E -->|Met Expectations| F[Finalize Success]
    E -->|Not Met| G{Script Analysis <br>& Refinement}
    G -->|Max Iterations Not Reached| D
    G -->|Max Iterations Reached| H[Finalize Timeup]
    F --> I{Final Review}
    H --> I
    I -->|Needs Refinement| D
    I -->|Approved| J[End]:::endState
    J -->|New Project| A
    classDef startState fill:#9f6,stroke:#333,stroke-width:2px;
    classDef endState fill:#f66,stroke:#333,stroke-width:2px;
```

### States And Triggers
The state machine is implemented in `craft_sm.py` and `sm_utils.py`. The states are encoded as 10 different ones:

1. requirement_proposal
2. review 
3. proposal_refinement
4. script_design_and_execution
5. script_execution_evaluation
6. script_analysis_and_refinement
7. finalize_success
8. finalize_timeup
9. final_review
10. end


The action type in each state can be classified into two types: `task` and `classification`. The state of `task` needs to perform certain task by the LLM while the `classification` task needs to decide the trigger from a limited set which is available to the current state. Each trigger corresponds to an individual transition among states. 

To predict one of the exact trigger from the given set, we leverage the [new feature](https://ollama.com/blog/tool-support) of ollama to make use of `tool` to make a function call to treat triggers as enum type parameter for the agent to send to a virtual function called `send_trigger`. The tool is crafted as:

```python
def get_tools_with_triggers(action_type, available_triggers):
    tools = []
    if action_type == 'classification':
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "send_trigger",
                    "description": "Send the trigger to the state machine.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trigger": {
                                "type": "string",
                                "description": f"The trigger to send. Possible values are: {', '.join(map(str, available_triggers))}",
                                "enum": available_triggers
                            }
                        },
                        "required": ["trigger"]
                    }
                }
            }
        ]
    return tools
```

Then the `tools` are passed as a parameter to the `ollama.chat`, it will make the classification task by output the parameter in `response_dict['tool_calls'][0]['function']['arguments']['trigger']` where `response_dict` is returned by `ollama.chat`.

## Features to Add

1. **Prompt Engineering Improvements**: Refine the system messages for each state to better achieve the expected effects.

2. **Enhanced Script Testing Interaction**: Improve the interaction process during the script testing phase.

3. **Database Integration**: Establish a proper connection to MariaDB for efficient data management.

4. **Tool Classification System**: Implement a classification system for crafted tools, categorizing them into:
   - Prompt tools
   - Script tools
   - System tools