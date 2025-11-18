# 檔案位置: automated_report_system/services/audit_processor.py
import re
from docx import Document
from .validator import Validator

class AuditProcessor:
    def __init__(self):
        self.mapping_list = []        # 詳細 Mapping 表 (Action B 產出)
        self.trace_requests = []      # 完整交易請求 (Action A 產出)
        self.address_requests = set() # 去重後的地址請求
        self.counters = {"ADDR": 0, "TXID": 0, "AMT": 0, "TIME": 0}

    def _get_next_id(self, prefix):
        self.counters[prefix] += 1
        return f"[{prefix}_{self.counters[prefix]:03d}]"

    def process_document(self, input_path, output_docx_path):
        print(f"  [AuditProcessor] 讀取文件: {input_path}")
        doc = Document(input_path)

        # --- 階段 1: 處理表格 (同時執行 Action A 與 Action B) ---
        # 表格是特殊的，因為它同時蘊含 "結構化資訊(Action A)" 和 "敏感文字(Action B)"
        for table in doc.tables:
            self._process_table_logic(table)

        # --- 階段 2: 處理非表格段落 (僅執行 Action B) ---
        # 針對散落在文件各處的文字進行無差別遮罩
        for para in doc.paragraphs:
            self._scan_and_mask_content(para)

        # (選用) 階段 3: 為了確保萬無一失，也可以掃描頁首頁尾
        for section in doc.sections:
            for header_para in section.header.paragraphs:
                self._scan_and_mask_content(header_para)
            for footer_para in section.footer.paragraphs:
                self._scan_and_mask_content(footer_para)

        doc.save(output_docx_path)
        print(f"  [AuditProcessor] 全域遮罩完成，文件已儲存: {output_docx_path}")
        
        return {
            "mapping": self.mapping_list,
            "trace_requests": self.trace_requests,
            "address_requests": list(self.address_requests)
        }

    def _process_table_logic(self, table):
        """
        針對表格的處理邏輯：
        1. [Action A] 嘗試提取 Trace Request (高標準，看結構)
        2. [Action B] 對所有格子進行遮罩 (低標準，看內容)
        """
        for row in table.rows:
            # ====== [Action A] 提取 Trace Request ======
            # 只有當欄位足夠時，才嘗試理解其結構 (假設前5欄為固定格式)
            if len(row.cells) >= 5:
                # 這裡只 "讀取" 來做判斷，絕對不修改文字
                raw_time = Validator.extract_first(row.cells[0].text, "TIME")
                raw_txid = Validator.extract_first(row.cells[1].text, "TXID")
                raw_from = Validator.extract_first(row.cells[2].text, "ADDR")
                raw_to   = Validator.extract_first(row.cells[3].text, "ADDR")
                raw_amt  = Validator.extract_first(row.cells[4].text, "AMT")

                # 判定邏輯：必須有 TXID 和 Amount 才視為有效交易
                if raw_txid and raw_amt:
                    # 使用 Validator 清洗資料用於 API 請求
                    clean_txid, _, _ = Validator.validate(raw_txid, "TXID")
                    clean_amt, _, _  = Validator.validate(raw_amt, "AMT")
                    clean_from, _, _ = Validator.validate(raw_from, "ADDR")
                    clean_to, _, _   = Validator.validate(raw_to, "ADDR")
                    clean_time, _, _ = Validator.validate(raw_time, "TIME")
                    
                    try: amt_val = float(clean_amt)
                    except: amt_val = 0.0

                    self.trace_requests.append({
                        "txh": clean_txid,
                        "chain": "TRON", "Token": "USDT",
                        "TimeStamp_UTC_8": clean_time if clean_time else row.cells[0].text.strip(),
                        "From": clean_from if clean_from else "",
                        "To": clean_to if clean_to else "",
                        "Amount": amt_val
                    })

            # ====== [Action B] 全域遮罩 (Global Masking) ======
            # 無差別遍歷這一列的 "每一個" 格子 (包含備註欄、第6欄以後...)
            # 不管 Action A 有沒有成功，這裡都要執行
            for cell in row.cells:
                self._scan_and_mask_content(cell)

    def _scan_and_mask_content(self, container):
        """
        [Action B 的核心] 通用掃描器
        適用於：Paragraph (段落), Table Cell (儲存格), Header/Footer
        功能：找出所有 TXID, ADDR, TIME, AMT 並遮罩
        """
        text = container.text
        if not text.strip(): return

        # 定義掃描順序：先長後短 (TXID -> ADDR -> TIME -> AMT)
        # 避免 ADDR 是 TXID 的一部分而被誤切
        scan_types = ["TXID", "ADDR", "TIME", "AMT"] 

        for dtype in scan_types:
            # 使用 find_all 找出 "所有" 符合項目 (不只第一個，避免漏網之魚)
            matches = Validator.find_all(container.text, dtype)
            
            for match in matches:
                raw_text = match.group(0)
                
                # 再次確認這個字串還在 (因為可能在迴圈中被前面的 mask 替換掉了)
                if raw_text in container.text:
                    self._mask_and_record(container, raw_text, dtype)

    def _mask_and_record(self, element, raw_text, type_prefix):
        """
        遮罩執行的原子操作：
        1. 給 ID
        2. 判斷狀態
        3. 寫 Mapping
        4. 替換文字
        """
        if not raw_text: return
        
        new_id = self._get_next_id(type_prefix)
        clean_val, status, err_msg = Validator.validate(raw_text, type_prefix)

        # 1. 寫入 Mapping 表 (這就是 Audit 的精髓：告訴下一個人錯在哪)
        self.mapping_list.append({
            "id": new_id, "type": type_prefix,
            "raw_text": raw_text, "clean_val": clean_val,
            "status": status, "error_msg": err_msg
        })

        # 2. 收集地址請求 (去重)
        if type_prefix == "ADDR" and clean_val:
            self.address_requests.add(clean_val)

        # 3. 執行遮罩 (修改 Word 物件)
        if hasattr(element, 'text'):
            element.text = element.text.replace(raw_text, new_id)