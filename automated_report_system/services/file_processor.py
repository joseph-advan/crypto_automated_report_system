import docx
import re
import os
import json
from . import address_validator  # <-- [新加入的行]
# (這裡的程式碼與您 v3.1 腳本幾乎相同，只是封裝成一個類別)

class FileProcessor:
    
    def __init__(self):
        # [修改] 
        # 舊模式 (錯誤的): r'\bT[...]{33}\b'
        # 新模式 (正確的): r'T(\s*[...]){33}'
        self.patterns = {
            # 匹配 "T" 
            # 接著匹配 "任意空白 + 1個TRON字元" (這個群組)
            # ... {33} 次
            "ADDR_TRON": re.compile(r'T(\s*[a-km-zA-NP-Z1-9]){33}'),
            
            # 匹配 "0x"
            # 接著匹配 "任意空白 + 1個HEX字元" (這個群組)
            # ... {40} 次
            "ADDR_ETH": re.compile(r'0x(\s*[a-fA-F0-9]){40}'),
            
            # 匹配 "1"
            # 接著匹配 "任意空白 + 1個BTC字元" (這個群組)
            # ... {25, 33} 次
            "ADDR_BTC_P2PKH": re.compile(r'1(\s*[a-km-zA-NP-Z1-9]){25,33}'),
            "ADDR_BTC_P2SH": re.compile(r'3(\s*[a-km-zA-NP-Z1-9]){25,33}'),
            
            # 匹配 "bc1"
            # 接著匹配 "任意空白 + 1個BECH32字元" (這個群組)
            # ... {39, 59} 次
            "ADDR_BTC_BECH32": re.compile(r'bc1(\s*[a-z0-9]){39,59}'),
            
            # 匹配 "1個HEX字元"
            # 接著匹配 "任意空白 + 1個HEX字元" (這個群組)
            # ... {63} 次
            "TXID_GENERIC": re.compile(r'[a-fA-F0-9](\s*[a-fA-F0-9]){63}')
        }
        self.mapping_data = {
            "ADDR_TRON": {}, "ADDR_ETH": {}, "ADDR_BTC": {}, "TXID_GENERIC": {}
        }
        self.formatting_errors = []

    def _get_unique_id(self, match_obj, prefix):
        original_string = match_obj.group(0)
        
        # 步驟 1: 清理字串 (不變)
        # 移除所有空白字元 (包含 space 和 newline)，用於 "驗證" 和 "mapping key"
        canonical_string = re.sub(r'\s+', '', original_string)
        
        # 步驟 2: [新] 檢查 "錯誤"
        # 根據您的新規則：只將 "空格" (space) 視為錯誤
        # "換行" (\n) 是可接受的，不視為錯誤。
        has_formatting_error = " " in original_string  # <-- [關鍵修改]
        
        # 步驟 3: 呼叫驗證器 (不變)
        is_valid = False
        if "BTC" in prefix:
            is_valid = address_validator.is_valid_btc(canonical_string)
        elif "TRON" in prefix:
            is_valid = address_validator.is_valid_tron(canonical_string)
        elif "ETH" in prefix:
            is_valid = address_validator.is_valid_eth(canonical_string)
        elif "TXID" in prefix:
            is_valid = address_validator.is_valid_txid(canonical_string)
        
        # 步驟 4: 驗證閘門 (不變)
        if not is_valid:
            # 驗證失敗 (例如：這是一個 TXID 碎片)
            return original_string

        # --- 驗證通過 ---
        
        # 步驟 5: [新] 記錄錯誤
        # 只有在 "驗證通過" 且 "偵測到空格" 時，才記錄錯誤
        if has_formatting_error:
            error_record = {
                "original_text": original_string.replace("\n", "\\n"), # 顯示換行符
                "corrected_address": canonical_string,
                "type_detected": prefix,
                "warning": "偵測到不必要的空格 (space)，已被自動修正。"
            }
            # 避免重複記錄
            if error_record not in self.formatting_errors:
                self.formatting_errors.append(error_record)

        # 步驟 6: 執行遮罩 (不變)
        map_key = "ADDR_BTC" if "BTC" in prefix else prefix
        current_map = self.mapping_data[map_key]
        
        if canonical_string not in current_map:
            new_id = f"[{map_key}_{len(current_map) + 1:03d}]"
            current_map[canonical_string] = new_id
            
        # 步驟 7: 回傳遮罩 ID (不變)
        return current_map[canonical_string]
    
    def _process_run(self, run):
        if not run.text:
            return
        for prefix, pattern in self.patterns.items():
            replacer = lambda match: self._get_unique_id(match, prefix)
            run.text = pattern.sub(replacer, run.text)

    # (刪除 _process_run 函式，它不再被需要)
    # def _process_run(self, run):
    #     ...

    def mask_and_create_mapping(self, input_path, output_path, mapping_path):
        """
        [階段一] 的主函式 (修改後：在段落層級處理)
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到輸入檔案: {input_path}")
            
        # [修改] 重置 mapping 和 錯誤列表
        self.mapping_data = {k: {} for k in self.mapping_data}
        self.formatting_errors = []

        doc = docx.Document(input_path)
        
        # [修改] 替換邏輯：直接處理 Paragraph.text
        def process_paragraph_text(para):
            if not para.text:
                return
            # (注意：這會失去原始樣式，但在 LLM 階段沒問題)
            new_text = para.text
            for prefix, pattern in self.patterns.items():
                replacer = lambda match: self._get_unique_id(match, prefix)
                # re.sub 會處理段落中所有的匹配，包含跨行
                new_text = pattern.sub(replacer, new_text)
            
            # 如果文字有變動，才清空重寫
            if new_text != para.text:
                para.clear() # 清空所有舊的 run
                para.add_run(new_text) # 加入一個包含已遮罩文字的新 run
        
        # [修改] 遍歷所有段落
        for para in doc.paragraphs:
            process_paragraph_text(para)

        # [修改] 遍歷所有表格
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        process_paragraph_text(para)
        
        doc.save(output_path)
        
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.mapping_data, f, indent=4, ensure_ascii=False)
            
        print(f"  [FileProcessor] 遮罩完成: {output_path}")
        print(f"  [FileProcessor] Mapping 表已儲存: {mapping_path}")

        # --- [新加入的程式碼] ---
        # 在儲存前，對錯誤報告進行排序
        print("  [FileProcessor] 正在排序錯誤報告...")
        def sort_key(error_record):
            """
            定義排序規則：
            - 地址 (ADDR_TRON, ADDR_BTC 等) 回傳 0
            - TXID (TXID_GENERIC) 回傳 1
            """
            if error_record.get("type_detected") == "TXID_GENERIC":
                return 1  # TXID 往後排
            else:
                return 0  # 地址 (ADDR_*) 往前排
        
        self.formatting_errors.sort(key=sort_key)
        # --- [新加入的程式碼結束] ---
        
        error_report_path = os.path.join(os.path.dirname(mapping_path), "formatting_errors.json")
        with open(error_report_path, 'w', encoding='utf-8') as f:
            json.dump(self.formatting_errors, f, indent=4, ensure_ascii=False)
        
        if self.formatting_errors:
            print(f"  [FileProcessor] [警告] 偵測到 {len(self.formatting_errors)} 筆格式錯誤，報告已儲存: {error_report_path}")
        else:
            print(f"  [FileProcessor] 未偵測到格式錯誤。")