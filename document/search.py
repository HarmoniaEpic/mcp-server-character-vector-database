"""
Document search functionality
"""

import re
from typing import List, Dict, Any, Optional, Tuple

from config.logging import get_logger

logger = get_logger(__name__)


class DocumentSearcher:
    """ドキュメント検索機能"""
    
    def __init__(self):
        """初期化"""
        self.search_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def search_in_document(self, content: str, query: str, 
                          max_results: int = 10,
                          case_sensitive: bool = False,
                          whole_word: bool = False) -> List[Dict[str, Any]]:
        """
        ドキュメント内でキーワード検索
        
        Args:
            content: 検索対象のコンテンツ
            query: 検索クエリ
            max_results: 最大結果数
            case_sensitive: 大文字小文字を区別するか
            whole_word: 単語全体を検索するか
            
        Returns:
            検索結果のリスト
        """
        # キャッシュキーを生成
        cache_key = f"{hash(content)}:{query}:{case_sensitive}:{whole_word}"
        if cache_key in self.search_cache:
            logger.debug(f"Using cached search results for: {query}")
            return self.search_cache[cache_key][:max_results]
        
        lines = content.split('\n')
        matches = []
        
        # 検索パターンを構築
        if whole_word:
            pattern = r'\b' + re.escape(query) + r'\b'
        else:
            pattern = re.escape(query)
        
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        for i, line in enumerate(lines):
            if regex.search(line):
                # 前後の文脈も含めて表示
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                
                context_lines = []
                for j in range(context_start, context_end):
                    prefix = ">>> " if j == i else "    "
                    context_lines.append(f"{prefix}{lines[j]}")
                
                # マッチ位置を特定
                match_positions = []
                for match in regex.finditer(line):
                    match_positions.append({
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group()
                    })
                
                match_info = {
                    "line_number": i + 1,
                    "matched_line": line.strip(),
                    "context": "\n".join(context_lines),
                    "match_positions": match_positions,
                    "score": len(match_positions)  # シンプルなスコアリング
                }
                
                matches.append(match_info)
                
                if len(matches) >= max_results * 2:  # キャッシュ用に多めに取得
                    break
        
        # スコアでソート（マッチ数が多い順）
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        # キャッシュに保存
        self.search_cache[cache_key] = matches
        
        logger.debug(f"Search for '{query}' found {len(matches)} matches")
        return matches[:max_results]
    
    def extract_section(self, content: str, section_name: str) -> str:
        """
        ドキュメントから特定のセクションを抽出
        
        Args:
            content: ドキュメントコンテンツ
            section_name: セクション名
            
        Returns:
            抽出されたセクション
        """
        lines = content.split('\n')
        in_section = False
        section_content = []
        section_level = 0
        
        # セクション名のパターンマッチング
        section_patterns = [
            rf'^# {re.escape(section_name)}$',
            rf'^## {re.escape(section_name)}$',
            rf'^### {re.escape(section_name)}$',
            rf'^#### {re.escape(section_name)}$',
            rf'^// {re.escape(section_name)}$',
            rf'^{re.escape(section_name)}$'
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # セクション開始の検出
            if not in_section:
                for i, pattern in enumerate(section_patterns):
                    if re.match(pattern, line_stripped, re.IGNORECASE):
                        in_section = True
                        section_level = i + 1
                        section_content.append(line)
                        break
                continue
            
            # セクション終了の検出
            if in_section:
                # 同レベル以上の見出しで終了
                if section_level <= 4:  # マークダウン見出し
                    header_match = re.match(r'^(#{1,4})\s', line_stripped)
                    if header_match:
                        current_level = len(header_match.group(1))
                        if current_level <= section_level:
                            break
                elif section_level == 5:  # // コメント形式
                    if line_stripped.startswith('//') and line_stripped != f"// {section_name}":
                        break
                
                section_content.append(line)
        
        result = '\n'.join(section_content)
        logger.debug(f"Extracted section '{section_name}': {len(result)} characters")
        return result
    
    def find_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        ドキュメント内のすべての見出しを検索
        
        Args:
            content: ドキュメントコンテンツ
            
        Returns:
            見出しのリスト
        """
        lines = content.split('\n')
        headers = []
        
        # マークダウン見出しパターン
        markdown_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        
        # コメント見出しパターン
        comment_pattern = re.compile(r'^//\s+(.+)$')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # マークダウン見出し
            match = markdown_pattern.match(line_stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headers.append({
                    "line_number": i + 1,
                    "level": level,
                    "title": title,
                    "type": "markdown",
                    "raw": line
                })
                continue
            
            # コメント見出し
            match = comment_pattern.match(line_stripped)
            if match:
                title = match.group(1).strip()
                # 大文字で始まる場合のみ見出しとして扱う
                if title and title[0].isupper():
                    headers.append({
                        "line_number": i + 1,
                        "level": 7,  # コメント見出しは特別なレベル
                        "title": title,
                        "type": "comment",
                        "raw": line
                    })
        
        return headers
    
    def get_table_of_contents(self, content: str) -> str:
        """
        ドキュメントの目次を生成
        
        Args:
            content: ドキュメントコンテンツ
            
        Returns:
            目次の文字列
        """
        headers = self.find_headers(content)
        toc_lines = ["# Table of Contents\n"]
        
        for header in headers:
            if header["type"] == "markdown":
                # インデントを計算
                indent = "  " * (header["level"] - 1)
                toc_lines.append(f"{indent}- {header['title']}")
        
        return "\n".join(toc_lines)
    
    def search_multiple_documents(self, documents: Dict[str, str], 
                                query: str,
                                max_results_per_doc: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数のドキュメントを検索
        
        Args:
            documents: ドキュメント名とコンテンツの辞書
            query: 検索クエリ
            max_results_per_doc: ドキュメントごとの最大結果数
            
        Returns:
            ドキュメントごとの検索結果
        """
        results = {}
        
        for doc_name, content in documents.items():
            matches = self.search_in_document(content, query, max_results_per_doc)
            if matches:
                results[doc_name] = matches
        
        return results
    
    def highlight_matches(self, text: str, query: str, 
                         highlight_start: str = "**",
                         highlight_end: str = "**") -> str:
        """
        テキスト内のマッチ箇所をハイライト
        
        Args:
            text: テキスト
            query: 検索クエリ
            highlight_start: ハイライト開始マーカー
            highlight_end: ハイライト終了マーカー
            
        Returns:
            ハイライトされたテキスト
        """
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        def replace_func(match):
            return f"{highlight_start}{match.group()}{highlight_end}"
        
        return pattern.sub(replace_func, text)
    
    def get_word_frequency(self, content: str, 
                          min_length: int = 3,
                          top_n: int = 20) -> List[Tuple[str, int]]:
        """
        単語頻度を取得
        
        Args:
            content: ドキュメントコンテンツ
            min_length: 最小単語長
            top_n: 上位N件
            
        Returns:
            (単語, 頻度)のタプルのリスト
        """
        # 単語を抽出
        words = re.findall(r'\b\w+\b', content.lower())
        
        # 頻度をカウント
        word_count = {}
        for word in words:
            if len(word) >= min_length:
                word_count[word] = word_count.get(word, 0) + 1
        
        # 頻度順にソート
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_words[:top_n]
    
    def clear_cache(self):
        """検索キャッシュをクリア"""
        self.search_cache.clear()
        logger.debug("Search cache cleared")
