"""
Utility functions for Vector Database MCP Server
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from decimal import Decimal


# ========================================================
# NumPy型変換
# ========================================================

def convert_numpy_types(obj: Any) -> Any:
    """
    NumPy型を再帰的にPython標準型に変換
    
    Args:
        obj: 変換するオブジェクト
        
    Returns:
        Python標準型に変換されたオブジェクト
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(v) for v in obj)
    return obj


# ========================================================
# JSON Serialization with datetime support
# ========================================================

class DateTimeEncoder(json.JSONEncoder):
    """シンプルなdatetime対応エンコーダー"""
    
    def default(self, obj):
        # datetime処理
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # NumPy scalar処理
        if hasattr(obj, 'item'):
            return obj.item()
        
        # NumPy array処理
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        
        # Decimal処理
        if isinstance(obj, Decimal):
            return float(obj)
        
        # セット処理
        if isinstance(obj, set):
            return list(obj)
        
        # バイト処理
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        
        # その他のオブジェクトは文字列化
        try:
            return str(obj)
        except:
            return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全なJSON シリアライゼーション（NumPy対応版）
    
    Args:
        obj: JSON化するオブジェクト
        **kwargs: json.dumps に渡す追加パラメータ
        
    Returns:
        JSON文字列
    """
    # デフォルトでensure_ascii=Falseを設定（マルチバイト対応）
    if 'ensure_ascii' not in kwargs:
        kwargs['ensure_ascii'] = False
    
    # デフォルトでDateTimeEncoderを使用
    if 'cls' not in kwargs:
        kwargs['cls'] = DateTimeEncoder
    
    # 循環参照対策
    if 'check_circular' not in kwargs:
        kwargs['check_circular'] = True
    
    try:
        # NumPy型を事前に変換
        converted_obj = convert_numpy_types(obj)
        return json.dumps(converted_obj, **kwargs)
    except Exception as e:
        # フォールバック：基本的な型のみを含むデータに変換
        cleaned_obj = clean_for_json(obj)
        return json.dumps(cleaned_obj, cls=DateTimeEncoder, **kwargs)


def clean_for_json(obj: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
    """
    JSONシリアライズ可能な形式にクリーニング
    
    Args:
        obj: クリーニングするオブジェクト
        max_depth: 最大再帰深度
        current_depth: 現在の再帰深度
        
    Returns:
        クリーニングされたオブジェクト
    """
    if current_depth > max_depth:
        return None
    
    # 基本型はそのまま
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    
    # NumPy型の変換
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    if isinstance(obj, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    
    if isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    
    if isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    
    # datetime
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    # リスト・タプル
    if isinstance(obj, (list, tuple)):
        return [clean_for_json(item, max_depth, current_depth + 1) for item in obj]
    
    # 辞書
    if isinstance(obj, dict):
        return {
            str(k): clean_for_json(v, max_depth, current_depth + 1) 
            for k, v in obj.items()
        }
    
    # その他は文字列化
    try:
        return str(obj)
    except:
        return None


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
    ChromaDB用にメタデータを厳密にフィルタリング
    
    Args:
        metadata: 元のメタデータ
        
    Returns:
        フィルタリング済みメタデータ
    """
    filtered = {}
    
    for key, value in metadata.items():
        # キーを文字列に変換
        key = str(key)
        
        # None値は除外
        if value is None:
            continue
        
        # NumPy型を事前に変換
        value = convert_numpy_types(value)
        
        # 値の型を適切に変換
        filtered_value = safe_metadata_value(value)
        
        # 変換後もNoneでなければ追加
        if filtered_value is not None:
            filtered[key] = filtered_value
    
    return filtered


def safe_metadata_value(value: Any, default_value: Any = None) -> Any:
    """
    ChromaDB用の安全なメタデータ値変換（拡張版）
    
    Args:
        value: 変換する値
        default_value: Noneの場合のデフォルト値
        
    Returns:
        安全な値
    """
    if value is None:
        return default_value
    
    # ブール値
    if isinstance(value, bool):
        return bool(value)
    
    # 整数
    if isinstance(value, int):
        return int(value)
    
    # 浮動小数点数
    if isinstance(value, float):
        # NaN や Inf のチェック
        if np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)
    
    # 文字列
    if isinstance(value, str):
        # 空文字列を避ける
        return value if value else default_value
    
    # リストやタプル -> JSON文字列に変換
    if isinstance(value, (list, tuple)):
        try:
            return safe_json_dumps(value)
        except:
            return str(value)
    
    # 辞書 -> JSON文字列に変換
    if isinstance(value, dict):
        try:
            return safe_json_dumps(value)
        except:
            return str(value)
    
    # datetime -> ISO文字列
    if isinstance(value, datetime):
        return value.isoformat()
    
    # その他の型は文字列に変換
    try:
        return str(value)
    except:
        return default_value


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
