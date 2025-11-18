# 檔案: automated_report_system/services/validator.py
import re

class Validator:
    """
    負責定義寬鬆的 Regex 規則，以及判斷資料狀態 (Status Code)。
    """

    # --- [定義寬鬆的 Regex] ---
    # 這些 Regex 的目的是 "盡可能抓到目標，即使格式有點錯"
    PATTERNS = {
        # 地址: 抓取 T 開頭，長度在 30~50 之間，允許中間有空白 (\s)
        "ADDR": re.compile(r'(?<![a-zA-Z0-9])T[\w\s]{30,50}(?![a-zA-Z0-9])'),
        
        # 金額: 抓取數字組合，允許逗號、空格，且必須有小數點
        # 例如: "104,811 .79", "1000.00"
        "AMT": re.compile(r'(?<![\d\.])([\d\s,]+\.[\d\s]+|[\d]{1,3}(,[\d]{3})+)(?![%])'),
        
        # TXID: 抓取 64 位 HEX，允許長度略有出入 (60~70)，允許中間有空白
        "TXID": re.compile(r'(?<![a-fA-F0-9])[a-fA-F0-9\s]{60,70}(?![a-fA-F0-9])'),
        
        # 時間: 簡單抓取 YYYY/MM/DD 或 YYYY-MM-DD 開頭的字串
        "TIME": re.compile(r'\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\s+\d{1,2}[:;]\d{1,2}[:;]\d{1,2}')
    }

    @staticmethod
    def validate(raw_text, type_prefix):
        """
        分析原始文字，回傳 (cleaned_value, status_code, error_msg)
        Status Code:
          0: OK
          1: 包含空格 (Space Error)
          2: 符號錯誤 (Symbol Error) - 如逗號錯置、分號代替冒號
          3: 格式/長度錯誤 (Format Error)
        """
        if not raw_text:
            return None, 0, "Empty"

        clean_val = raw_text.strip()
        status = 0
        msg = []

        # --- 檢查 1: 空格錯誤 ---
        # 如果字串中間有空格 (前後空格已被 strip 去除)
        if " " in clean_val:
            status = 1
            msg.append("Contains spaces")
            clean_val = clean_val.replace(" ", "")

        # --- 檢查 2: 符號與格式特定檢查 ---
        if type_prefix == "AMT":
            # 移除逗號以便轉型
            if "," in clean_val:
                # 簡單檢查: 逗號後應該有3位數字 (簡易版)
                pass 
            clean_val = clean_val.replace(",", "")
            
            try:
                float(clean_val)
            except ValueError:
                status = max(status, 2) # 升級錯誤
                msg.append("Invalid number format")

        elif type_prefix == "TIME":
            # 修正常見的時間分隔符錯誤 (例如 16;20 -> 16:20)
            if ";" in clean_val:
                status = max(status, 2)
                msg.append("Invalid time separator ';'")
                clean_val = clean_val.replace(";", ":")
            # 修正日期分隔符 (例如 01:04-:15 -> 01:04:15)
            if "-:" in clean_val:
                status = max(status, 2)
                msg.append("Typos in timestamp")
                clean_val = clean_val.replace("-:", ":")

        elif type_prefix == "ADDR":
            # 檢查長度 (TRON 地址通常是 34 位)
            if len(clean_val) != 34:
                status = max(status, 3)
                msg.append(f"Length mismatch ({len(clean_val)})")

        elif type_prefix == "TXID":
            # 檢查長度 (TXID 通常是 64 位)
            if len(clean_val) != 64:
                status = max(status, 3)
                msg.append(f"Length mismatch ({len(clean_val)})")

        error_message = "; ".join(msg) if msg else None
        return clean_val, status, error_message

    @staticmethod
    def extract_first(text, type_prefix):
        """
        從一段文字中，使用 Regex 抓取「第一個」符合的字串。
        用於從 Table Cell 中提取資料。
        """
        if not text: return None
        pattern = Validator.PATTERNS.get(type_prefix)
        match = pattern.search(text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def find_all(text, type_prefix):
        """
        從一段文字中，抓取「所有」符合的字串。
        用於掃描段落。
        """
        if not text: return []
        pattern = Validator.PATTERNS.get(type_prefix)
        return list(pattern.finditer(text))