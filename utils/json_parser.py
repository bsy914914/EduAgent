"""JSON parsing utilities"""

import json
import re
from typing import Dict, Any, Union, List
from config import DEFAULT_TEMPLATE_STRUCTURE


def extract_json_from_response(response_content: Union[str, List, Dict]) -> Dict:
    """Extract JSON from LLM response content"""
    try:
        # Handle different response formats
        if isinstance(response_content, list):
            text_content = ""
            for item in response_content:
                if isinstance(item, dict) and 'text' in item:
                    text_content += item['text']
                elif isinstance(item, str):
                    text_content += item
        elif isinstance(response_content, str):
            text_content = response_content
        else:
            print(f"Unknown response format: {type(response_content)}")
            return DEFAULT_TEMPLATE_STRUCTURE
        
        # Method 1: Extract JSON from markdown code blocks (multiple patterns)
        json_patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json ... ```
            r'```\s*\n(.*?)\n```',      # ``` ... ```
            r'```json(.*?)```',          # ```json...``` (no newlines)
            r'```(.*?)```',              # ```...``` (no newlines)
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text_content, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        cleaned = match.strip()
                        return json.loads(cleaned)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON decode failed for pattern {pattern}: {e}")
                        continue
        
        # Method 2: Find complete JSON objects (supports nesting)
        start_idx = text_content.find('{')
        if start_idx != -1:
            brace_count = 0
            for i in range(start_idx, len(text_content)):
                if text_content[i] == '{':
                    brace_count += 1
                elif text_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            json_str = text_content[start_idx:i+1]
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            break
        
        # Method 3: Clean and try direct parsing
        try:
            # Remove common prefixes and suffixes
            cleaned_content = text_content.strip()
            
            # Remove common markdown artifacts
            if cleaned_content.startswith('json'):
                cleaned_content = cleaned_content[4:].strip()
            
            # Try parsing
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"⚠️ Direct JSON parsing failed: {e}")
            pass
        
        # Method 4: Try to find JSON array
        array_start = text_content.find('[')
        if array_start != -1:
            bracket_count = 0
            for i in range(array_start, len(text_content)):
                if text_content[i] == '[':
                    bracket_count += 1
                elif text_content[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        try:
                            json_str = text_content[array_start:i+1]
                            result = json.loads(json_str)
                            # Wrap array in object if needed
                            if isinstance(result, list):
                                return {"data": result}
                            return result
                        except json.JSONDecodeError:
                            break
        
        # If all methods fail, return default template
        print("=" * 80)
        print(f"❌ Cannot extract valid JSON from response, using default template")
        print(f"📝 Response type: {type(text_content)}")
        print(f"📏 Response length: {len(text_content)}")
        print(f"🔍 First 1000 characters of response:")
        print(text_content[:1000])
        print("=" * 80)
        
        # 保存完整响应用于调试
        try:
            with open("failed_json_response.txt", "w", encoding="utf-8") as f:
                f.write(text_content)
            print("💾 完整响应已保存到 failed_json_response.txt")
        except:
            pass
            
        return DEFAULT_TEMPLATE_STRUCTURE
        
    except Exception as e:
        print(f"JSON extraction error: {e}")
        return DEFAULT_TEMPLATE_STRUCTURE

def fix_and_extract_json(content_text):
    """
    修复并提取JSON - 处理LaTeX公式和代码块中的特殊字符
    """
    pattern = r'```json\s*(.*?)\s*```'
    matches = re.findall(pattern, content_text, re.DOTALL)
    
    valid_jsons = []
    
    for i, match in enumerate(matches):
        json_text = match.strip()
        
        try:
            # 关键修复步骤
            
            # 1. 修复LaTeX公式中的反斜杠（在双引号内的反斜杠需要转义）
            # 将 $ ... \command ... $ 中的单反斜杠改为双反斜杠
            def fix_latex(m):
                content = m.group(0)
                # 替换公式内的 \ 为 \\
                return content.replace('\\', '\\\\')
            
            json_text = re.sub(r'\$[^$]+\$', fix_latex, json_text)
            
            # 2. 修复代码块中的实际换行符
            # 找到包含代码的字符串值，将真实换行替换为 \n
            def fix_code_newlines(text):
                # 在字符串值内部查找并替换换行符
                in_string = False
                escape_next = False
                result = []
                
                for char in text:
                    if escape_next:
                        result.append(char)
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        result.append(char)
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        result.append(char)
                        continue
                    
                    if in_string:
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                        elif ord(char) < 32:  # 其他控制字符
                            result.append(f'\\u{ord(char):04x}')
                        else:
                            result.append(char)
                    else:
                        result.append(char)
                
                return ''.join(result)
            
            json_text = fix_code_newlines(json_text)
            
            # 3. 尝试解析
            json_obj = json.loads(json_text)
            valid_jsons.append(json_obj)
            print(f"JSON {i+1} 提取成功")
            
        except json.JSONDecodeError as e:
            print(f"JSON {i+1} 解析失败: {e}")
            print(f"错误位置: {json_text[max(0, e.pos-100):e.pos+100]}")
    
    return valid_jsons

