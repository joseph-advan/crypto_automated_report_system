# 檔名: automated_report_system/services/address_validator.py
#
# 職責：
# 提供一組「精確的」加密貨幣地址驗證函式。
# 這些函式使用密碼學校驗碼 (Checksum) 來驗證，
# 而不只是依賴寬鬆的正規表示式 (Regex)。
#
# 這將被 FileProcessor 用來過濾掉 Regex 誤抓的字串 (例如 TXID 碎片)。
#
# 需要安裝:
# pip install base58 bech32 web3

import re
import base58
import bech32
from web3 import Web3

def is_valid_btc(addr: str) -> bool:
    """
    使用 base58check 和 bech32 驗證 BTC 地址的校驗碼。
    這可以精確過濾掉 TXID 碎片。
    """
    try:
        if addr.startswith("1") or addr.startswith("3"):
            # 驗證 Legacy (P2PKH) 和 Nested SegWit (P2SH)
            # b58decode_check 會自動驗證 checksum，
            # 如果 checksum 錯誤 (例如：這是一個 TXID 碎片)，將會拋出 Exception。
            base58.b58decode_check(addr)
            return True
            
        elif addr.startswith("bc1"):
            # 驗證 Native SegWit (Bech32) 或 Taproot (Bech32m)
            # 必須至少成功解碼 "一種"
            
            hrp = None
            data = None
            spec = None

            try:
                # 嘗試 Bech32 (P2WPKH / P2WSH)
                spec = bech32.Encoding.BECH32
                hrp, data = bech32.decode(addr, encoding=spec)
            except Exception:
                pass # 失敗是正常的，繼續嘗試 Bech32m
            
            if hrp == 'bc' and data is not None:
                return True # 是合法的 Bech32

            try:
                # 嘗試 Bech32m (P2TR / Taproot)
                spec = bech32.Encoding.BECH32M
                hrp, data = bech32.decode(addr, encoding=spec)
            except Exception:
                pass # 兩種都失敗了
                
            if hrp == 'bc' and data is not None:
                return True # 是合法的 Bech32m
            
    except Exception:
        # 任何解碼或校驗碼錯誤（例如：無效的 Base58 字元、Checksum 失敗）
        return False
        
    return False

def is_valid_tron(addr: str) -> bool:
    """
    使用 base58check 驗證 Tron 地址 (T... 開頭)
    """
    try:
        # 1. 基本格式檢查
        if not addr.startswith("T") or len(addr) != 34:
            return False
        
        # 2. Checksum 驗證
        decoded = base58.b58decode_check(addr)
        
        # 3. Tron 特定格式驗證 (解碼後必須以 0x41 開頭)
        if decoded.hex().startswith("41"):
            return True
            
    except Exception:
        # Checksum 失敗或無效字元
        return False
        
    return False

def is_valid_eth(addr: str) -> bool:
    """
    使用 Web3.py 驗證 ETH 地址 (0x... 開頭)
    Web3.is_address 會處理 EIP-55 checksum 或全小寫/全大寫的地址
    """
    return Web3.is_address(addr)

def is_valid_txid(addr: str) -> bool:
    """
    驗證是否為標準的 64 位元十六進制字串 (TXID)
    這是一個格式檢查，而非 checksum 驗證。
    """
    # re.fullmatch 確保整個字串 100% 匹配
    return re.fullmatch(r"^[a-fA-F0-9]{64}$", addr) is not None