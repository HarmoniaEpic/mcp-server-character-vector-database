"""
Security validators and verification functions
"""

import os
import re
import stat
import uuid
from pathlib import Path
from typing import Optional, Tuple

from config.logging import get_logger
from core.exceptions import ValidationError, PathTraversalError

logger = get_logger(__name__)


def validate_path(path: str, base_dir: str) -> str:
    """
    パスの安全性を検証（パストラバーサル攻撃防止）
    
    Args:
        path: 検証するパス
        base_dir: 基準ディレクトリ
        
    Returns:
        正規化された安全なパス
        
    Raises:
        PathTraversalError: パストラバーサル攻撃が検出された場合
    """
    # 絶対パスに変換
    base_path = Path(base_dir).resolve()
    target_path = (base_path / path).resolve()
    
    # パストラバーサル攻撃の検出
    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise PathTraversalError(f"Path traversal attack detected: {path}")
    
    return str(target_path)


def validate_session_id(session_id: str) -> bool:
    """
    セッションIDの厳格な検証
    
    Args:
        session_id: 検証するセッションID
        
    Returns:
        有効な場合True
    """
    try:
        # UUIDフォーマットのみ許可
        uuid.UUID(session_id)
        
        # 追加の安全チェック
        if not session_id.replace('-', '').isalnum():
            return False
        
        if len(session_id) != 36:  # UUID標準長
            return False
            
        if '..' in session_id or '/' in session_id or '\\' in session_id:
            return False
            
        return True
    except (ValueError, TypeError):
        return False


def validate_uuid(value: str) -> bool:
    """
    UUID形式の検証
    
    Args:
        value: 検証する値
        
    Returns:
        有効なUUIDの場合True
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def check_file_permissions(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    ファイルのパーミッションをチェック
    
    Args:
        file_path: チェックするファイルパス
        
    Returns:
        (安全かどうか, エラーメッセージ)
    """
    try:
        file_stat = os.stat(file_path)
        mode = file_stat.st_mode
        
        # グループとその他の読み取り権限をチェック
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            return False, "File is readable by group or others"
        
        # グループとその他の書き込み権限をチェック
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            return False, "File is writable by group or others"
        
        return True, None
        
    except OSError as e:
        return False, f"Failed to check file permissions: {e}"


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズ
    
    Args:
        filename: サニタイズするファイル名
        
    Returns:
        安全なファイル名
    """
    # 危険な文字を除去
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # 連続するピリオドを単一に
    safe_name = re.sub(r'\.+', '.', safe_name)
    
    # 先頭と末尾のピリオドを除去
    safe_name = safe_name.strip('.')
    
    # 空文字列の場合はデフォルト名
    if not safe_name:
        safe_name = "unnamed"
    
    # 長さ制限
    max_length = 255
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:max_length - len(ext)] + ext
    
    return safe_name


def validate_json_structure(data: dict, required_fields: list) -> Tuple[bool, Optional[str]]:
    """
    JSONデータ構造の検証
    
    Args:
        data: 検証するデータ
        required_fields: 必須フィールドのリスト
        
    Returns:
        (有効かどうか, エラーメッセージ)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None


def validate_data_type(value: any, expected_type: type, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    データ型の検証
    
    Args:
        value: 検証する値
        expected_type: 期待される型
        field_name: フィールド名（エラーメッセージ用）
        
    Returns:
        (有効かどうか, エラーメッセージ)
    """
    if not isinstance(value, expected_type):
        return False, f"{field_name} must be of type {expected_type.__name__}, got {type(value).__name__}"
    
    return True, None


def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    数値範囲の検証
    
    Args:
        value: 検証する値
        min_val: 最小値
        max_val: 最大値
        field_name: フィールド名（エラーメッセージ用）
        
    Returns:
        (有効かどうか, エラーメッセージ)
    """
    if not isinstance(value, (int, float)):
        return False, f"{field_name} must be a number"
    
    if value < min_val or value > max_val:
        return False, f"{field_name} must be between {min_val} and {max_val}, got {value}"
    
    return True, None


def validate_enum_value(value: str, allowed_values: list, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    列挙値の検証
    
    Args:
        value: 検証する値
        allowed_values: 許可される値のリスト
        field_name: フィールド名（エラーメッセージ用）
        
    Returns:
        (有効かどうか, エラーメッセージ)
    """
    if value not in allowed_values:
        return False, f"{field_name} must be one of {allowed_values}, got '{value}'"
    
    return True, None


def is_safe_directory_path(path: str) -> bool:
    """
    ディレクトリパスの安全性チェック
    
    Args:
        path: チェックするパス
        
    Returns:
        安全な場合True
    """
    # 危険なパターンのチェック
    dangerous_patterns = [
        '..',  # 親ディレクトリ参照
        '~',   # ホームディレクトリ展開
        '$',   # 環境変数展開
        '|',   # パイプ
        ';',   # コマンド区切り
        '&',   # バックグラウンド実行
        '<', '>', # リダイレクト
        '`',   # コマンド置換
        '\0',  # NULL文字
    ]
    
    for pattern in dangerous_patterns:
        if pattern in path:
            return False
    
    # 絶対パスを許可しない（オプション）
    if os.path.isabs(path):
        return False
    
    return True
