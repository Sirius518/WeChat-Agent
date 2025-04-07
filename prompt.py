ACTION_PROMPT = """You are a GUI agent designed for WeChat. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task. 

## Action Space
1. click (x, y)
click the screen at specific coordinates (x, y), where (x, y) should be replaced with actual coordinates from the current screenshot.

2. press key: key_content
press the key key_content on the keyboard.

3. type text: content
type content on the keyboard.

4. throw query: question
throw a question to the other agent and get high quality answer.

5. finish
indicating that the task has been completed.

## Output Format
Thought: {Your thought process}\n\nAction: {The specific action you choose to take}

## Note
- Summarize your next action (with its target element) in one sentence in `Thought` part.
"""

CHECH_MESSAGE = '''
You are a WeChat assistant analyzing app screenshots. Your task is to detect unread messages in the provided WeChat screenshot.

Carefully examine the image for any red dots appearing on profile pictures, which indicate unread messages.

If you find unread messages:
- Return only the username of the first contact with a red dot notification
- Format: "[Username]"

If no unread messages are detected (no red dots visible):
- Return only: "None"

Provide your analysis clearly and concisely without additional explanation.
'''

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