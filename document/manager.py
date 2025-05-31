"""
Document management module
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config.settings import DOCS_DIR, AVAILABLE_DOCUMENTS, MAX_FILE_SIZE
from config.logging import get_logger
from core.exceptions import DocumentError, DocumentNotFoundError, DocumentAccessError
from security.validators import validate_path
from .search import DocumentSearcher

logger = get_logger(__name__)


class DocumentManager:
    """ドキュメント読み込み管理クラス（セキュリティ強化版）"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """初期化"""
        if base_dir is None:
            self.docs_dir = DOCS_DIR
        else:
            self.docs_dir = Path(base_dir).resolve()
        
        # 利用可能ドキュメントの定義（ホワイトリスト方式）
        self.available_docs = AVAILABLE_DOCUMENTS.copy()
        
        # ドキュメント情報のキャッシュ
        self.doc_cache: Dict[str, Dict[str, Any]] = {}
        self.doc_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 検索機能
        self.searcher = DocumentSearcher()
        
        logger.info(f"DocumentManager initialized with base directory: {self.docs_dir}")
        self._scan_documents()
    
    def _scan_documents(self):
        """利用可能ドキュメントをスキャン"""
        for doc_key, filename in self.available_docs.items():
            doc_path = self.docs_dir / filename
            
            if doc_path.exists() and doc_path.is_file():
                try:
                    stat_info = doc_path.stat()
                    self.doc_metadata[doc_key] = {
                        "filename": filename,
                        "path": str(doc_path),
                        "size": stat_info.st_size,
                        "modified": datetime.fromtimestamp(stat_info.st_mtime),
                        "accessible": True
                    }
                    logger.info(f"Document found: {doc_key} -> {filename}")
                except Exception as e:
                    logger.warning(f"Error accessing document {filename}: {e}")
                    self.doc_metadata[doc_key] = {
                        "filename": filename,
                        "path": str(doc_path),
                        "accessible": False,
                        "error": str(e)
                    }
            else:
                logger.warning(f"Document not found: {filename}")
                self.doc_metadata[doc_key] = {
                    "filename": filename,
                    "path": str(doc_path),
                    "accessible": False,
                    "error": "File not found"
                }
    
    def _validate_document_access(self, doc_key: str) -> bool:
        """
        ドキュメントアクセスの安全な検証
        
        Args:
            doc_key: ドキュメントキー
            
        Returns:
            アクセス可能な場合True
        """
        if doc_key not in self.available_docs:
            return False
        
        doc_path = self.docs_dir / self.available_docs[doc_key]
        
        # パストラバーサル攻撃防止
        try:
            resolved_path = doc_path.resolve()
            resolved_docs_dir = self.docs_dir.resolve()
            
            # パスが許可されたディレクトリ内にあることを確認
            if not str(resolved_path).startswith(str(resolved_docs_dir)):
                logger.error(f"Path traversal attack detected: {resolved_path}")
                return False
            
            return resolved_path.exists() and resolved_path.is_file()
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    def read_document(self, doc_key: str) -> str:
        """
        安全なドキュメント読み込み
        
        Args:
            doc_key: ドキュメントキー
            
        Returns:
            ドキュメントコンテンツ
            
        Raises:
            DocumentNotFoundError: ドキュメントが見つからない場合
            DocumentAccessError: アクセスエラーの場合
            DocumentError: その他のエラー
        """
        if not self._validate_document_access(doc_key):
            raise DocumentNotFoundError(f"Document not accessible: {doc_key}")
        
        # キャッシュチェック
        if doc_key in self.doc_cache:
            cache_entry = self.doc_cache[doc_key]
            doc_path = self.docs_dir / self.available_docs[doc_key]
            
            try:
                current_mtime = doc_path.stat().st_mtime
                if cache_entry["mtime"] == current_mtime:
                    logger.debug(f"Returning cached content for: {doc_key}")
                    return cache_entry["content"]
            except Exception:
                # キャッシュ無効化
                del self.doc_cache[doc_key]
        
        # ファイル読み込み
        doc_path = self.docs_dir / self.available_docs[doc_key]
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ファイルサイズ制限（10MB）
            if len(content) > MAX_FILE_SIZE:
                raise DocumentError(f"Document too large: {len(content)} bytes")
            
            # キャッシュに保存
            self.doc_cache[doc_key] = {
                "content": content,
                "mtime": doc_path.stat().st_mtime
            }
            
            logger.info(f"Document loaded: {doc_key} ({len(content)} characters)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to read document {doc_key}: {e}")
            raise DocumentAccessError(f"Failed to read document: {e}")
    
    def extract_section(self, content: str, section_name: str) -> str:
        """
        ドキュメントから特定のセクションを抽出
        
        Args:
            content: ドキュメントコンテンツ
            section_name: セクション名
            
        Returns:
            抽出されたセクション
        """
        return self.searcher.extract_section(content, section_name)
    
    def search_in_document(self, content: str, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        ドキュメント内でキーワード検索
        
        Args:
            content: ドキュメントコンテンツ
            query: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        return self.searcher.search_in_document(content, query, max_results)
    
    def search_all_documents(self, query: str, max_results_per_doc: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        すべてのドキュメントを検索
        
        Args:
            query: 検索クエリ
            max_results_per_doc: ドキュメントごとの最大結果数
            
        Returns:
            ドキュメントごとの検索結果
        """
        documents = {}
        
        for doc_key in self.available_docs:
            try:
                content = self.read_document(doc_key)
                documents[doc_key] = content
            except Exception as e:
                logger.warning(f"Failed to read document {doc_key} for search: {e}")
        
        return self.searcher.search_multiple_documents(documents, query, max_results_per_doc)
    
    def get_document_info(self, doc_key: Optional[str] = None) -> Dict[str, Any]:
        """
        ドキュメント情報を取得
        
        Args:
            doc_key: ドキュメントキー（Noneの場合は全体情報）
            
        Returns:
            ドキュメント情報
        """
        if doc_key is None:
            return {
                "available_documents": self.doc_metadata,
                "docs_directory": str(self.docs_dir),
                "cache_status": {
                    "cached_documents": list(self.doc_cache.keys()),
                    "cache_size": len(self.doc_cache)
                }
            }
        
        if doc_key not in self.available_docs:
            return {"error": f"Unknown document key: {doc_key}"}
        
        return self.doc_metadata.get(doc_key, {"error": "Document metadata not available"})
    
    def get_document_headers(self, doc_key: str) -> List[Dict[str, Any]]:
        """
        ドキュメントの見出し一覧を取得
        
        Args:
            doc_key: ドキュメントキー
            
        Returns:
            見出しのリスト
        """
        content = self.read_document(doc_key)
        return self.searcher.find_headers(content)
    
    def get_table_of_contents(self, doc_key: str) -> str:
        """
        ドキュメントの目次を生成
        
        Args:
            doc_key: ドキュメントキー
            
        Returns:
            目次
        """
        content = self.read_document(doc_key)
        return self.searcher.get_table_of_contents(content)
    
    def add_document(self, doc_key: str, filename: str) -> bool:
        """
        新しいドキュメントを登録（ホワイトリストに追加）
        
        Args:
            doc_key: ドキュメントキー
            filename: ファイル名
            
        Returns:
            成功した場合True
        """
        # セキュリティチェック
        if not filename.replace('-', '').replace('_', '').replace('.', '').isalnum():
            logger.error(f"Invalid filename: {filename}")
            return False
        
        # ドキュメントを追加
        self.available_docs[doc_key] = filename
        
        # 再スキャン
        self._scan_documents()
        
        return doc_key in self.doc_metadata and self.doc_metadata[doc_key].get("accessible", False)
    
    def remove_document(self, doc_key: str) -> bool:
        """
        ドキュメントを登録から削除
        
        Args:
            doc_key: ドキュメントキー
            
        Returns:
            成功した場合True
        """
        if doc_key not in self.available_docs:
            return False
        
        # 登録から削除
        del self.available_docs[doc_key]
        
        # キャッシュから削除
        if doc_key in self.doc_cache:
            del self.doc_cache[doc_key]
        
        if doc_key in self.doc_metadata:
            del self.doc_metadata[doc_key]
        
        return True
    
    def clear_cache(self):
        """ドキュメントキャッシュをクリア"""
        self.doc_cache.clear()
        self.searcher.clear_cache()
        logger.info("Document cache cleared")
    
    def refresh(self):
        """ドキュメント情報をリフレッシュ"""
        self.clear_cache()
        self._scan_documents()
        logger.info("Document manager refreshed")
