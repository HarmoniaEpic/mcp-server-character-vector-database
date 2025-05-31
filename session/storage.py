"""
Session storage handling
"""

import os
import stat
from pathlib import Path
from typing import Optional, Dict, Any

from config.logging import get_logger
from core.utils import safe_json_dumps, safe_json_loads
from core.exceptions import SessionError, PathTraversalError
from security.validators import validate_session_id, check_file_permissions

logger = get_logger(__name__)


class SessionStorage:
    """セッションデータのファイルストレージ管理"""
    
    def __init__(self, storage_dir: str):
        """
        初期化
        
        Args:
            storage_dir: セッションファイルの保存ディレクトリ
        """
        self.storage_dir = Path(storage_dir).resolve()
        self._create_secure_directory()
    
    def _create_secure_directory(self):
        """セキュアなディレクトリ作成"""
        try:
            self.storage_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            logger.info(f"Created secure session directory: {self.storage_dir}")
        except OSError as e:
            logger.error(f"Failed to create directory {self.storage_dir}: {e}")
            raise SessionError(f"Failed to create session directory: {e}")
    
    def _get_session_path(self, session_id: str) -> Path:
        """
        セッションファイルパスを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            セッションファイルのパス
            
        Raises:
            SessionError: 無効なセッションIDの場合
        """
        if not validate_session_id(session_id):
            raise SessionError(f"Invalid session ID: {session_id}")
        
        # ファイル名を安全に構築
        filename = f"{session_id}.json"
        file_path = self.storage_dir / filename
        
        # パストラバーサル攻撃の防止
        try:
            file_path.relative_to(self.storage_dir)
        except ValueError:
            raise PathTraversalError(f"Path traversal attack detected: {file_path}")
        
        return file_path
    
    def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        セッションデータを保存
        
        Args:
            session_id: セッションID
            data: 保存するデータ
            
        Returns:
            成功した場合True
        """
        try:
            file_path = self._get_session_path(session_id)
            
            # 一時ファイルに書き込み
            temp_path = file_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(safe_json_dumps(data, ensure_ascii=False, indent=2))
            
            # セキュアな権限設定
            os.chmod(temp_path, 0o600)  # 所有者のみ読み書き
            
            # 原子的リネーム
            temp_path.replace(file_path)
            
            logger.debug(f"Saved session data: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            # 一時ファイルのクリーンアップ
            try:
                temp_path = self._get_session_path(session_id).with_suffix('.tmp')
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
            return False
    
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションデータを読み込み
        
        Args:
            session_id: セッションID
            
        Returns:
            セッションデータまたはNone
        """
        try:
            file_path = self._get_session_path(session_id)
            
            if not file_path.exists():
                logger.debug(f"Session file not found: {session_id}")
                return None
            
            # ファイル権限チェック
            is_safe, error_msg = check_file_permissions(str(file_path))
            if not is_safe:
                logger.warning(f"Unsafe file permissions for {file_path}: {error_msg}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = safe_json_loads(f.read())
            
            logger.debug(f"Loaded session data: {session_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def delete(self, session_id: str) -> bool:
        """
        セッションデータを削除
        
        Args:
            session_id: セッションID
            
        Returns:
            成功した場合True
        """
        try:
            file_path = self._get_session_path(session_id)
            
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted session file: {session_id}")
                return True
            else:
                logger.debug(f"Session file not found for deletion: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def exists(self, session_id: str) -> bool:
        """
        セッションファイルが存在するかチェック
        
        Args:
            session_id: セッションID
            
        Returns:
            存在する場合True
        """
        try:
            file_path = self._get_session_path(session_id)
            return file_path.exists()
        except:
            return False
    
    def list_sessions(self) -> list[str]:
        """
        保存されているセッション一覧を取得
        
        Returns:
            セッションIDのリスト
        """
        sessions = []
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                if file_path.is_file():
                    session_id = file_path.stem
                    if validate_session_id(session_id):
                        sessions.append(session_id)
                    else:
                        logger.warning(f"Invalid session file found: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
        
        return sessions
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        古いセッションファイルをクリーンアップ
        
        Args:
            days: 保持する日数
            
        Returns:
            削除したファイル数
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                if file_path.is_file():
                    try:
                        # ファイルの更新時刻をチェック
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                            logger.info(f"Cleaned up old session: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old session files")
        return deleted_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        ストレージ統計情報を取得
        
        Returns:
            統計情報
        """
        try:
            total_size = 0
            file_count = 0
            oldest_mtime = None
            newest_mtime = None
            
            for file_path in self.storage_dir.glob("*.json"):
                if file_path.is_file():
                    stat = file_path.stat()
                    total_size += stat.st_size
                    file_count += 1
                    
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if oldest_mtime is None or mtime < oldest_mtime:
                        oldest_mtime = mtime
                    if newest_mtime is None or mtime > newest_mtime:
                        newest_mtime = mtime
            
            return {
                "storage_dir": str(self.storage_dir),
                "total_sessions": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_session": oldest_mtime.isoformat() if oldest_mtime else None,
                "newest_session": newest_mtime.isoformat() if newest_mtime else None
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "storage_dir": str(self.storage_dir),
                "error": str(e)
            }
