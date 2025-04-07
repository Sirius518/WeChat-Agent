from utils import *
import re

class GroundingAgent:
    def __init__(self, grounding_client):
        self.grounding_client = grounding_client
        #self.grounding_model = grounding_client.models.list().data[0].id
        self.paper_model = 'bot-20250323202019-mxkrp'
        self.normal_model = 'bot-20250401143657-r9w4d'
        print(f"paper model: {self.paper_model}")
        print(f"normal model: {self.normal_model}")
        self.message_history = []
        screenshot = get_screenshot()
        self.window_width = screenshot.width
        self.window_height = screenshot.height
        

    def call_grounding(self, instruction):
        """
        call the grounding model to locate the element,
        return x, y, there_are_none
        """
        self.message_history.append({"role": "user", "content": instruction})
        instruction, model = self.paper_guide(instruction)

        if model == self.paper_model:
            completion = self.grounding_client.chat.completions.create(
                model=model,
                messages=get_llm_messages(instruction),
                max_tokens=2048,
                temperature=0.8,
            )
        else:
            messages = get_full_message(self.message_history)
            completion = self.grounding_client.chat.completions.create(
                model=self.normal_model,
                messages=messages,
                max_tokens=2048,
                temperature=0.8,
            )
        
        # Try each response until we find valid coordinates
        output_text = completion.choices[0].message.content
        self.message_history.append({"role": "assistant", "content": output_text})

        return output_text
    

    def paper_guide(self, text):
        """
        在文本中查找并转换 arXiv 链接为标准 PDF 格式
        
        Args:
            text (str): 包含 arXiv 链接的文本
                    
        Returns:
            tuple: (处理后的文本, 使用的模型名称)
        """
        # 匹配 arXiv ID 的模式
        patterns = [
            r'(https?://arxiv\.org/abs/\d+\.\d+(?:v\d+)?)',    # 匹配 abs 格式
            r'(https?://arxiv\.org/pdf/\d+\.\d+(?:v\d+)?)',    # 匹配 pdf 格式
            r'(https?://arxiv\.org/html/\d+\.\d+(?:v\d+)?)',   # 匹配 html 格式
            r'(arXiv:\d+\.\d+(?:v\d+)?)',                      # 匹配 arXiv:ID 格式
        ]
        
        # 移除版本号（如果存在）
        def remove_version(arxiv_id):
            return arxiv_id.split('v')[0]
        
        # 提取 arXiv ID 的模式
        id_patterns = [
            r'arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+(?:v\d+)?)',  # 匹配网址中的ID
            r'arXiv:(\d+\.\d+(?:v\d+)?)',                        # 匹配 arXiv:ID 格式
        ]
        
        # 标记是否找到 arXiv 链接
        found_arxiv = False
        
        # 在文本中查找所有可能的 arXiv 链接
        result_text = text
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_arxiv = True
                original_link = match.group(0)
                
                # 从链接中提取 ID
                arxiv_id = None
                for id_pattern in id_patterns:
                    id_match = re.search(id_pattern, original_link, re.IGNORECASE)
                    if id_match:
                        arxiv_id = id_match.group(1)
                        break
                
                if arxiv_id:
                    # 移除版本号并构建新链接
                    clean_id = remove_version(arxiv_id)
                    new_link = f'https://arxiv.org/pdf/{clean_id}'
                    # 替换原文本中的链接
                    result_text = result_text.replace(original_link, new_link)
        
        # 根据是否找到 arXiv 链接返回对应的模型
        return result_text, self.paper_model if found_arxiv else self.normal_model
