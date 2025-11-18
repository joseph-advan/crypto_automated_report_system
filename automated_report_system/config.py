# 檔案位置: automated_report_system/config.py
import os
# from dotenv import load_dotenv # 如果您有用到 .env 再打開

# --- 1. 檔案路徑 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# --- [新] 輸出檔案路徑 ---
MASKED_REPORT_PATH = os.path.join(OUTPUT_DIR, "report-MASKED.docx")
MAPPING_PATH = os.path.join(OUTPUT_DIR, "mapping.json")
TRACE_REQUEST_PATH = os.path.join(OUTPUT_DIR, "traceRequestBody.json")
ADDRESS_REQUEST_PATH = os.path.join(OUTPUT_DIR, "addressCheckRequest.json")
