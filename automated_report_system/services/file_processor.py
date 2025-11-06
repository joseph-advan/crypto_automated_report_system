import docx
import re
import os
import json

# (這裡的程式碼與您 v3.1 腳本幾乎相同，只是封裝成一個類別)

class FileProcessor:
    
    def __init__(self):
        # 定義規則
        self.patterns = {
            "ADDR_TRON": re.compile(r'\bT[a-km-zA-NP-Z1-9]{33}\b'),
            "ADDR_ETH": re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
            "ADDR_BTC_P2PKH": re.compile(r'\b1[a-km-zA-NP-Z1-9]{25,33}\b'),
            "ADDR_BTC_P2SH": re.compile(r'\b3[a-km-zA-NP-Z1-9]{25,33}\b'),
            "ADDR_BTC_BECH32": re.compile(r'\bbc1[a-z0-9]{39,59}\b'),
            "TXID_GENERIC": re.compile(r'\b[a-fA-F0-9]{64}\b')
        }
        self.mapping_data = {
            "ADDR_TRON": {}, "ADDR_ETH": {}, "ADDR_BTC": {}, "TXID_GENERIC": {}
        }

    def _get_unique_id(self, match_obj, prefix):
        original_string = match_obj.group(0)
        map_key = "ADDR_BTC" if "BTC" in prefix else prefix
        current_map = self.mapping_data[map_key]
        
        if original_string not in current_map:
            new_id = f"[{map_key}_{len(current_map) + 1:03d}]"
            current_map[original_string] = new_id
        return current_map[original_string]

    def _process_run(self, run):
        if not run.text:
            return
        for prefix, pattern in self.patterns.items():
            replacer = lambda match: self._get_unique_id(match, prefix)
            run.text = pattern.sub(replacer, run.text)

    def mask_and_create_mapping(self, input_path, output_path, mapping_path):
        """
        [階段一] 的主函式
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到輸入檔案: {input_path}")
            
        # 重置 mapping
        self.mapping_data = {k: {} for k in self.mapping_data}
            
        doc = docx.Document(input_path)
        
        for para in doc.paragraphs:
            for run in para.runs:
                self._process_run(run)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            self._process_run(run)
        
        doc.save(output_path)
        
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.mapping_data, f, indent=4, ensure_ascii=False)
            
        print(f"  [FileProcessor] 遮罩完成: {output_path}")
        print(f"  [FileProcessor] Mapping 表已儲存: {mapping_path}")