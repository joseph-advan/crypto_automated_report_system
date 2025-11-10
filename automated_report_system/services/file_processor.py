import docx
import re
import os
import json

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

    def _get_unique_id(self, match_obj, prefix):
        original_string = match_obj.group(0)
        
        # [新] 清理字串，移除所有空白和換行
        canonical_string = re.sub(r'\s+', '', original_string)
        
        map_key = "ADDR_BTC" if "BTC" in prefix else prefix
        current_map = self.mapping_data[map_key]
        
        # [修改] 使用清理過的 "canonical_string" 作為 Key
        if canonical_string not in current_map:
            new_id = f"[{map_key}_{len(current_map) + 1:03d}]"
            current_map[canonical_string] = new_id
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
            
        self.mapping_data = {k: {} for k in self.mapping_data}
            
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