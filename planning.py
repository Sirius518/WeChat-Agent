from utils import *
from prompt import ACTION_PROMPT, CHECH_MESSAGE

class PlanningAgent:
    def __init__(self, plan_client):
        self.plan_client = plan_client
        #self.plan_model = plan_client.models.list().data[0].id
        self.plan_model = 'qwen2.5-vl-72b-instruct'
        print(f"Planning model: {self.plan_model}")
        self.history = []
        self.HISTORY_CUT_OFF = 10
        
    def get_plan(self, screenshot, user):
        """
        get the next plan
        Args:
            screenshot: the screenshot
            task_description: task description
            retry_click_elements: the list of elements that failed to click before
        Returns:
            plan_str: plan description
            action_str: specific action
        """
        instruction = self.get_plan_instruction(user)
                
        base64_image = encode_image(screenshot)
        messages = get_vlm_messages(instruction, base64_image)
        completion = self.plan_client.chat.completions.create(
            model=self.plan_model,
            messages=messages,
            max_tokens=512,
            temperature=0.2
        )
        output_text = completion.choices[0].message.content
        return self.split_output(output_text)
    
    def check_message(self, screenshot):
        base64_image = encode_image(screenshot)
        message = get_vlm_messages(CHECH_MESSAGE, base64_image)
        completion = self.plan_client.chat.completions.create(
            model=self.plan_model,
            messages=message,
            max_tokens=512,
            temperature=0.2
        )
        output_text = completion.choices[0].message.content
        return output_text
    
    def add_to_history(self, output):
        """
        add the output to the history
        """
        plan, action = self.split_output(output)
        if "finish" in action:
            self.history = []
        else:
            self.history.append(output)
        print(f"History: {self.history}")

    def get_plan_instruction(self, user):
        """
        generate the planning instruction
        """
        prompt = ACTION_PROMPT + f"Your task is: {self.gen_prompt(user)}\n\n"
        
        if len(self.history) > self.HISTORY_CUT_OFF:
            history_str = "\n\n".join(f"[{i+1}] {item}" for i, item in enumerate(self.history[-self.HISTORY_CUT_OFF:]))
        else:
            history_str = "\n\n".join(f"[{i+1}] {item}" for i, item in enumerate(self.history))
            
        if history_str == '':
            history_str = "None"
            
        prompt += f"History of the previous actions you have done: {history_str}\n\n"
        prompt += "--------------------------------------------\n\n"
        prompt += f"Given the screenshot. What's the next step that you will do follow the action sequence?\n\n"
        return prompt
    
    def split_output(self, output):
        """
        split the output into plan and action
        """
        plan_str = output.split("Action:")[0].strip()
        action_str = output.split("Action:")[1].strip()
        return plan_str, action_str

    def gen_prompt(self, user):
        return f'''Respond to {user} messages within the interface. User messages appear in white boxes, while your responses will be displayed in green boxes.

## Action Sequence
1. Locate and **click** on {user}'s profile that has a red notification dot.
2. Extract all recent user messages (all content in white boxes) that appear after the LAST green box.
3. Compile these messages into a single query and **throw** it.
4. Send the response to the user.
5. **Finish** the task.

## Important Guidelines
- Messages on screen typically alternate between white boxes (user) and green boxes (responses).
- Only extract and process white box messages that appear AFTER the most recent green box.
- If multiple unread white box messages exist after the last green box, combine them into one comprehensive query.
- Maintain the same language used by the user in your compiled query.
- Ignore any content in green boxes or white boxes that appear before the last green box.'''