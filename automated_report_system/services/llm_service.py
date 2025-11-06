import requests
import json
from docx import Document

class LLMService:
    
    # [修改] __init__ 現在也接收 model_name
    def __init__(self, api_key, model_name):
        if not api_key:
            raise ValueError("API Key 不得為空。請檢查您的 .env 檔案。")
            
        self.api_key = api_key
        self.endpoint = "https://api.together.xyz/v1/chat/completions"
        self.model = model_name  # [修改] 不再寫死，而是使用傳入的參數
        print(f"  [LLMService] 已初始化，使用模型: {self.model}")

    def _call_api(self, prompt_text):
        """ 呼叫 Together AI API 的私有方法 """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model, # [修改] 這裡會使用您在 config 中指定的新模型
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.0, 
            "max_tokens": 4096,
            "response_format": {"type": "json_object"} 
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=data)
            response.raise_for_status() 
            
            raw_response = response.json()
            json_string = raw_response['choices'][0]['message']['content']
            
            if json_string.startswith("```json"):
                json_string = json_string[7:-3].strip()
                
            return json.loads(json_string)
            
        except requests.RequestException as e:
            print(f"  [LLMService] API 呼叫失敗: {e}")
            raise
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [LLMService] 無法解析 LLM 回傳的 JSON: {e}")
            print(f"  [LLMService] 原始回傳: {response.text}")
            raise

    def extract_data_from_report(self, masked_docx_path, prompt_template):
        """
        [階段二] 的主函式
        """
        print(f"  [LLMService] 正在讀取遮罩檔案: {masked_docx_path}")
        doc = Document(masked_docx_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        
        final_prompt = f"{prompt_template}\n\n[報告內文開始]\n{full_text}\n[報告內文結束]\n\n請開始擷取："
        
        print(f"  [LLMService] 正在呼叫 LLM (擷取)...")
        return self._call_api(final_prompt)

    def generate_report_from_diff(self, diff_report_masked_json, prompt_template, schema_json):
        """
        [階段五] 的主函式
        """
        diff_string = json.dumps(diff_report_masked_json, indent=2, ensure_ascii=False)
        final_prompt = prompt_template.replace(
            '{{"diff_data_placeholder"}}', 
            diff_string
        )
        
        print("  [LLMService] 正在呼叫 LLM (生成報告)...")
        return self._call_api(final_prompt)