def get_tools_with_triggers(action_type, available_triggers):
    tools = []
    if action_type == 'classification':
        tools =  [
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
    #############################
    # REQUIREMENT PROPOSAL STATE
    #############################
    'requirement_proposal': {
        "description": "Gather necessary information and propose a comprehensive requirement for the tool, including expected inputs and outputs.",
        "expected_behavior": """
1. Engage with the user to collect all necessary information for the tool development:
   a. Understand and articulate the primary purpose and goals of the tool
   b. Identify and list specific functionalities required
   c. Determine any constraints or preferences (e.g., programming language, performance requirements)
   d. Clarify the target users and use cases
   e. Gather any additional context or background information relevant to the tool
   f. Specify the expected inputs for the tool:
      - Data types and formats
      - Range of acceptable values
      - Any constraints or special conditions
   g. Define the expected outputs or results from the tool:
      - Data types and formats of results
      - Performance metrics or quality indicators
      - Any specific formatting or presentation requirements
   h. Propose an implementation approach or architecture
   i. Identify potential challenges and suggest mitigation strategies
   j. Estimate timeline and resources (if applicable)

2. Formulate the project proposal based on the collected information.

3. Present the comprehensive proposal to the user, asking for their feedback and confirmation.
        """,
        "action_type": "task",
        "response_format": """
1. Comprehensive Project Proposal:
   a. Tool Purpose and Objectives
   b. Required Functionalities
   c. Expected Inputs:
      - Data types and formats
      - Acceptable value ranges
      - Constraints or conditions
   d. Expected Outputs:
      - Result data types and formats
      - Performance metrics
      - Formatting requirements
   e. Proposed Implementation Approach
   f. Potential Challenges and Mitigations
   g. Timeline and Resource Estimates (if applicable)

2. Questions for User:
   [Any final clarifications needed or points for user to confirm, especially regarding inputs, outputs, and any additional context or background information relevant to the tool]
        """,
        "available_actions": ["propose_design"]
    },

    #################
    # REVIEW STATE
    #################
    'review': {
        "description": "Review the proposed design and decide to approve or refine.",
        "expected_behavior": """
Evaluate the design against the requirements and user feedback. Consider:
1. Does it meet all the requirements?
2. Is it efficient and well-structured?
3. Are there any potential issues or improvements?
4. Has the user provided any feedback, whether specific or general?

Respond ONLY with:
- 'implement_design' if the design is satisfactory and no significant improvements are needed.
- 'refine_design' if any improvements or changes are necessary, regardless of whether the user provided specific feedback or not.
        """,
        "action_type": "classification",
        "response_format": "Single word response: either 'implement_design' or 'refine_design'",
        "available_actions": ["implement_design", "refine_design"]
    },

    ###########################
    # PROPOSAL REFINEMENT STATE
    ###########################
    'proposal_refinement': {
        "description": "Refine the existing proposal based on user feedback or through self-reflection.",
        "expected_behavior": """
1. Review the previous proposal thoroughly.

2. If specific user feedback is provided:
   a. Carefully analyze and incorporate the user's feedback into the revised proposal
   b. Ensure the changes align with the overall project goals

3. If no specific user feedback is provided or additional refinement is needed:
   Conduct a comprehensive self-reflection:
   a. Analyze the proposal for completeness, clarity, consistency, feasibility, and alignment with user needs
   b. Identify areas for improvement or refinement, such as:
      - Missing or underspecified requirements
      - Overly complex or unnecessary features
      - Potential risks or challenges not previously identified
      - Opportunities for optimization or enhanced efficiency

4. Propose specific refinements or additions to improve the original proposal.

5. Ensure that any refinements maintain or enhance the overall coherence and feasibility of the project.

6. Present the refined proposal to the user, highlighting the changes and improvements made.
        """,
        "action_type": "task",
        "response_format": """
1. Summary of Original Proposal:
   [Brief recap of the key points from the original proposal]

2. Refinements Made:
   [List of significant changes, additions, or improvements]

3. Justification for Changes:
   [Explanation of how each refinement addresses user feedback or improves the proposal]

4. Updated Comprehensive Project Proposal:
   [Full refined proposal with all sections, similar to the original proposal format]

5. Questions for User:
   [Any points needing clarification or confirmation regarding the refinements]
        """,
        "available_actions": ["propose_refined_design"]
    },

    ###################################
    # SCRIPT DESIGN AND EXECUTION STATE
    ###################################
    'script_design_and_execution': {
        "description": "Design, implement, and execute the script based on the approved proposal.",
        "expected_behavior": """
1. Review the approved design and all collected information.
2. Create the actual script or code for the tool, ensuring it meets all specified requirements.
3. Include comments in the code to explain key functionality and design decisions.
4. Implement error handling and edge case management where appropriate.
5. Execute the script with appropriate test inputs.
6. Collect and document the execution results.
7. Prepare a brief explanation of how the script works, any assumptions made, and the initial execution results.
        """,
        "action_type": "task",
        "response_format": """
1. Script Implementation:
   [Provide the full script or significant code snippets]
2. Design and Implementation Notes:
   [Explain key design decisions, structures used, and any assumptions made]
3. Execution Results:
   [Summary of initial test runs and their outcomes]
4. Next Steps:
   [Recommendation for further analysis or refinement]
        """,
        "available_actions": ["analyze_script"]
    },

    #################################
    # SCRIPT EXECUTION EVALUATION STATE
    #################################
    'script_execution_evaluation': {
        "description": "Analyze the results of script execution and determine if expectations are met.",
        "expected_behavior": """
1. Review the execution results thoroughly.
2. Compare the actual outputs with the expected behavior defined in the requirements.
3. Assess if the results meet the project requirements and expectations.
4. Determine if further refinement is needed or if the script is satisfactory.

Respond ONLY with:
- 'results_met_expectations' if the script meets all requirements and performs as expected.
- 'results_not_met_expectations' if improvements or changes are necessary.
        """,
        "action_type": "classification",
        "response_format": "Single word response: either 'results_met_expectations' or 'results_not_met_expectations'",
        "available_actions": ["results_met_expectations", "results_not_met_expectations"]
    },
    ########################################
    # SCRIPT ANALYSIS AND REFINEMENT PLANNING
    ########################################
    'script_analysis_and_refinement': {
        "description": "Provide detailed analysis of script execution and plan refinements if necessary.",
        "expected_behavior": """
1. Review the execution results thoroughly.
2. Identify any discrepancies, bugs, or areas for improvement.
3. If improvements are needed:
   a. Generate specific, actionable feedback for script improvement.
   b. Prioritize areas for refinement based on their impact and the remaining iteration budget.
   c. Develop a detailed plan for implementing these refinements.
   d. If approaching maximum iterations, focus on critical changes to meet core requirements.
4. If no improvements are needed, summarize why the script meets all expectations.
        """,
        "action_type": "task",
        "response_format": """
1. Execution Analysis:
   [Detailed review of script performance, including any issues identified]

2. Evaluation of Results:
   [Assessment of whether results meet project requirements and expectations]

3. Refinement Plan (if needed):
   a. Proposed Refinements:
      [Prioritized list of specific changes or improvements]
   b. Implementation Plan:
      [Detailed steps for making the proposed refinements]
   c. Expected Outcomes:
      [Anticipated improvements after implementing the refinements]

4. Conclusion:
   [Final statement on whether the script is satisfactory or needs refinement]
        """,
        "available_actions": ["iterate", "end_iteration"], 
    },

    ##############################
    # FINALIZE SUCCESS STATE
    ##############################
    'finalize_success': {
        "description": "Conclude the tool development process after achieving satisfactory results, present to the user, and gather feedback.",
        "expected_behavior": """
1. Review the final state of the tool and its performance metrics:
   a. Confirm that all initial requirements and objectives have been met.
   b. Verify that the tool's performance meets or exceeds the defined quality thresholds.
   c. Ensure all features are working as intended.

2. Prepare a comprehensive summary of the tool's development process:
   a. Outline the initial requirements and objectives.
   b. Highlight key milestones and improvements made during the development.
   c. Present the final performance metrics and how they meet or exceed expectations.

3. Document any notable challenges overcome and solutions implemented.

4. Identify potential areas for future enhancements or optimizations.

5. Compile all necessary documentation for the tool:
   a. User manual or usage instructions.
   b. API documentation (if applicable).
   c. Known limitations or edge cases.

6. Present the comprehensive summary to the user:
   a. Highlight achievements and met criteria.
   b. Demonstrate key features and functionalities.
   c. Explain how the tool addresses the initial requirements.

7. Gather user feedback:
   a. Ask if the tool meets their expectations and requirements.
   b. Inquire about any concerns or desired changes.
   c. Discuss potential future enhancements or additional features.
        """,
        "action_type": "task",
        "response_format": """
1. Tool Development Summary:
   [Brief overview of the tool's purpose, key features, and development journey]

2. Performance Metrics:
   [Detailed breakdown of how the tool meets or exceeds expectations]

3. Key Achievements:
   [List of significant milestones or challenges overcome]

4. Documentation Overview:
   [Summary of prepared documentation and its locations]

5. User Presentation Notes:
   [Key points highlighted during the presentation to the user]

6. User Feedback:
   a. Satisfaction Level: [High/Medium/Low]
   b. Met Expectations: [Yes/Partially/No]
   c. Concerns Raised: [List any concerns mentioned by the user]
   d. Suggested Improvements: [List any improvements or changes requested by the user]

7. Future Enhancement Possibilities:
   [Potential improvements or features discussed with the user]
        """,
        "available_actions": ["provide_user_sentiment"]
    },

    ##############################
    # FINALIZE TIMEUP STATE
    ##############################
    'finalize_timeup': {
        "description": "Conclude the tool development process after reaching the maximum allowed iterations, present current state to the user, and gather feedback.",
        "expected_behavior": """
1. Conduct a thorough review of the tool's current state:
   a. Assess which initial requirements and objectives have been met.
   b. Identify any unmet requirements or partially implemented features.
   c. Evaluate the tool's current performance against the defined quality thresholds.

2. Prepare a detailed report on the development process:
   a. Recap the initial requirements and objectives.
   b. Outline the progress made through each iteration.
   c. Highlight successful implementations and remaining challenges.

3. Analyze the reasons for reaching the maximum iterations:
   a. Identify any persistent issues or challenges.
   b. Assess if the initial scope was too broad or if unforeseen complexities arose.

4. Document the current limitations of the tool:
   a. List features that are incomplete or not performing as expected.
   b. Describe any known bugs or issues.

5. Develop recommendations for moving forward:
   a. Suggest priority areas for further development if more time were allocated.
   b. Propose alternative approaches or solutions for unresolved issues.

6. Present the current state of the tool to the user:
   a. Explain the progress made and features implemented.
   b. Clearly communicate the limitations and unmet objectives.
   c. Discuss the reasons for reaching the maximum iterations.

7. Gather user feedback:
   a. Ask about their satisfaction with the current state of the tool.
   b. Discuss the impact of limitations and unmet objectives.
   c. Inquire if they want to allocate more time for development or prefer to conclude the process.
        """,
        "action_type": "task",
        "response_format": """
1. Development Status Summary:
   [Overview of the tool's current state, met and unmet objectives]

2. Iteration Analysis:
   [Breakdown of progress made and challenges faced in each iteration]

3. Current Performance Metrics:
   [Detailed assessment of the tool's performance against initial requirements]

4. Limitations and Risks:
   [List of current limitations, known issues, and potential risks]

5. User Presentation Notes:
   [Key points highlighted during the presentation to the user]

6. User Feedback:
   a. Satisfaction with Current State: [High/Medium/Low]
   b. Willingness to Continue Development: [Yes/No/Undecided]
   c. Major Concerns: [List significant concerns raised by the user]
   d. Prioritization Suggestions: [User's input on what to prioritize if development continues]

7. Impact of Limitations:
   [User's perspective on how the current limitations affect their needs]
        """,
        "available_actions": ["provide_user_sentiment"]
    },

    ##############################
    # FINAL REVIEW STATE
    ##############################
    'final_review': {
        "description": "Make the final decision on the tool's fate based on the gathered user feedback, tool state, and overall user sentiment.",
        "expected_behavior": """
Review the user feedback, tool state summary, and overall user sentiment from the previous stages. Based on this information, determine the appropriate course of action:

1. If the user sentiment is positive, the tool meets all requirements, and there are no significant requests for improvements:
   - Choose 'end_tool_crafting'

2. If the user sentiment indicates dissatisfaction, there are substantial requests for improvements, or the user agrees to allocate more time for development (in the timeup scenario):
   - Choose 'refine_tool'

3. If the user sentiment suggests a desire to abandon the tool crafting process, regardless of the reason:
   - Choose 'end_tool_crafting'

Respond ONLY with:
- 'refine_tool' if further development is needed and agreed upon.
- 'end_tool_crafting' if the process should conclude, either due to satisfaction or abandonment.
        """,
        "action_type": "classification",
        "response_format": "Single word response: either 'refine_tool' or 'end_tool_crafting'",
        "available_actions": ["refine_tool", "end_tool_crafting"]
    },

    ##############################
    # END STATE
    ##############################
    'end': {
        "description": "Conclude the tool development process and provide a comprehensive summary of the project.",
        "expected_behavior": """
1. Review the entire tool development process from start to finish:
   a. Recall the initial requirements and objectives.
   b. Summarize the key stages of development and major decisions made.
   c. Highlight significant challenges faced and how they were addressed.

2. Assess the final state of the tool:
   a. Evaluate how well the tool meets the initial requirements and objectives.
   b. List the key features and functionalities successfully implemented.
   c. Note any limitations or unresolved issues, if any.

3. Summarize the user feedback and sentiment:
   a. Recap the user's overall satisfaction with the tool.
   b. Highlight any particularly positive aspects mentioned by the user.
   c. Address how any concerns or suggestions from the user were handled.

4. Reflect on the development process:
   a. Identify key learnings and insights gained during the project.
   b. Note any best practices or effective strategies that emerged.
   c. Suggest potential improvements for future tool development processes.

5. If applicable, outline next steps or future considerations:
   a. Suggest potential areas for future enhancements or expansions of the tool.
   b. Recommend any maintenance or support considerations.
   c. Propose ideas for potential related tools or projects.

6. Provide a final statement on the project's outcome:
   a. Assess whether the project can be considered successful.
   b. Highlight the most significant achievements or innovations.
   c. Express appreciation for the user's involvement and feedback throughout the process.

7. If the tool crafting was abandoned, provide a respectful closure:
   a. Summarize the reasons for discontinuation.
   b. Highlight any valuable insights or partial achievements from the process.
   c. Suggest how the experience and learnings can be applied to future projects.
        """,
        "action_type": "task",
        "response_format": """
1. Project Overview:
   [Brief summary of the tool's purpose, initial requirements, and objectives]

2. Development Journey:
   [Key stages, major decisions, and significant challenges overcome]

3. Final Tool Assessment:
   a. Met Requirements: [List of successfully implemented features and functionalities]
   b. Limitations: [Any unresolved issues or constraints, if applicable]

4. User Feedback Summary:
   [Recap of user satisfaction, positive aspects, and how concerns were addressed]

5. Process Reflection:
   [Key learnings, best practices, and suggestions for future improvements]

6. Future Considerations:
   [Potential enhancements, maintenance needs, or related project ideas]

7. Conclusion:
   [Final statement on project success, significant achievements, and appreciation for user involvement]

8. (If Abandoned) Discontinuation Summary:
   [Reasons for abandonment, valuable insights gained, and potential applications for future projects]
        """,
        "available_actions": ["complete_project"]
    },
}

def extract_trigger(response):
    valid_triggers = [
                  'propose_design',
                  'refine_design',
                  'propose_refined_design',
                  'implement_design',
                  'eval_script',
                  'results_met_expectations',
                  'results_not_met_expectations',
                  'iterate',
                  'summarize_development',
                  'refine_tool',
                  'end_tool_crafting',
                  'new_project']
    response = response.strip().lower()
    if response in valid_triggers:
        return response
    else:
        raise ValueError(f"Invalid trigger: {response}")

      