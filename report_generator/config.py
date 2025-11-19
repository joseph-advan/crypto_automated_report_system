# 檔案位置: report_generator/config.py
# (這是完整的、已修改的版本)

import os
from dotenv import load_dotenv

# --- 1. 核心路徑設定 ---
REPORT_GENERATOR_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(REPORT_GENERATOR_DIR)

# --- 2. 載入環境變數 (API 金鑰) ---
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print(f"[Config] 成功從 {ENV_PATH} 載入 .env 檔案。")
else:
    print(f"[Config] 警告: 在 {ENV_PATH} 找不到 .env 檔案。")
    print("[Config] 請確保 .env 檔案位於 'crypto_llm/' 根目錄下。")

# --- 3. Together AI 設定 ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
LLM_MODEL_ID = "togethercomputer/Llama-4-Scout-Instruct-17Bx16E" 

# --- 4. 檔案路徑設定 (輸入) ---
AUDIT_DATA_DIR = os.path.join(BASE_DIR, "automated_report_system", "data")

# (階段一) AuditProcessor 的輸出
MAPPING_FILE = os.path.join(AUDIT_DATA_DIR, "output", "mapping.json")

# (階段二) API 回傳的檔案
ADDRESS_API_RESPONSE_FILE = os.path.join(AUDIT_DATA_DIR, "api_data", "addressChech200OK.json")

# --- [ critical ] 修改 ---
# 1. 變數名稱從 TRACE_ 改為 TXH_ 以符合語意
# 2. 路徑從 api_data_trace/trace200OK.json 改為 api_data_txh/txhCheck200OK.json
TXH_API_RESPONSE_FILE = os.path.join(AUDIT_DATA_DIR, "api_data_txh", "txhCheck200OK.json")
# --- [修改完畢] ---


# --- 5. Prompt 模板路徑 (輸入) ---
PROMPT_DIR = os.path.join(REPORT_GENERATOR_DIR, "prompts")
ENTITY_SYSTEM_PROMPT_FILE = "entity_correction_system.txt"
ENTITY_USER_PROMPT_FILE = "entity_correction_user.txt" 

# --- 6. 最終報告輸出路徑 (輸出) ---
OUTPUT_REPORT_DIR = os.path.join(REPORT_GENERATOR_DIR, "generated_reports")

# 獨立測試用的 Debug 檔案 (會儲存在 generated_reports/ 中)
DEBUG_AUGMENTED_DATA_FILE = os.path.join(OUTPUT_REPORT_DIR, "_debug_augmented_data.json")
DEBUG_PROMPT_MESSAGES_FILE = os.path.join(OUTPUT_REPORT_DIR, "_debug_prompt_messages.json")
FINAL_REPORT_FILE = os.path.join(OUTPUT_REPORT_DIR, "entity_correction_report.md")

# --- 7. 確保輸出目錄存在 ---
try:
    os.makedirs(OUTPUT_REPORT_DIR, exist_ok=True)
except OSError as e:
    print(f"[Config] 錯誤: 無法建立輸出目錄 {OUTPUT_REPORT_DIR}: {e}")