import json
import requests # 用來呼叫假裝的 Ground Truth API

class VerificationService:
    
    def __init__(self, api_endpoint):
        self.api_endpoint = api_endpoint
        self._mapping = {}
        self._reverse_mapping = {}

    def _load_mapping(self, map_path):
        """ 載入 mapping.json 並建立反向 mapping """
        with open(map_path, 'r', encoding='utf-8') as f:
            self._mapping = json.load(f)
        
        # 建立反向 mapping，用於「回向遮罩」
        self._reverse_mapping = {}
        for category, mappings in self._mapping.items():
            for real_val, mask_id in mappings.items():
                self._reverse_mapping[real_val] = mask_id
        print("  [Verifier] Mapping 表已載入並反轉。")

    def _de_mask_data(self, masked_data):
        """ 
        [步驟 7] 逆向還原 (De-masking)
        (這是一個簡化版本，實際應用中需要遞迴遍歷 JSON)
        """
        real_data = {}
        
        # 建立一個扁平化的 mapping (mask_id -> real_val)
        flat_mapping = {}
        for category, mappings in self._mapping.items():
            for real_val, mask_id in mappings.items():
                flat_mapping[mask_id] = real_val
                
        # 簡易示範：
        # 假設 masked_data = {"txid": "[TXID_001]", "sender": "[ADDR_002]"}
        # real_data 會變成 {"txid": "ee0c65a...", "sender": "TSaRZDi..."}
        
        # (樁函式：這裡應有遞迴 JSON 替換邏輯)
        print("  [Verifier] (樁函式) 執行逆向還原...")
        real_data = masked_data # 暫時跳過，假裝還原完畢
        return real_data # 應回傳 llm_extracted_REAL.json 的內容

    def _call_ground_truth_api(self, real_data):
        """ 
        [步驟 8] 呼叫標準答案 API
        (這是一個樁函式 (Stub)，假裝呼叫了 API)
        """
        print(f"  [Verifier] (樁函式) 正在呼叫 Ground Truth API: {self.api_endpoint}")
        # response = requests.post(self.api_endpoint, json=real_data)
        # return response.json()
        
        # --- 假裝 API 回傳了標準答案 ---
        return {
            "txid": "b8ffc91c7da1147ad1c8eb7134b8f21e00f2c940ffe473cb65eba2eb58f77992",
            "error": "交易數額錯誤", 
            "expected_amount": "20,410",
            "reported_amount": "20,410.7"
        } # 這是 ground_truth.json 的內容

    def _compare_and_diff(self, extracted_real_data, ground_truth_data):
        """
        [步驟 10] 執行差異比對
        (這是一個樁函式 (Stub))
        """
        print("  [Verifier] (樁函式) 正在執行差異比對...")
        # 這裡應有複雜的比對邏輯
        
        # --- 假裝比對出了差異 ---
        return {
             "wallet_errors": [
                {"address": "TXfMcg2kFqMb5xi91C4MGcFpq5z46daM7", "error": "地址格式錯誤"}
              ],
              "txid_errors": [
                {"txid": "b8ffc91c7da1147ad1c8eb7134b8f21e00f2c940ffe473cb65eba2eb58f77992", 
                 "error": "交易數額錯誤", 
                 "expected": "20,410",
                 "reported": "20,410.7"
                 }
              ]
        } # 這是 diff_report_REAL.json 的內容

    def _re_mask_data(self, real_diff_data):
        """
        [步驟 12] 執行「回向遮罩」
        (這是一個樁函式 (Stub)，使用 self._reverse_mapping)
        """
        print("  [Verifier] (樁函式) 正在執行回向遮罩...")
        # (樁函式：這裡應有遞迴 JSON 替換邏輯)
        
        # 假裝 real_diff_data = {"txid": "b8ffc...", "error": ...}
        # 替換後 -> {"txid": "[TXID_002]", "error": ...}
        
        masked_diff_data = real_diff_data # 暫時跳過，假裝遮罩完畢
        return masked_diff_data # 這是 diff_report_MASKED.json 的內容

    def verify_and_diff(self, masked_extraction_json, map_path):
        """
        [階段三 & 四] 的主函式
        協調所有本地機密作業
        """
        
        # 1. 載入金鑰
        self._load_mapping(map_path)
        
        # 2. [步驟 7] 還原
        real_data = self._de_mask_data(masked_extraction_json)
        
        # 3. [步驟 8 & 9] 驗證
        ground_truth_data = self._call_ground_truth_api(real_data)
        
        # 4. [步驟 10] 比對
        real_diff_data = self._compare_and_diff(real_data, ground_truth_data)
        
        # 5. [步驟 12] 再遮罩
        masked_diff_data = self._re_mask_data(real_diff_data)
        
        return masked_diff_data