import re

class Validator:
    # 定義 Regex (AMT 必須嚴格，以免誤抓頁碼)
    PATTERNS = {
        "ADDR": re.compile(r'(?<![a-zA-Z0-9])T[\w\s]{30,50}(?![a-zA-Z0-9])'),
        # 金額: 允許含逗號或小數點的數字
        "AMT": re.compile(r'(?<![\d\.])([\d\s,]+\.[\d\s]+|[\d]{1,3}(,[\d]{3})+)(?![%])'),
        "TXID": re.compile(r'(?<![a-fA-F0-9])[a-fA-F0-9\s]{60,70}(?![a-fA-F0-9])'),
        "TIME": re.compile(r'\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\s+\d{1,2}[:;]\d{1,2}[:;]\d{1,2}')
    }

    @staticmethod
    def validate(raw_text, type_prefix):
        """
        分析原始文字，回傳 (cleaned_value, status_code, error_msg)
        """
        if not raw_text:
            return None, 0, "Empty"

        clean_val = raw_text.strip()
        status = 0
        msg = []

        # --- [修改重點] TXID 特殊處理 ---
        if type_prefix == "TXID":
            # 如果是 TXID，我們允許空格 (視為換行)，直接清除且「不報錯」 (Status 保持 0)
            if " " in clean_val:
                clean_val = clean_val.replace(" ", "")
            # 檢查長度 (TRON TXID 固定 64 碼)
            if len(clean_val) != 64:
                status = max(status, 3)
                msg.append(f"Length mismatch ({len(clean_val)})")

        # --- 其他類型 (維持嚴格檢查) ---
        else:
            # 對 ADDR, AMT, TIME 來說，中間有空格就是格式錯誤
            if " " in clean_val:
                status = 1
                msg.append("Contains spaces")
                clean_val = clean_val.replace(" ", "")

            # 特定格式檢查
            if type_prefix == "AMT":
                clean_val = clean_val.replace(",", "")
                try:
                    float(clean_val)
                except ValueError:
                    status = max(status, 2)
                    msg.append("Invalid number format")

            elif type_prefix == "TIME":
                if ";" in clean_val:
                    status = max(status, 2)
                    msg.append("Invalid time separator ';'")
                    clean_val = clean_val.replace(";", ":")
                if "-:" in clean_val:
                    status = max(status, 2)
                    msg.append("Typos in timestamp")
                    clean_val = clean_val.replace("-:", ":")

            elif type_prefix == "ADDR":
                if len(clean_val) != 34:
                    status = max(status, 3)
                    msg.append(f"Length mismatch ({len(clean_val)})")

        error_message = "; ".join(msg) if msg else None
        return clean_val, status, error_message

    # ... (extract_first, find_all 保持原樣) ...
    @staticmethod
    def extract_first(text, type_prefix):
        if not text: return None
        pattern = Validator.PATTERNS.get(type_prefix)
        match = pattern.search(text)
        if match: return match.group(0)
        return None

    @staticmethod
    def find_all(text, type_prefix):
        if not text: return []
        pattern = Validator.PATTERNS.get(type_prefix)
        return list(pattern.finditer(text))