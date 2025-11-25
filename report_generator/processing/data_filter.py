import json
import os

class DataFilter:
    """
    負責對 DataIntegrator 整合後的資料進行篩選。
    核心目標：只保留「有問題」的項目，過濾掉「完全正確」的項目，
    以減少 LLM 的 Context loading 並降低幻覺風險。
    """

    def __init__(self):
        pass

    def filter_anomalies(self, augmented_entities):
        """
        篩選邏輯：
        1. 保留 `local_status != 0` 的項目 (本地格式錯誤)。
        2. 保留 `api_result` 顯示驗證失敗的項目 (鏈上數據錯誤)。
        3. 丟棄完全正確的項目 (Local OK + API OK)。
        
        Args:
            augmented_entities (list): 來自 DataIntegrator 的完整實體清單。
            
        Returns:
            list: 篩選後的實體清單 (只包含異常項目)。
        """
        filtered_list = []
        
        print(f"[DataFilter] 開始篩選異常項目 (輸入: {len(augmented_entities)} 筆)...")
        
        for entity in augmented_entities:
            
            # 1. 取得基本資訊
            local_status = entity.get("local_validation", {}).get("status", 0)
            entity_type = entity.get('type')
            api_verification = entity.get('api_verification') 
            
            is_api_failed = False # 預設 API 驗證通過 (或沒驗證)

            # 2. 判斷 API 是否失敗
            if api_verification:
                if entity_type == 'ADDR':
                    # ADDR 判斷標準: formatCheck.message 不為空，表示有錯誤
                    # 或是 formatCheck.isPassed 為 False (視 API 結構而定)
                    fmt = api_verification.get('formatCheck', {})
                    if fmt.get('message') or fmt.get('isPassed') is False: 
                        is_api_failed = True
                
                elif entity_type == 'TXID':
                    # TXID 判斷標準: formatCheck.isPassed 為 False
                    fmt = api_verification.get('formatCheck', {})
                    if fmt.get('isPassed') is False:
                        is_api_failed = True

            # 3. 核心篩選邏輯
            # 如果 (本地有錯) 或 (API 有錯)，才加入清單
            if local_status != 0 or is_api_failed:
                filtered_list.append(entity)

        print(f"[DataFilter] 篩選完成。保留 {len(filtered_list)} 筆異常項目。")
        return filtered_list

    def save_payload(self, data, output_path):
        """
        將篩選後的資料儲存為 JSON 檔案，供使用者檢查。
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[DataFilter] 篩選後的 Payload 已儲存至: {output_path}")
        except Exception as e:
            print(f"[DataFilter] 儲存 Payload 失敗: {e}")
