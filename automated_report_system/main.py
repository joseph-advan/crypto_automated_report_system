import os
import json
import config
from services.audit_processor import AuditProcessor

# 確保資料夾存在
os.makedirs(config.INPUT_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

def run_audit_process(report_filename):
    print(f"[系統] 開始執行自動化審計: {report_filename}")
    
    input_path = os.path.join(config.INPUT_DIR, report_filename)
    if not os.path.exists(input_path):
        print(f"錯誤: 找不到檔案 {input_path}")
        return

    # 1. 初始化處理器
    processor = AuditProcessor()

    # 2. 執行處理 (讀取 -> 掃描 -> 遮罩)
    outputs = processor.process_document(
        input_path=input_path,
        output_docx_path=config.MASKED_REPORT_PATH
    )

    # 3. 存檔: Mapping 表 (含狀態碼)
    print(f"[存檔] Mapping 表: {config.MAPPING_PATH}")
    with open(config.MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(outputs['mapping'], f, indent=2, ensure_ascii=False)

    # 4. 存檔: Trace Requests (完整交易)
    print(f"[存檔] Trace Requests: {config.TRACE_REQUEST_PATH}")
    with open(config.TRACE_REQUEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(outputs['trace_requests'], f, indent=2, ensure_ascii=False)

    # 5. 存檔: Address Requests (轉換為指定格式)
    print(f"[存檔] Address Requests: {config.ADDRESS_REQUEST_PATH}")
    addr_req_list = [
        {"address": addr, "chain": "Tron", "forceRefresh": False}
        for addr in outputs['address_requests']
    ]
    with open(config.ADDRESS_REQUEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(addr_req_list, f, indent=2, ensure_ascii=False)

    print("\n[完成] 所有審計檔案已產出。")

if __name__ == "__main__":
    # 請確保檔案名稱正確
    run_audit_process("幣流追蹤調查報告_v3.1.docx")