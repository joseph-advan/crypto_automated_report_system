# 檔案: automated_report_system/main.py

import os
import config
from services.file_processor import FileProcessor
from services.llm_service import LLMService
from services.verification_service import VerificationService
from services.pdf_renderer import PDFRenderer
from services.pre_check_service import PreCheckService # <-- [新加入的行]

# --- 準備工作 ---
os.makedirs(config.INPUT_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)
os.makedirs(config.TEMP_DIR, exist_ok=True)
os.makedirs(config.API_DATA_DIR, exist_ok=True) # <-- [新加入的行] (確保資料夾存在)

# --- 初始化所有服務 ---
processor = FileProcessor()
pre_checker = PreCheckService() # <-- [新加入的行]
llm = LLMService(
    api_key=config.TOGETHER_API_KEY, 
    model_name=config.TOGETHER_MODEL_NAME
)
verifier = VerificationService(api_endpoint=config.GROUND_TRUTH_API_ENDPOINT)
renderer = PDFRenderer()

def run_full_process(original_report_name):
    """
    執行完整的 6 階段自動化鑑定流程
    """
    print(f"[系統] 開始處理新報告: {original_report_name}\n")

    try:
        # --- 階段一：資料處理與安全遮罩 (本地) ---
        print("[階段 1/6] 執行資料遮罩...")
        original_path = os.path.join(config.INPUT_DIR, original_report_name)
        masked_path = os.path.join(config.TEMP_DIR, "report-MASKED.docx")
        map_path = os.path.join(config.OUTPUT_DIR, "mapping.json")
        
        processor.mask_and_create_mapping(original_path, masked_path, map_path)
        print(f"[成功] 產出遮罩檔案及 Mapping 表: {map_path}\n")

        # --- [新階段] 預先檢查 (本地模擬) ---
        print("[新階段] 執行 Mapping 地址預先檢查...")
        pre_check_report_path = config.PRE_CHECK_REPORT_PATH # 從 config 讀取路徑
        pre_checker.run_check(
            mapping_path=map_path,
            ground_truth_path=config.ADDRESS_CHECK_TRUTH_PATH,
            output_report_path=pre_check_report_path
        )
        print(f"[成功] 產出預先檢查報告: {pre_check_report_path}\n")
        
        # --- [修改] 測試暫停點 ---
        print("--- [測試] 階段一 及 預先檢查 已完成，程式將在此停止 ---")
        print(f"--- [測試] 請檢查檔案: {map_path} ---")
        print(f"--- [測試] 請檢查檔案: {pre_check_report_path} ---") # <-- [新加入的行]
        return # <--- 關鍵修改！程式會在這裡停止執行。
        
        # --- 階段二：LLM 資料擷取 (雲端) ---
        # (因為上面的 return, 以下的程式碼將不會被執行)
        print("[階段 2/6] 呼叫雲端 LLM 進行資料擷取...")
        masked_extraction_json = llm.extract_data_from_report(
            masked_path, 
            config.EXTRACTION_PROMPT
        )
        print("[成功] 收到遮罩後的擷取結果 (JSON)\n")
        
        # --- (後續階段暫時跳過) ---
        print("--- [階段二測試完成] ---")
        # ... (階段 3-6 程式碼) ...


    except Exception as e:
        print(f"[!! 嚴重錯誤 !!] 處理流程中斷: {e}")
        raise

# --- 執行 ---
if __name__ == "__main__":
    # 確保您已將 "幣流追蹤調查報告_v3.1.docx" 放在 /data/input/ 資料夾
    run_full_process("幣流追蹤調查報告_v3.1.docx")