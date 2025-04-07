import os
import time
import io
import base64
from PIL import ImageDraw, ImageGrab, Image
import re


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot

# def resize_screenshot(screenshot, target_width):
    
#     original_width, original_height = screenshot.size
#     scaling_factor = target_width / original_width  # 计算缩放比例
#     target_height = int(original_height * scaling_factor)  # 等比例计算高度
    
#     resized_screenshot = screenshot.resize(
#         (target_width, target_height), 
#         Image.LANCZOS  # 使用高质量的缩放算法
#     )

#     return resized_screenshot


def encode_image(image):
    # encode image to base64 string
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def save_screenshot(screenshot, path):
    screenshot.save(path, format="PNG")


def get_vlm_messages(instruction, base64_image):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
                {
                    "type": "text",
                    "text": instruction
                },
            ],
        },
    ]
    return messages

def get_llm_messages(instruction):
    messages = [
        {
            "role": "user",
            "content": [
                    {"type": "text", "text": instruction}
            ],
        },
    ]
    return messages

def get_full_message(history, max_turns=5):
    # 如果历史记录为空，直接返回空列表
    if not history:
        return []
    
    # 只保留最后 max_turns 轮对话
    recent_history = history[-max_turns*2:] if len(history) > max_turns*2 else history
    
    messages = []
    for message in recent_history:
        messages.append({
            "role": message["role"],
            "content": message["content"]
        })
    
    return messages


def mark_screenshot(original_screenshot, coordinates, rect=None):
    screenshot = original_screenshot.copy()
    x, y = coordinates
    point = {"x": x, "y": y}

    if rect is not None:
        # create a drawable object
        draw = ImageDraw.Draw(screenshot)
        # draw the rectangle
        draw.rectangle(
            [(rect["left"], rect["top"]), (rect["right"], rect["bottom"])],
            outline="red",
            width=3  # line width
        )

    if point is not None:
        draw = ImageDraw.Draw(screenshot)

        # calculate the top-left and bottom-right coordinates of the solid circle
        radius = 3
        left = point["x"] - radius
        top = point["y"] - radius
        right = point["x"] + radius
        bottom = point["y"] + radius

        # draw the solid circle
        draw.ellipse(
            [(left, top), (right, bottom)],
            fill="red"
        )

        # add a larger hollow circle
        circle_radius = 18
        circle_left = point["x"] - circle_radius
        circle_top = point["y"] - circle_radius
        circle_right = point["x"] + circle_radius
        circle_bottom = point["y"] + circle_radius

        # draw the hollow circle
        draw.ellipse(
            [(circle_left, circle_top), (circle_right, circle_bottom)],
            outline="red",
            width=2
        )

    return screenshot


def record_in_md(directory_path, task_description, screenshot_path, output, external_reflection=None,
                 first_event=False):
    file_name = "inference_record.md"
    with open(os.path.join(directory_path, file_name), "a", encoding="utf-8") as file:
        if first_event:
            file.write(f"# Inference Task\n")
            file.write(f"**Description:** {task_description}\n\n")
        file.write(f"### {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        file.write(f"**Screenshot:**\n")
        file.write(f'<img src="{screenshot_path}" width="100%" height="100%">\n\n')
        file.write(f"**External Reflection:**\n{external_reflection}\n\n") if external_reflection else None
        file.write(f"**Output:**\n{output}\n\n")


def log(message, filename="agent.log"):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # open the file with UTF-8 encoding
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(f"{current_time}\n{message}\n\n")


def print_in_green(message):
    print(f"\033[92m{message}\033[0m")


def split_markdown_by_paragraphs(markdown_text, max_length):
    """
    将Markdown文本仅在段落之间切分，确保每个片段不超过max_length
    
    参数:
        markdown_text (str): 输入的Markdown文本
        max_length (int): 最大片段长度
        
    返回:
        list: 切分后的文本片段列表
    """
    # 按照段落分割文本
    paragraphs = re.split(r'\n', markdown_text)
    paragraphs = [p for p in paragraphs if p.strip()]
    
    # 计算每个段落的长度
    paragraph_lengths = [len(p) for p in paragraphs]
    
    # 贪心算法：尽可能少地切分文本
    segments = []
    current_segment = []
    current_length = 0
    
    for i, paragraph in enumerate(paragraphs):
        para_length = paragraph_lengths[i]
        
        # 如果单个段落超过最大长度，则单独作为一个片段
        if para_length > max_length:
            # 如果当前已有内容，先保存
            if current_segment:
                segments.append("\n".join(current_segment))
                current_segment = []
                current_length = 0
            
            # 添加这个过长的段落作为单独片段
            segments.append(paragraph)
            continue
        
        # 如果加上这个段落后超过最大长度，先保存当前片段
        if current_length + para_length + (2 if current_segment else 0) > max_length:
            segments.append("\n".join(current_segment))
            current_segment = [paragraph]
            current_length = para_length
        else:
            # 否则添加到当前片段
            current_segment.append(paragraph)
            current_length += para_length + (2 if current_length > 0 else 0)  # 加上段落间的换行符长度
    
    # 添加最后一个片段
    if current_segment:
        segments.append("\n".join(current_segment))
    
    return segments

def remove_markdown(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 移除粗体 **文本**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # 移除斜体 *文本*
    # 移除标题标记 (# 标题)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # 移除有序列表标记 (1. 列表项)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    # 移除无序列表标记 (- 列表项 或 * 列表项)
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    # 移除链接，保留链接文本 ([链接文本](链接URL))
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 移除图片标记 (![替代文本](图片URL))
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 移除代码块
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # 移除行内代码标记
    text = re.sub(r'`(.*?)`', r'\1', text)
    # 移除引用标记
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # 移除水平分割线
    text = re.sub(r'^\s*[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # 处理可能的多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()