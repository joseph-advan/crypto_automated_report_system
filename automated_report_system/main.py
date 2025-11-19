# 檔案位置: automated_report_system/main.py
# (這是完整的、已修改的版本)

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
    # [修改] outputs 現在包含 'txh_requests'
    outputs = processor.process_document(
        input_path=input_path,
        output_docx_path=config.MASKED_REPORT_PATH
    )

    # 3. 存檔: Mapping 表 (含狀態碼) (不變)
    print(f"[存檔] Mapping 表: {config.MAPPING_PATH}")
    with open(config.MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(outputs['mapping'], f, indent=2, ensure_ascii=False)

    # 4. 存檔: Trace Requests (未來金流比對用) (不變)
    # (我們仍然保留這個檔案，為了你未來的「金流確認」API)
    print(f"[存檔] (金流確認) Trace Requests: {config.TRACE_REQUEST_PATH}")
    with open(config.TRACE_REQUEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(outputs['trace_requests'], f, indent=2, ensure_ascii=False)

    # 5. 存檔: Address Requests (地址實體驗證) (不變)
    print(f"[存檔] (地址確認) Address Requests: {config.ADDRESS_REQUEST_PATH}")
    addr_req_list = [
        {"address": addr, "chain": "Tron", "forceRefresh": False}
        for addr in outputs['address_requests']
    ]
    with open(config.ADDRESS_REQUEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(addr_req_list, f, indent=2, ensure_ascii=False)

    # 6. [新增] 存檔: TXH Check Requests (TXID 實體驗證)
    print(f"[存檔] (交易序號確認) TXH Check Requests: {config.TXH_CHECK_REQUEST_PATH}")
    txh_req_list = [
        {"txh": txh, "chain": "TRON", "forceRefresh": False}
        for txh in outputs['txh_requests']
    ]
    # 根據你提供的 txhCheckRequestBody.json 格式，它需要是一個物件
    txh_req_object = {"queries": txh_req_list} 
    
    # 檢查 config.py 是否有 TXH_CHECK_REQUEST_PATH 這個設定
    if not hasattr(config, 'TXH_CHECK_REQUEST_PATH'):
        print(f"錯誤: 請先在 automated_report_system/config.py 中新增 'TXH_CHECK_REQUEST_PATH' 設定！")
        return
        
    with open(config.TXH_CHECK_REQUEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(txh_req_object, f, indent=2, ensure_ascii=False)


    print("\n[完成] 所有審計檔案已產出。")

if __name__ == "__main__":
    # 請確保檔案名稱正確
    run_audit_process("幣流追蹤調查報告_v3.1.docx")