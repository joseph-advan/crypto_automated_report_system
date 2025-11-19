# 檔案位置: report_generator/services/prompt_manager.py
# (這是完整的、已修改的版本)

import json
import os
import config 

class PromptManager:
    """
    (新架構) 
    負責從 `prompts/` 資料夾載入模板，
    並將動態資料 (augmented_entities) 填入模板中，
    最終產生 API 所需的 "messages" 格式。
    """

    def __init__(self):
        if not os.path.isdir(config.PROMPT_DIR):
            print(f"[PromptManager] 嚴重錯誤: Prompt 目錄未找到: {config.PROMPT_DIR}")
            raise FileNotFoundError(f"Prompt 目錄未找到: {config.PROMPT_DIR}")
        print(f"[PromptManager] 已初始化。Prompt 模板目錄: {config.PROMPT_DIR}")

    def _load_prompt_template(self, filename):
        file_path = os.path.join(config.PROMPT_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[PromptManager] 嚴重錯誤: 找不到 Prompt 檔案: {file_path}")
            raise
        except Exception as e:
            print(f"[PromptManager] 讀取 Prompt 檔案時發生錯誤 {file_path}: {e}")
            raise

    def _format_entities_for_llm(self, augmented_entities):
        """
        [輔助函式]
        (此函式已更新，以處理 txhCheck200OK 的新格式)
        """
        simplified_list = []
        for entity in augmented_entities:
            
            api_result_simplified = None
            entity_type = entity.get('type')
            api_verification = entity.get('api_verification') 
            
            if api_verification:
                if entity_type == 'ADDR':
                    # (不變) 對於地址，我們只關心 'formatCheck' 的結果
                    api_result_simplified = api_verification.get('formatCheck', {'message': 'API response missing formatCheck'})
                
                # --- [ critical ] 修改 ---
                elif entity_type == 'TXID':
                    # 'api_verification' 現在是 txhCheck200OK 的結果物件
                    # 例如: {"status": "Invalid", "message": "Tx hash format is invalid"}
                    # 這個格式本身已經很簡潔，我們直接傳遞它
                    api_result_simplified = api_verification 
                # --- [修改完畢] ---
            
            simplified_list.append({
                "id": entity.get("id"),
                "type": entity.get("type"),
                "raw_text": entity.get("raw_text"),
                "local_status": entity.get("local_validation", {}).get("status"),
                "local_error": entity.get("local_validation", {}).get("error_msg"),
                "api_result": api_result_simplified 
            })
        
        return json.dumps(simplified_list, indent=2, ensure_ascii=False)

    def get_entity_correction_prompt(self, augmented_entities):
        """
        (此函式不變，因為它只負責載入和填入模板)
        """
        print(f"[PromptManager] 正在從 '{config.PROMPT_DIR}' 載入 Prompt 模板...")
        try:
            system_prompt = self._load_prompt_template(config.ENTITY_SYSTEM_PROMPT_FILE)
            user_template = self._load_prompt_template(config.ENTITY_USER_PROMPT_FILE)
        except FileNotFoundError:
            print("[PromptManager] 錯誤: 找不到必要的 Prompt 檔案。停止執行。")
            return None 
        except Exception as e:
            print(f"[PromptManager] 載入 Prompt 時發生未預期錯誤: {e}")
            return None

        print("[PromptManager] 正在格式化資料以供 LLM 使用...")
        data_payload = self._format_entities_for_llm(augmented_entities)
        
        print("[PromptManager] 正在將資料注入 User Prompt 模板...")
        try:
            user_prompt = user_template.format(data_payload=data_payload)
        except KeyError as e:
            print(f"[PromptManager] 嚴重錯誤: User Prompt 模板中找不到佔位符: {e}")
            print("請確保 'entity_correction_user.txt' 包含 '{data_payload}'。")
            return None

        print("[PromptManager] Prompt 準備完成。")
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

# --- 獨立測試程式碼 (更新) ---
if __name__ == "__main__":
    
    print("="*50)
    print("=== 執行 PromptManager 獨立測試 ===")
    print("="*50)
    
    import sys
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPORT_GENERATOR_DIR = os.path.dirname(CURRENT_DIR)
    sys.path.append(REPORT_GENERATOR_DIR) 
    
    try:
        import config 
        from processing.data_integrator import DataIntegrator 
    except ImportError as e:
        print(f"\n[測試失敗] 無法匯入必要的模組: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[測試失敗] Config 載入時出錯。")
        sys.exit(1)

    try:
        print("\n[測試] 正在初始化 DataIntegrator...")
        integrator = DataIntegrator(
            mapping_path=config.MAPPING_FILE,
            address_api_path=config.ADDRESS_API_RESPONSE_FILE,
            txh_api_path=config.TXH_API_RESPONSE_FILE # <--- [修改]
        )
        augmented_data = integrator.integrate_data()

        if augmented_data:
            print("\n[測試] 正在初始化 PromptManager...")
            prompter = PromptManager()
            messages = prompter.get_entity_correction_prompt(augmented_data)
            
            if messages:
                print("\n" + "="*50)
                print("=== 測試成功：成功產生 Prompt Messages ===")
                print("="*50)
                
                os.makedirs(config.OUTPUT_REPORT_DIR, exist_ok=True)
                with open(config.DEBUG_PROMPT_MESSAGES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, indent=2, ensure_ascii=False)
                print(f"\n[測試] 完整的 Prompt Messages (包含注入的資料) 已儲存至: {config.DEBUG_PROMPT_MESSAGES_FILE}")

    except FileNotFoundError as e:
        print(f"\n[測試失敗] 找不到必要的輸入檔案: {e}")
    except Exception as e:
        print(f"\n[測試] 測試時發生未預期錯誤: {e}")