# 檔名: automated_report_system/services/pre_check_service.py
#
# 職責：
# 模擬一個「預先檢查」階段。
# 讀取 mapping.json，並與一個 "標準答案" API 回應檔 (addressChech200OK.json) 進行比對。
# 產出一份預先檢查報告，說明 mapping 中的地址是否有格式錯誤或未通過 API 檢查。

import json
import os

class PreCheckService:
    
    def __init__(self):
        print("  [PreCheckService] 已初始化。")

    def _load_mapping_addresses(self, mapping_path):
        """
        載入 mapping.json 並提取所有被遮罩的 "真實地址" 列表。
        這模擬了「建立 API 請求主體」的過程。
        """
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            all_addresses = []
            # 遍歷所有類別 (ADDR_TRON, ADDR_BTC, TXID_GENERIC)
            for category_map in mapping_data.values():
                # .keys() 就是真實的地址/TXID
                all_addresses.extend(category_map.keys())
            
            print(f"  [PreCheckService] 從 Mapping 載入 {len(all_addresses)} 個地址/TXID。")
            return all_addresses
        except FileNotFoundError:
            print(f"  [PreCheckService] 錯誤: 找不到 Mapping 檔案: {mapping_path}")
            return []

    def _load_ground_truth_api(self, ground_truth_path):
        """
        載入 addressChech200OK.json 並建立一個 "地址 -> 檢查結果" 的查詢表。
        """
        try:
            with open(ground_truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            lookup_table = {}
            # 遍歷 results 列表
            for result in truth_data.get("results", []):
                address = result.get("inputQuery", {}).get("address")
                if address:
                    # 我們儲存 "formatCheck" 物件，因為那是我們關心的
                    lookup_table[address] = result.get("formatCheck", {})
            
            print(f"  [PreCheckService] 從 Ground Truth 載入 {len(lookup_table)} 筆 API 回應。")
            return lookup_table
        except FileNotFoundError:
            print(f"  [PreCheckService] 錯誤: 找不到 Ground Truth 檔案: {ground_truth_path}")
            print(f"  [PreCheckService] 請確認您已建立 'data/api_data/' 資料夾並放入檔案。")
            return {}
        except json.JSONDecodeError:
            print(f"  [PreCheckService] 錯誤: Ground Truth 檔案 JSON 格式錯誤: {ground_truth_path}")
            return {}

    def run_check(self, mapping_path, ground_truth_path, output_report_path):
        """
        [新階段] 主函式：比對 Mapping 與 API 標準答案
        """
        print(f"  [PreCheckService] 開始執行地址預先檢查...")
        
        # 1. 載入我們從 Word 抓到的地址 (from mapping.json)
        # 這模擬了 request body
        scraped_entities = self._load_mapping_addresses(mapping_path)
        
        # 2. 載入 "API" 的假回傳 (from addressChech200OK.json)
        api_results_lookup = self._load_ground_truth_api(ground_truth_path)
        
        comparison_results = []
        
        # 3. 開始比對
        for entity in scraped_entities:
            result_entry = {
                "entity": entity, # 地址或 TXID
                "status": "",
                "message": ""
            }
            
            if entity in api_results_lookup:
                # 在 "API 回應" 中找到了
                api_result = api_results_lookup[entity]
                api_message = api_result.get("message", "")
                
                if not api_message:
                    # Message 是空的，代表 API 認為 OK
                    result_entry["status"] = "Verified_OK"
                    result_entry["message"] = "此地址已在 API 檢查通過。"
                else:
                    # API 回傳了錯誤訊息! (例如 "未符合Tron地址格式")
                    result_entry["status"] = "Failed_Format"
                    result_entry["message"] = f"API 驗證失敗: {api_message}"
            else:
                # 在 "API 回應" 中 "沒有" 找到
                result_entry["status"] = "Not_Found_In_API"
                result_entry["message"] = "警告：此實體存在於報告中，但在 API 標準答案檔案中未找到。"
            
            comparison_results.append(result_entry)
        
        # 4. 儲存比對報告
        with open(output_report_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_results, f, indent=4, ensure_ascii=False)
            
        print(f"  [PreCheckService] 預先檢查完成。報告已儲存: {output_report_path}")