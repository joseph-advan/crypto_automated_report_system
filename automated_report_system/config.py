import os
import json
from dotenv import load_dotenv

# --- [新] 輔助函式：用來讀取檔案 ---
def load_prompt_file(file_path):
    """從指定的檔案路徑讀取文字內容。"""
    if not os.path.exists(file_path):
        print(f"警告：找不到 Prompt 檔案: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"讀取 Prompt 檔案 {file_path} 時發生錯誤: {e}")
        return None

# --- 載入 .env 檔案 ---
load_dotenv()

# --- 1. 檔案路徑 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
# [新] Prompt 檔案的路徑
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

# --- 2. API 金鑰與端點 ---
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    print("錯誤：找不到 TOGETHER_API_KEY，請檢查您的 .env 檔案。")

TOGETHER_MODEL_NAME = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
GROUND_TRUTH_API_ENDPOINT = "https://api.your-partner.com/v1/verify"

# --- 3. LLM 提示詞 (Prompts) ---

# [修改] 不再寫死，而是從外部檔案讀取
EXTRACTION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "extraction_prompt.txt")
GENERATION_SCHEMA_PATH = os.path.join(PROMPTS_DIR, "generation_schema.json")
GENERATION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "generation_prompt.txt")

EXTRACTION_PROMPT = load_prompt_file(EXTRACTION_PROMPT_PATH)
REPORT_SCHEMA_JSON = load_prompt_file(GENERATION_SCHEMA_PATH) # 這會讀取為字串
GENERATION_PROMPT_TEMPLATE = load_prompt_file(GENERATION_PROMPT_PATH) # 存為模板

# [修改] 讓 GENERATION_PROMPT 在 "執行時" 才組合
# 這樣可以確保 REPORT_SCHEMA_JSON 總是保持最新
def get_generation_prompt(diff_data_json_string):
    """
    組合最終的「階段五」生成提示詞
    """
    if not GENERATION_PROMPT_TEMPLATE or not REPORT_SCHEMA_JSON:
        raise FileNotFoundError("找不到 Generation Prompt 或 Schema 檔案。")
        
    # 替換模板中的佔位符
    prompt = GENERATION_PROMPT_TEMPLATE.replace(
        '{{diff_data_placeholder}}', 
        diff_data_json_string
    )
    prompt = prompt.replace(
        '{{schema_placeholder}}', 
        REPORT_SCHEMA_JSON
    )
    return prompt