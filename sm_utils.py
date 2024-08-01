
SYSTEM_MESSAGE_TEMPLATE = """
You are part of a tool development process managed by a state machine. Your role is to assist in developing a tool based on user requirements. Follow these guidelines and adhere to the response format strictly:

Current State: {current_state}
State Description: {state_description}

Available Actions: {available_actions}

Action Type: {action_type}
Required Action:
- If action_type is 'task': Perform the task described in the Expected Behavior.
- If action_type is 'classification': Respond ONLY with one of the Available Actions. DO NOT FORGET the underscore. Do not include any explanation.

Expected Behavior:
{expected_behavior}

Response Format:
{response_format}
"""

STATE_DESCRIPTIONS_DICT = {
    'requirement_proposal': {
        "description": "Propose a clear and detailed requirement for the tool.",
        "expected_behavior": "Based on the user's request, propose specific functionalities and any constraints or preferences mentioned by the user.",
        "action_type": "task",
        "response_format": "Free-form response detailing the proposed requirements.",
        "prompt": "Based on the user's request, please propose a clear and detailed requirement for the tool. Include specific functionalities and any constraints or preferences mentioned by the user.",
        "available_actions": []
    },
    'review': {
        "description": "Review the proposed design and decide to approve or refine.",
        "expected_behavior": "Evaluate the design against the requirements. Decide if it's satisfactory or needs refinement.",
        "action_type": "classification",
        "response_format": "Respond ONLY with either 'approve_design' or 'refine_design'.",
        "prompt": "Review the proposed design. Consider the following:\n1. Does it meet all the requirements?\n2. Is it efficient and well-structured?\n3. Are there any potential issues or improvements?\nRespond ONLY with 'approve_design' if satisfied or 'refine_design' if changes are needed.",
        "available_actions": ["approve_design", "refine_design"]
    },
    'refinement': {
        "description": "Refine the design based on feedback.",
        "expected_behavior": "Address the points mentioned in the feedback and make necessary improvements to the design.",
        "action_type": "task",
        "response_format": "Free-form response detailing the refined design.",
        "prompt": "Based on the previous feedback, please refine the design. Address all the points mentioned and make any necessary improvements. Provide a detailed explanation of the changes made.",
        "available_actions": []
    },
    'information_collection': {
        "description": "Collect necessary details from the user.",
        "expected_behavior": "Identify and ask for any additional information needed to implement the tool.",
        "action_type": "task",
        "response_format": "List of specific questions or requests for information.",
        "prompt": "We need to gather all necessary information to implement the tool. What additional details do we need from the user? List specific questions or requests for information.",
        "available_actions": []
    },
    'script_design': {
        "description": "Design the script and prepare for testing.",
        "expected_behavior": "Create the actual script or code for the tool based on the approved design and collected information.",
        "action_type": "task",
        "response_format": "Complete, working implementation of the script or code.",
        "prompt": "Using the approved design and collected information, create the actual script or code for the tool. Provide a complete, working implementation.",
        "available_actions": []
    },
    'verification': {
        "description": "Verify the results of the script.",
        "expected_behavior": "Analyze the script's performance against expected outcomes. Provide a detailed analysis including any test cases used.",
        "action_type": "classification",
        "response_format": "Respond ONLY with either 'verify_results' or 'iterate'.",
        "prompt": "Verify the results of the script. Does it meet the expected outcomes? Consider performance and any test cases used. Respond ONLY with 'verify_results' if it meets expectations or 'iterate' if improvements are needed.",
        "available_actions": ["verify_results", "iterate"]
    },
    'iteration': {
        "description": "Iterate on the design if results do not meet expectations.",
        "expected_behavior": "Based on the verification results, propose specific changes or improvements to the script.",
        "action_type": "task",
        "response_format": "Detailed plan for this iteration, including specific changes to be made.",
        "prompt": """This is iteration {iteration_count} out of {max_iterations}. 

                Based on the previous verification results, what specific changes or improvements should be made to the script? Provide a detailed plan for this iteration. 

                Remember:
                1. Maintain the same high standard of suggestions regardless of the iteration number.
                2. Focus on the most impactful improvements that will bring the tool closer to meeting all requirements.
                3. If we're approaching the maximum iterations, consider prioritizing critical changes, but do not compromise on quality or completeness.

                Please provide a comprehensive and detailed plan for this iteration:""",
        "available_actions": []
    },
    'decision_point': {
        "description": "Decide whether to finalize the tool or continue refining.",
        "expected_behavior": "Analyze the current state of the tool, considering if it meets initial requirements and if further improvements would significantly enhance functionality.",
        "action_type": "classification",
        "response_format": "Respond ONLY with either 'decide' or 'iterate'.",
        "prompt": "We've reached a decision point. Analyze the current state of the tool:\n1. Does it fully meet the initial requirements?\n2. Are there any outstanding issues?\n3. Could further improvements significantly enhance its functionality?\nRespond ONLY with 'decide' to finalize the tool or 'iterate' to continue refining.",
        "available_actions": ["decide", "iterate"]
    },
    'final_review': {
        "description": "Conduct a final review of the tool with the user.",
        "expected_behavior": "Provide a comprehensive summary of the tool, including how it meets requirements, key features, limitations, and usage instructions.",
        "action_type": "classification",
        "response_format": "Respond ONLY with either 'approve_tool' or 'refine_tool'.",
        "prompt": "Conduct a final review of the tool. Consider:\n1. How well it meets the initial requirements\n2. Key features and functionalities\n3. Any limitations or potential future improvements\n4. Instructions for use\nRespond ONLY with 'approve_tool' if satisfied or 'refine_tool' if any final changes are needed.",
        "available_actions": ["approve_tool", "refine_tool"]
    },
    'completion': {
        "description": "Finalize the tool creation and move to completion.",
        "expected_behavior": "Provide a final summary of the tool, including its purpose, key features, usage instructions, and any important notes for the user.",
        "action_type": "task",
        "response_format": "Comprehensive final summary of the completed tool.",
        "prompt": "The tool creation process is complete. Provide a final summary of the tool, including its purpose, key features, usage instructions, and any important notes for the user. Confirm that the tool is ready for use.",
        "available_actions": []
    },
    'end': {
        "description": "The process is finished.",
        "expected_behavior": "Confirm the end of the tool crafting process and inquire if the user wants to start a new process or discuss the completed tool.",
        "action_type": "classification",
        "response_format": "Respond ONLY with either 'new_requirement' or 'end'.",
        "prompt": "The tool crafting process has ended. Would you like to start a new tool creation process or end the session? Respond ONLY with 'new_requirement' to start a new process or 'end' to finish.",
        "available_actions": ["new_requirement", "end"]
    }
}

def extract_decision(response):
    valid_decisions = [
        'approve_design', 'refine_design', 'verify_results', 'iterate', 
        'decide', 'approve_tool', 'refine_tool', 'new_requirement', 'end'
    ]
    response = response.strip().lower()
    if response in valid_decisions:
        return response
    else:
        raise ValueError(f"Invalid decision: {response}")