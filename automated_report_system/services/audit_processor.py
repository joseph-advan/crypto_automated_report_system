# 檔案位置: automated_report_system/services/audit_processor.py
import re
from docx import Document
from .validator import Validator

class AuditProcessor:
    def __init__(self):
        self.mapping_list = []        # 詳細 Mapping 表 (Action B 產出)
        self.trace_requests = []      # (保留) 為了 traceRequestBody.json (未來金流比對)
        self.address_requests = set() # (保留) 為了 addressCheckRequest.json
        self.txh_check_requests = set() # <--- [修改] 為了 txhCheckRequestBody.json (實體驗證)
        self.counters = {"ADDR": 0, "TXID": 0, "AMT": 0, "TIME": 0}

    def _get_next_id(self, prefix):
        self.counters[prefix] += 1
        return f"[{prefix}_{self.counters[prefix]:03d}]"

    def process_document(self, input_path, output_docx_path):
        print(f"  [AuditProcessor] 讀取文件: {input_path}")
        doc = Document(input_path)

        # --- 階段 1: 處理表格 ---
        for table in doc.tables:
            self._process_table_logic(table)

        # --- 階段 2: 處理非表格段落 ---
        for para in doc.paragraphs:
            self._scan_and_mask_content(para)

        # --- 階段 3: 處理頁首頁尾 ---
        for section in doc.sections:
            for header_para in section.header.paragraphs:
                self._scan_and_mask_content(header_para)
            for footer_para in section.footer.paragraphs:
                self._scan_and_mask_content(footer_para)

        doc.save(output_docx_path)
        print(f"  [AuditProcessor] 全域遮罩完成，文件已儲存: {output_docx_path}")
        
        # [修改] 在回傳中加入 txh_check_requests
        return {
            "mapping": self.mapping_list,
            "trace_requests": self.trace_requests,
            "address_requests": list(self.address_requests),
            "txh_requests": list(self.txh_check_requests) # <--- [新增]
        }

    def _process_table_logic(self, table):
        """
        針對表格的處理邏輯：
        1. [Action A] 嘗試提取 Trace Request (高標準，看結構)
        2. [Action B] 對所有格子進行遮罩 (低標準，看內容)
        """
        for row in table.rows:
            # ====== [Action A] 提取 Trace Request ======
            if len(row.cells) >= 5:
                # 讀取原始文字
                raw_time = Validator.extract_first(row.cells[0].text, "TIME")
                raw_txid = Validator.extract_first(row.cells[1].text, "TXID")
                raw_from = Validator.extract_first(row.cells[2].text, "ADDR")
                raw_to   = Validator.extract_first(row.cells[3].text, "ADDR")
                raw_amt  = Validator.extract_first(row.cells[4].text, "AMT")

                # 判定邏輯：必須有 TXID 和 Amount 才視為有效交易
                if raw_txid and raw_amt:
                    # 清洗資料
                    clean_txid, _, _ = Validator.validate(raw_txid, "TXID")
                    clean_amt, _, _  = Validator.validate(raw_amt, "AMT")
                    clean_from, _, _ = Validator.validate(raw_from, "ADDR")
                    clean_to, _, _   = Validator.validate(raw_to, "ADDR")
                    clean_time, _, _ = Validator.validate(raw_time, "TIME")
                    
                    # --- [修改] 同時收集 TXID 和 Trace 資訊 ---
                    
                    # 1. (新增) 將表格中的 TXID 加入 txh_check_requests (用於實體驗證)
                    if clean_txid:
                        self.txh_check_requests.add(clean_txid)
                    
                    try: amt_val = float(clean_amt)
                    except: amt_val = 0.0

                    # 2. (保留) 將完整的交易紀錄加入 trace_requests (用於金流比對)
                    self.trace_requests.append({
                        "txh": clean_txid,
                        "chain": "TRON", "Token": "USDT",
                        "TimeStamp_UTC_8": clean_time if clean_time else row.cells[0].text.strip(),
                        "From": clean_from if clean_from else "",
                        "To": clean_to if clean_to else "",
                        "Amount": amt_val
                    })

            # ====== [Action B] 全域遮罩 (Global Masking) ======
            # (此部分不變)
            for cell in row.cells:
                self._scan_and_mask_content(cell)

    def _scan_and_mask_content(self, container):
        """
        [Action B 的核心] 通用掃描器
        (此函式不變)
        """
        text = container.text
        if not text.strip(): return

        scan_types = ["TXID", "ADDR", "TIME", "AMT"] 

        for dtype in scan_types:
            matches = Validator.find_all(container.text, dtype)
            
            for match in matches:
                raw_text = match.group(0)
                
                if raw_text in container.text:
                    self._mask_and_record(container, raw_text, dtype)

    def _mask_and_record(self, element, raw_text, type_prefix):
        """
        遮罩執行的原子操作：
        (此函式已修改，以收集 TXID)
        """
        if not raw_text: return
        
        new_id = self._get_next_id(type_prefix)
        clean_val, status, err_msg = Validator.validate(raw_text, type_prefix)

        # 1. 寫入 Mapping 表 (不變)
        self.mapping_list.append({
            "id": new_id, "type": type_prefix,
            "raw_text": raw_text, "clean_val": clean_val,
            "status": status, "error_msg": err_msg
        })

        # 2. 收集地址請求 (去重) (不變)
        if type_prefix == "ADDR" and clean_val:
            self.address_requests.add(clean_val)
            
        # 3. [新增] 收集 TXID 請求 (去重)
        if type_prefix == "TXID" and clean_val:
            self.txh_check_requests.add(clean_val)

        # 4. 執行遮罩 (修改 Word 物件) (不變)
        if hasattr(element, 'text'):
            element.text = element.text.replace(raw_text, new_id)