"""
Utility functions for Vector Database MCP Server
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional


# ========================================================
# JSON Serialization with datetime support
# ========================================================

class DateTimeEncoder(json.JSONEncoder):
    """datetime オブジェクトを自動的に ISO 文字列に変換する JSON エンコーダー"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    datetime 対応の安全な JSON シリアライゼーション
    
    Args:
        obj: JSON化するオブジェクト
        **kwargs: json.dumps に渡す追加パラメータ
        
    Returns:
        JSON文字列
    """
    return json.dumps(obj, cls=DateTimeEncoder, **kwargs)


def datetime_hook(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSON から読み込み時に ISO 文字列を datetime に変換（安全版）
    
    Args:
        obj: JSONオブジェクト
        
    Returns:
        変換後のオブジェクト
    """
    if not isinstance(obj, dict):
        return obj
    
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                # ISO 形式の文字列を datetime に変換を試行
                if 'T' in value and ('.' in value or '+' in value or 'Z' in value):
                    # より厳密な検証
                    if len(value) >= 19 and value.count('T') == 1:
                        obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError, TypeError):
                # 変換失敗は無視して元の値を保持
                pass
    return obj


def safe_json_loads(s: str, **kwargs) -> Any:
    """
    datetime 対応の安全な JSON デシリアライゼーション
    
    Args:
        s: JSON文字列
        **kwargs: json.loads に渡す追加パラメータ
        
    Returns:
        Pythonオブジェクト
    """
    return json.loads(s, object_hook=datetime_hook, **kwargs)


# ========================================================
# ChromaDB Metadata Processing
# ========================================================

def filter_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChromaDB用にメタデータからNone値を除外し、型を適切に変換
    
    Args:
        metadata: 元のメタデータ
        
    Returns:
        フィルタリング済みメタデータ
    """
    filtered = {}
    for key, value in metadata.items():
        if value is not None:
            # 型の明示的変換
            if isinstance(value, (int, float, bool)):
                filtered[key] = value
            elif isinstance(value, str):
                filtered[key] = value
            else:
                # その他の型は文字列に変換
                filtered[key] = str(value)
    return filtered


def safe_metadata_value(value: Any, default_value: Any = "") -> Any:
    """
    ChromaDB用の安全なメタデータ値変換
    
    Args:
        value: 変換する値
        default_value: Noneの場合のデフォルト値
        
    Returns:
        安全な値
    """
    if value is None:
        return default_value
    
    if isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        return value
    else:
        return str(value)


# ========================================================
# General Utilities
# ========================================================

def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    テキストを指定長で切り詰める
    
    Args:
        text: 切り詰めるテキスト
        max_length: 最大長
        suffix: 切り詰め時の接尾辞
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    2つの辞書を深くマージする
    
    Args:
        dict1: ベース辞書
        dict2: マージする辞書
        
    Returns:
        マージされた辞書
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    ネストされた辞書から値を取得
    
    Args:
        data: 辞書
        path: ドット区切りのパス (e.g., "a.b.c")
        default: デフォルト値
        
    Returns:
        取得した値またはデフォルト値
    """
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """
    ネストされた辞書に値を設定
    
    Args:
        data: 辞書
        path: ドット区切りのパス (e.g., "a.b.c")
        value: 設定する値
    """
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    タイムスタンプをフォーマット
    
    Args:
        dt: datetime オブジェクト（Noneの場合は現在時刻）
        format_str: フォーマット文字列
        
    Returns:
        フォーマットされた文字列
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)
