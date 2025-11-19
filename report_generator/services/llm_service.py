# 檔案位置: report_generator/services/llm_service.py

import requests
import json
import config # 這是 report_generator/config.py，由 main_generate_report.py 載入

class LLMService:
    """
    (新架構)
    專門負責與 Together AI API 進行通訊。
    這是一個獨立的服務，不包含任何 Prompt 邏輯或資料處理邏輯。
    
    [階段 3：LLM 通訊]
    """

    def __init__(self, api_key, api_url):
        """
        初始化 LLM 服務。
        
        Args:
            api_key (str): 來自 config.TOGETHER_API_KEY
            api_url (str): 來自 config.TOGETHER_API_URL
        """
        if not api_key:
            raise ValueError("LLMService 錯誤: TOGETHER_API_KEY 未設定，請檢查您的 .env 檔案。")
        
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json" # 明確要求 JSON 回應
        }

    def generate_report(self, messages, model_id):
        """
        呼叫 Together AI 的 Chat Completions API。
        
        Args:
            messages (list): 由 PromptManager 產生的 `messages` 列表。
            model_id (str): 要使用的模型 ID (例如 config.LLM_MODEL_ID)。

        Returns:
            str: 來自 LLM 的文字回應，或是一段錯誤訊息。
        """
        
        print(f"[LLMService] 正在呼叫 Together AI API... 模型: {model_id}")
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.1,  # 審計報告需要精確，使用低溫
            "top_p": 0.9,
            "max_tokens": 4096,  # 預留足夠空間給報告
            "repetition_penalty": 1.05
        }
        
        try:
            # 我們設定一個較長的超時時間 (例如 180 秒)，因為 MoE 模型可能需要一些時間
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                data=json.dumps(payload), 
                timeout=180 
            )
            
            # 檢查 HTTP 狀態碼 (例如 401, 404, 500)
            response.raise_for_status() 
            
            response_data = response.json()
            
            # 提取 LLM 的回覆
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content")
                if content:
                    print("[LLMService] 成功收到 LLM 回應。")
                    return content.strip()
                else:
                    print("[LLMService] 錯誤：API 回應中找不到 'content'。")
                    return "錯誤：API 回應中找不到 'content'。"
            else:
                print(f"[LLMService] 錯誤：API 回應格式不正確。 {response_data}")
                return f"錯誤：API 回應格式不正確。 {response_data}"

        except requests.exceptions.HTTPError as http_err:
            # 處理 4xx 或 5xx 錯誤
            print(f"[LLMService] HTTP 錯誤: {http_err} - 回應: {response.text}")
            return f"HTTP 錯誤: {http_err} - 回應: {response.text}"
        except requests.exceptions.Timeout:
            # 處理超時
            print("[LLMService] 錯誤：API 請求超時 (Timeout)。")
            return "錯誤：API 請求超時 (Timeout)。"
        except requests.exceptions.RequestException as req_err:
            # 處理其他連線錯誤
            print(f"[LLMService] 連線錯誤: {req_err}")
            return f"連線錯誤: {req_err}"
        except json.JSONDecodeError:
            print(f"[LLMService] 錯誤：無法解析 API 的 JSON 回應。 回應: {response.text}")
            return f"錯誤：無法解析 API 的 JSON 回應。 回應: {response.text}"
        except Exception as e:
            # 處理其他未預期錯誤
            print(f"[LLMService] 發生未預期錯誤: {e}")
            return f"發生未預期錯誤: {e}"

# --- 用於獨立測試的程式碼 ---
if __name__ == "__main__":
    # 這個區塊允許你 "直接" 執行這個檔案 (python services/llm_service.py)
    # 來快速測試你的 API 金鑰是否有效，而不需要執行整個 main_generate_report.py
    
    print("=== 執行 LLMService 獨立測試 ===")
    
    # --- 測試環境設定 (修正 import 路徑) ---
    # 為了讓這個 "子檔案" 能夠讀取到 "父資料夾" 中的 config.py
    # 我們需要手動將父資料夾 (report_generator) 加入 Python 的系統路徑
    import sys
    import os
    
    # 取得目前檔案 (llm_service.py) 的目錄 (services/)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # 取得 'services/' 的上一層目錄 (report_generator/)
    REPORT_GENERATOR_DIR = os.path.dirname(CURRENT_DIR)
    
    # 將 report_generator/ 加入 sys.path
    sys.path.append(REPORT_GENERATOR_DIR)
    
    try:
        import config # 現在可以成功 import config.py 了
    except ImportError:
        print("測試錯誤: 似乎無法找到 config.py。")
        print(f"請確認 config.py 位於: {REPORT_GENERATOR_DIR}")
        sys.exit(1)
    # --- 測試環境設定完畢 ---

    if not config.TOGETHER_API_KEY:
        print("測試失敗: TOGETHER_API_KEY 未在 .env 檔案中設定。")
    else:
        print("成功載入 API 金鑰。")
        
        # 1. 初始化服務
        llm = LLMService(
            api_key=config.TOGETHER_API_KEY,
            api_url=config.TOGETHER_API_URL
        )
        
        # 2. 準備一個簡單的測試 Prompt
        test_messages = [
            {"role": "system", "content": "你是一個有用的助理。"},
            {"role": "user", "content": "請用繁體中文回覆 'Hello'。"}
        ]
        
        print(f"正在使用模型 {config.LLM_MODEL_ID} 進行連線測試...")
        
        # 3. 執行 API 呼叫
        response = llm.generate_report(
            messages=test_messages,
            model_id=config.LLM_MODEL_ID
        )
        
        print("\n" + "="*30)
        print("  Together AI API 測試回應：")
        print("="*30)
        print(response)