from utils import *
import pyautogui
import pyperclip
import time
import re
import os

MAX_ACTION_CNT = 50
PLANNING_MAX_RETRY = 3
TARGET_WIDTH = 1280 
TARGET_HEIGHT = 720
# 1280x720



class PCAgent:
    def __init__(self, planning_agent, grounding_agent, task_description, output_queue=None):
        self.planning_agent = planning_agent
        self.grounding_agent = grounding_agent
        self.task_description = task_description
        self.output_queue = output_queue
        self.retry_click_elements = []
        self.step_cnt = 0
        screenshot = get_screenshot()
        self.window_width = screenshot.width
        self.window_height = screenshot.height

        # set record directory
        file_path = os.path.dirname(os.path.abspath(__file__))
        directory_name = f"inference_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
        self.directory_path = os.path.join(file_path, 'record', directory_name)
        os.makedirs(self.directory_path, exist_ok=True)

    def run(self):
        try:
            while True:
                screenshot = get_screenshot()
                user_to_reply = self.if_new_message(screenshot)
                print("action:", user_to_reply)
                if user_to_reply:
                    self.execute_action(user_to_reply)
                    output = f"check message agent\nAction: {user_to_reply}"
                    self.after_action(output)

                    group_or_single = self.check_user(screenshot)
                    print("user:", group_or_single)
                    self.reply_message(screenshot, group_or_single)

                else:
                    time.sleep(2)  # sleep for 5 minutes

        except Exception as e:
            print(f"Error: {e}")
            self.exit(1)

    def check_user(self, screenshot):
        check_user = self.planning_agent.group_or_single_user(screenshot)
        if 'group' in check_user:
            return True
        else:
            return False

    def if_new_message(self, screenshot):
        if_message = self.planning_agent.check_message(screenshot)
        if 'None' in if_message:
            return False
        else:
            return if_message.strip('"').strip(" ")
        
    def reply_message(self, screenshot, user):
        try:
            while True:
                time.sleep(2)
                screenshot = get_screenshot()
                output, screenshot= self.step(screenshot, user)
                self.record(output, screenshot)
                
                action = output.split("Action: ")[-1].strip()
                if 'finish' in action:  # 在循环内部检查终止条件
                    break
                    
        except Exception as e:
            print(f"Error: {e}")
            self.exit(1)
        


    def step(self, screenshot, user):
        plan, action = self.planning_agent.get_plan(screenshot, user)
        
        if "throw query:" in action:
            # call response agent to answer
            query = action.split("throw query:")[1].strip()
            response = self.grounding_agent.call_grounding(query)
            self.add_success_block(plan, action)
            output = f"{plan}\nAction: {action}"
            self.planning_agent.add_to_history(output)
            self.after_action(output)
            
            action = "send text: " + response # conjunction action
            self.add_success_block(plan, action)

            self.longtext_type(response)
            output = f"I get the high quality answer and I will send it.\nAction: {action}"
            self.planning_agent.add_to_history(output)
            self.after_action(output)
            return output, screenshot

        else:
            # non-click action
            self.add_success_block(plan, action)
            self.execute_action(action)
            output = f"{plan}\nAction: {action}"
            self.planning_agent.add_to_history(output)
            self.after_action(output)
            return output, screenshot
    
    def chinese_type(self, text):
        pyperclip.copy(text)
        pyautogui.hotkey('command', 'v')

    def longtext_type(self, text):
        segments = split_markdown_by_paragraphs(text, 400)
        for i, segment in enumerate(segments):
            segment = remove_markdown(segment)
            self.chinese_type(segment)
            time.sleep(0.5)  # Add a small delay between segments
            pyautogui.press('enter')

    def after_action(self, output):
        print_in_green(f"\nAgent Done:\n{output}")
        self.step_cnt += 1


    def execute_action(self, action):
        # click
        match = re.match(r"click \((-?\d+), (-?\d+)\)", action)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))

            if action.startswith("click"):
                pyautogui.click(x, y)
            elif action.startswith("right click"):
                pyautogui.rightClick(x, y)
            elif action.startswith("double click"):
                pyautogui.doubleClick(x, y)
            return

        # drag
        match = re.match(r"(drag from) \((-?\d+), (-?\d+)\) to \((-?\d+), (-?\d+)\)", action)
        if match:
            x1 = int(match.group(2))  # start x coordinate
            y1 = int(match.group(3))  # start y coordinate
            x2 = int(match.group(4))  # target x coordinate
            y2 = int(match.group(5))  # target y coordinate
            pyautogui.mouseDown(x1, y1)
            pyautogui.dragTo(x2, y2, duration=0.5)
            return

        # scroll
        match = re.match(r"scroll \((-?\d+), (-?\d+)\)", action)
        if match:
            x = int(match.group(1))  # horizontal scroll distance
            y = int(match.group(2))  # vertical scroll distance
            if x != 0:
                pyautogui.hscroll(x)  # horizontal scroll
            if y != 0:
                pyautogui.scroll(y)  # vertical scroll
            return

        # press key
        match = re.match(r"press key: (.+)", action)
        if match:
            key_content = match.group(1)
            pyautogui.press(key_content)
            return

        # hotkey
        match = re.match(r"hotkey \((.+), (.+)\)", action)
        if match:
            key1 = match.group(1).lower()
            key2 = match.group(2).lower()
            pyautogui.hotkey(key1, key2)
            return

        # type text
        match = re.match(r"type text: (.+)", action)
        if match:
            text_content = match.group(1)
            pyautogui.typewrite(text_content)
            return

        # wait
        if action == "wait":
            time.sleep(3)
            
        # finish
        #if action == "finish":
        #    self.exit(0)

        # fail
        if action == "fail":
            self.exit(1)

    def record(self, output, screenshot):
        # record in markdown
        first_event = self.step_cnt == 1
        record_in_md(self.directory_path, self.task_description, f"{self.step_cnt}.png", output, first_event=first_event)
        # save image
        screenshot_path = os.path.join(self.directory_path, f"{self.step_cnt}.png")
        save_screenshot(screenshot, screenshot_path)
    
    def add_success_block(self, plan, action):
        if self.output_queue is not None:
            self.output_queue.put(f"{plan}\n\nAction: {action}")
    
    def add_fail_block(self, plan):
        if self.output_queue is not None:
            self.output_queue.put(f"{plan}")
        
    def exit(self, exit_code):
        if exit_code == 0:
            print("Task is done!")
        
        exit(exit_code)
    