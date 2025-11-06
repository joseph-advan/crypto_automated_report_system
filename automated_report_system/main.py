import os
import config
from services.file_processor import FileProcessor
from services.llm_service import LLMService
from services.verification_service import VerificationService
from services.pdf_renderer import PDFRenderer

# --- 準備工作 ---
os.makedirs(config.INPUT_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)
os.makedirs(config.TEMP_DIR, exist_ok=True)

# --- [修改] 初始化所有服務 ---
processor = FileProcessor()
# 將 config 中的 API Key 和新模型名稱傳入
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
        # ... (此階段程式碼不變) ...
        original_path = os.path.join(config.INPUT_DIR, original_report_name)
        masked_path = os.path.join(config.TEMP_DIR, "report-MASKED.docx")
        map_path = os.path.join(config.OUTPUT_DIR, "mapping.json")
        
        processor.mask_and_create_mapping(original_path, masked_path, map_path)
        print(f"[成功] 產出遮罩檔案及 Mapping 表: {map_path}\n")

        # --- 階段二：LLM 資料擷取 (雲端) ---
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