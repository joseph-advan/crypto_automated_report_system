# 檔案位置: report_generator/processing/data_integrator.py
import json
import os
import config

class DataIntegrator:
    """
    負責整合來自 AuditProcessor 的本地驗證檔 (mapping.json)
    以及外部 API 的真實性驗證檔 (addressChech200OK.json, txhCheck200OK.json)。
    """
    
    def __init__(self, mapping_path, address_api_path, txh_api_path):
        """
        初始化整合器並傳入所有需要的檔案路徑。
        """
        self.mapping_path = mapping_path
        self.address_api_path = address_api_path
        self.txh_api_path = txh_api_path
        
        # 驗證所有檔案都存在
        check_paths = [mapping_path, address_api_path, txh_api_path]
        if not all(os.path.exists(p) for p in check_paths):
            missing = [p for p in check_paths if not os.path.exists(p)]
            if txh_api_path in missing:
                 print(f"警告: 找不到 TXH API 回應檔: {txh_api_path}")
            if address_api_path in missing:
                 print(f"警告: 找不到 Address API 回應檔: {address_api_path}")
            
            raise FileNotFoundError(f"資料整合器錯誤：找不到必要的檔案：{', '.join(missing)}")

    def _load_json(self, file_path):
        """一個安全的 JSON 讀取輔助函式。"""
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
        """
        print(f"[DataIntegrator] 開始整合資料...")

        # 1. 載入基礎 mapping (from mapping.json)
        report_entities = self._load_json(self.mapping_path)
        if report_entities is None:
            print(f"[DataIntegrator] 嚴重錯誤: 無法讀取 mapping.json {self.mapping_path}")
            return []
        print(f"[DataIntegrator] 成功載入 {len(report_entities)} 筆本地實體 (from mapping.json)")

        # 2. 載入 Address API 回應
        address_data = self._load_json(self.address_api_path)
        address_api_results = {}
        if address_data and 'results' in address_data:
            # 解析 List 格式
            for result in address_data['results']:
                # 嘗試從 inputQuery 取得 address
                key = result.get('inputQuery', {}).get('address')
                if key:
                    address_api_results[key] = result
        print(f"[DataIntegrator] 成功索引 {len(address_api_results)} 筆地址 API 回應")

        # --- [修改重點] ---
        # 3. 載入 TXH Check API 回應 (適應 List 格式)
        txh_data = self._load_json(self.txh_api_path)
        tx_api_results = {}
        
        if txh_data and 'results' in txh_data:
            results_list = txh_data['results']
            # 判斷是否為 List
            if isinstance(results_list, list):
                for result in results_list:
                    # 從 inputQuery 中提取 txh 作為 key
                    key = result.get('inputQuery', {}).get('txh')
                    if key:
                        # 為了讓 LLM 容易讀，我們只存需要的部分，或者存整個物件
                        # 這裡我們存整個 result，後續再處理
                        tx_api_results[key] = result
                print(f"[DataIntegrator] 成功索引 {len(tx_api_results)} 筆 TXH API 回應 (List 格式)")
            elif isinstance(results_list, dict):
                 # 相容舊格式 (以防萬一)
                 tx_api_results = results_list
                 print(f"[DataIntegrator] 成功索引 {len(tx_api_results)} 筆 TXH API 回應 (Dict 格式)")
        else:
            print(f"[DataIntegrator] 警告: 未能從 {self.txh_api_path} 載入 TXH API 回應，或格式不符。")
        # --- [修改結束] ---


        # 4. 遍歷 "事實基礎"，並注入 API 驗證結果
        augmented_entities = []
        for entity in report_entities:
            clean_val = entity.get('clean_val')
            if not clean_val:
                continue

            # a. 整理本地驗證狀態
            entity['local_validation'] = {
                "status": entity.get("status"),
                "error_msg": entity.get("error_msg")
            }

            # b. 注入 API 驗證結果
            api_verification = None
            
            if entity.get('type') == 'ADDR':
                if clean_val in address_api_results:
                    # 這裡我們提取 formatCheck 或是 chainScanResults
                    full_res = address_api_results[clean_val]
                    # 簡化給 LLM 看的資料
                    api_verification = {
                        "formatCheck": full_res.get("formatCheck"),
                        "chainData": full_res.get("chainScanResults")
                    }
                else:
                    # 只有當這個地址確實存在於 mapping 但 API 沒回傳時才警告
                    pass 
            
            elif entity.get('type') == 'TXID':
                if clean_val in tx_api_results:
                    full_res = tx_api_results[clean_val]
                    # 簡化給 LLM 看的資料
                    api_verification = {
                        "formatCheck": full_res.get("formatCheck"),
                        "chainData": full_res.get("chainScanResults")
                    }
                else:
                    pass
            
            entity['api_verification'] = api_verification
            
            # 清理不必要的欄位
            entity.pop("status", None)
            entity.pop("error_msg", None)
            
            augmented_entities.append(entity)

        print(f"[DataIntegrator] 資料整合完成。共 {len(augmented_entities)} 筆豐富化實體準備完畢。")
        return augmented_entities