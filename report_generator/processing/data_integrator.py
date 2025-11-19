# 檔案位置: report_generator/processing/data_integrator.py
# (這是完整的、已修改的版本)

import json
import os
import config # 載入我們剛修改的 config

class DataIntegrator:
    """
    負責整合來自 AuditProcessor 的本地驗證檔 (mapping.json)
    以及外部 API 的真實性驗證檔 (addressChech200OK.json, txhCheck200OK.json)。
    """
    
    # --- [ critical ] 修改 ---
    def __init__(self, mapping_path, address_api_path, txh_api_path): # 變數名稱更新
        """
        初始化整合器並傳入所有需要的檔案路徑。
        """
        self.mapping_path = mapping_path
        self.address_api_path = address_api_path
        self.txh_api_path = txh_api_path # 變數名稱更新
        
        # 驗證所有檔案都存在
        check_paths = [mapping_path, address_api_path, txh_api_path]
        if not all(os.path.exists(p) for p in check_paths):
            missing = [p for p in check_paths if not os.path.exists(p)]
            # 提出更具體的警告
            if txh_api_path in missing:
                 print(f"警告: 找不到 TXH API 回應檔: {txh_api_path}")
                 print("請確認 txhCheck200OK.json 已放置在 automated_report_system/data/api_data_txh/ 資料夾中")
            if address_api_path in missing:
                 print(f"警告: 找不到 Address API 回應檔: {address_api_path}")
                 print("請確認 addressChech200OK.json 已放置在 automated_report_system/data/api_data/ 資料夾中")
            
            raise FileNotFoundError(f"資料整合器錯誤：找不到必要的檔案：{', '.join(missing)}")
    # --- [修改完畢] ---

    def _load_json(self, file_path):
        """
        一個安全的 JSON 讀取輔助函式。 (不變)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"錯誤: 解析 JSON 失敗 {file_path}")
            return None
        except Exception as e:
            print(f"讀取檔案時發生錯誤 {file_path}: {e}")
            return None

    def integrate_data(self):
        """
        執行資料整合。
        (此函式中的 TXID 讀取邏輯已完全重寫)
        """
        print(f"[DataIntegrator] 開始整合資料...")

        # 1. 載入基礎 mapping (from mapping.json) (不變)
        report_entities = self._load_json(self.mapping_path)
        if report_entities is None:
            print(f"[DataIntegrator] 嚴重錯誤: 無法讀取 mapping.json {self.mapping_path}")
            return []
        print(f"[DataIntegrator] 成功載入 {len(report_entities)} 筆本地實體 (from mapping.json)")

        # 2. 載入 Address API 回應 (from addressChech200OK.json) (不變)
        address_data = self._load_json(self.address_api_path)
        address_api_results = {}
        if address_data and 'results' in address_data:
            for result in address_data['results']:
                key = result.get('inputQuery', {}).get('address')
                if key:
                    address_api_results[key] = result
        print(f"[DataIntegrator] 成功索引 {len(address_api_results)} 筆地址 API 回應")

        # --- [ critical ] 修改 ---
        # 3. 載入 TXH Check API 回應 (from txhCheck200OK.json)
        txh_data = self._load_json(self.txh_api_path) # self.txh_api_path 是新路徑
        tx_api_results = {}
        
        # 新的 txhCheck200OK.json 結構是: {"results": {"txh1...": {...}, "txh2...": {...}}}
        if txh_data and 'results' in txh_data and isinstance(txh_data['results'], dict):
            # 'results' 本身就是一個以 TXID 為 key 的字典，我們可以直接使用
            tx_api_results = txh_data['results']
            print(f"[DataIntegrator] 成功索引 {len(tx_api_results)} 筆 TXH API 回應 (新格式)")
        else:
            print(f"[DataIntegrator] 警告: 未能從 {self.txh_api_path} 載入 TXH API 回應，或格式不符。")
        # --- [修改完畢] ---


        # 4. 遍歷 "事實基礎"，並注入 API 驗證結果
        augmented_entities = []
        for entity in report_entities:
            clean_val = entity.get('clean_val')
            if not clean_val:
                continue

            # a. 整理本地驗證狀態 (不變)
            entity['local_validation'] = {
                "status": entity.get("status"),
                "error_msg": entity.get("error_msg")
            }

            # b. 注入 API 驗證結果
            api_verification = None
            if entity.get('type') == 'ADDR':
                if clean_val in address_api_results:
                    api_verification = address_api_results[clean_val]
                else:
                    print(f"[DataIntegrator] 警告 (ADDR): {clean_val} 在 API 回應中未找到。")
            
            # --- [ critical ] 修改 ---
            elif entity.get('type') == 'TXID':
                if clean_val in tx_api_results:
                    # 直接獲取該 TXID 的驗證結果物件
                    # (例如: {"status": "Invalid", "message": "Tx hash format is invalid"})
                    api_verification = tx_api_results[clean_val]
                else:
                    # 即使在 txh_check_requests 中，API 也可能沒有回傳 (例如 API 內部錯誤)
                    print(f"[DataIntegrator] 警告 (TXID): {clean_val} 在 API 回應中未找到。")
            # --- [修改完畢] ---

            entity['api_verification'] = api_verification
            
            # 清理原始 mapping.json 的頂層欄位 (不變)
            entity.pop("status", None)
            entity.pop("error_msg", None)
            
            augmented_entities.append(entity)

        print(f"[DataIntegrator] 資料整合完成。共 {len(augmented_entities)} 筆豐富化實體準備完畢。")
        return augmented_entities

# --- 用於獨立測試的程式碼 (修改) ---
if __name__ == "__main__":
    
    print("="*50)
    print("=== 執行 DataIntegrator 獨立測試 ===")
    print("="*50)
    
    import sys
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPORT_GENERATOR_DIR = os.path.dirname(CURRENT_DIR)
    sys.path.append(REPORT_GENERATOR_DIR)
    
    try:
        import config 
    except ImportError as e:
        print(f"\n[測試失敗] 無法匯入 config: {e}")
        sys.exit(1)

    try:
        # 3. 初始化整合器 (使用 config 中定義的新變數)
        integrator = DataIntegrator(
            mapping_path=config.MAPPING_FILE,
            address_api_path=config.ADDRESS_API_RESPONSE_FILE,
            txh_api_path=config.TXH_API_RESPONSE_FILE # <--- [修改]
        )

        # 4. 執行整合
        augmented_data = integrator.integrate_data()

        if augmented_data:
            print("\n" + "="*50)
            print("=== 測試成功：整合結果 (前 3 筆) ===")
            print(json.dumps(augmented_data[:3], indent=2, ensure_ascii=False))
            
            # 儲存一份整合後的檔案，方便除錯
            os.makedirs(config.OUTPUT_REPORT_DIR, exist_ok=True)
            with open(config.DEBUG_AUGMENTED_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(augmented_data, f, indent=2, ensure_ascii=False)
            print(f"\n[測試] 完整的整合資料已儲存至: {config.DEBUG_AUGMENTED_DATA_FILE}")

    except FileNotFoundError as e:
        print(f"\n[測試失敗] {e}")
        print("請確認 automated_report_system/data/ 目錄下是否已包含必要的 JSON 檔案。")
    except Exception as e:
        print(f"\n[測試] 測試時發生未預期錯誤: {e}")