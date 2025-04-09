from utils import *
from prompt import ACTION_PROMPT, CHECH_MESSAGE, gen_prompt, CHECH_USER

class PlanningAgent:
    def __init__(self, plan_client):
        self.plan_client = plan_client
        #self.plan_model = plan_client.models.list().data[0].id
        self.plan_model = 'qwen2.5-vl-72b-instruct'
        print(f"Planning model: {self.plan_model}")
        self.history = []
        self.HISTORY_CUT_OFF = 10
        
    def get_plan(self, screenshot, user):
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
        prompt = ACTION_PROMPT + f"Your task is: {gen_prompt(user)}\n\n"
        
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
    
    def group_or_single_user(self, screenshot):
        base64_image = encode_image(screenshot)
        message = get_vlm_messages(CHECH_USER, base64_image)
        completion = self.plan_client.chat.completions.create(
            model=self.plan_model,
            messages=message,
            max_tokens=512,
            temperature=0.2
        )
        output_text = completion.choices[0].message.content
        print(f"User: {output_text}")
        return output_text