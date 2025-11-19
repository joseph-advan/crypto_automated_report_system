# 檔案位置: report_generator/main_generate_report.py
# (這是完整的、已修改的版本)

import config
import os
from processing.data_integrator import DataIntegrator
from services.prompt_manager import PromptManager
from services.llm_service import LLMService

def main():
    print("[主程式] 1. 載入設定...")
    
    try:
        # --- [ critical ] 修改 ---
        # 建立服務
        # 1. 傳入 config.TXH_API_RESPONSE_FILE 而不是 ...TRACE...
        integrator = DataIntegrator(
            mapping_path=config.MAPPING_FILE,
            address_api_path=config.ADDRESS_API_RESPONSE_FILE,
            txh_api_path=config.TXH_API_RESPONSE_FILE # <--- [修改]
        )
        # --- [修改完畢] ---
        
        prompter = PromptManager()
        
        llm = LLMService(
            api_key=config.TOGETHER_API_KEY,
            api_url=config.TOGETHER_API_URL
        )
    except FileNotFoundError as e:
        print(f"\n[主程式] 嚴重錯誤: {e}")
        print("請檢查 automated_report_system/data/ 目錄下是否缺少必要的輸入檔案。")
        return
    except ValueError as e:
         print(f"\n[主程式] 嚴重錯誤: {e}")
         print("請檢查您的 .env 檔案是否已設定 TOGETHER_API_KEY。")
         return

    print("[主程式] 2. 正在整合本地與 API 資料...")
    augmented_data = integrator.integrate_data()
    
    if not augmented_data:
        print("[主程式] 錯誤：資料整合失敗，請檢查輸入檔案。")
        return

    print(f"[主程式] 3. 成功整合 {len(augmented_data)} 筆實體資料。正在準備 Prompt...")
    report_prompt_messages = prompter.get_entity_correction_prompt(augmented_data)
    
    if not report_prompt_messages:
        print("[主程式] 錯誤：產生 Prompt 失敗，請檢查 Prompt 模板檔案。")
        return

    print("[主程式] 4. 正在傳送請求至 LLM (Llama 4 Scout)...")
    final_report = llm.generate_report(
        messages=report_prompt_messages,
        model_id=config.LLM_MODEL_ID
    )

    print("\n" + "="*50)
    print(" 最終產出的「實體項目訂正報告」：")
    print("="*50 + "\n")
    print(final_report)

    # 5. 存檔
    try:
        with open(config.FINAL_REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"\n[主程式] 報告已儲存至: {config.FINAL_REPORT_FILE}")
    except IOError as e:
        print(f"\n[主程式] 錯誤: 儲存報告失敗: {e}")


if __name__ == "__main__":
    main()