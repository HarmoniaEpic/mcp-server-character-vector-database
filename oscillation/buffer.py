"""
Oscillation buffer management
"""

from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from config.settings import OSCILLATION_BUFFER_SIZE
from config.logging import get_logger

logger = get_logger(__name__)


class OscillationBuffer:
    """振動バッファ管理クラス"""
    
    def __init__(self, max_size: int = OSCILLATION_BUFFER_SIZE):
        """
        初期化
        
        Args:
            max_size: バッファの最大サイズ
        """
        self.max_size = max_size
        self.values = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self._stats_cache = None
        self._cache_timestamp = None
    
    def add(self, value: float, timestamp: Optional[datetime] = None):
        """
        値を追加
        
        Args:
            value: 振動値
            timestamp: タイムスタンプ（省略時は現在時刻）
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 確実にfloat型に変換
        self.values.append(float(value))
        self.timestamps.append(timestamp)
        
        # キャッシュを無効化
        self._invalidate_cache()
    
    def add_multiple(self, values: List[float], timestamps: Optional[List[datetime]] = None):
        """
        複数の値を一度に追加
        
        Args:
            values: 振動値のリスト
            timestamps: タイムスタンプのリスト
        """
        if timestamps is None:
            current_time = datetime.now()
            timestamps = [current_time] * len(values)
        elif len(timestamps) != len(values):
            raise ValueError("Values and timestamps must have the same length")
        
        for value, timestamp in zip(values, timestamps):
            # 確実にfloat型に変換
            self.values.append(float(value))
            self.timestamps.append(timestamp)
        
        # キャッシュを無効化
        self._invalidate_cache()
    
    def get_values(self) -> List[float]:
        """すべての値を取得"""
        # float型のリストとして返す
        return [float(v) for v in self.values]
    
    def get_timestamps(self) -> List[datetime]:
        """すべてのタイムスタンプを取得"""
        return list(self.timestamps)
    
    def get_recent(self, count: int) -> List[float]:
        """
        最近の値を取得
        
        Args:
            count: 取得する値の数
            
        Returns:
            最近の値のリスト
        """
        if count >= len(self.values):
            return self.get_values()
        # float型のリストとして返す
        return [float(v) for v in list(self.values)[-count:]]
    
    def get_recent_with_timestamps(self, count: int) -> List[Tuple[datetime, float]]:
        """
        最近の値をタイムスタンプ付きで取得
        
        Args:
            count: 取得する値の数
            
        Returns:
            (タイムスタンプ, 値)のタプルのリスト
        """
        recent_values = self.get_recent(count)
        recent_timestamps = list(self.timestamps)[-count:] if count < len(self.timestamps) else list(self.timestamps)
        return list(zip(recent_timestamps, recent_values))
    
    def size(self) -> int:
        """現在のバッファサイズ"""
        return len(self.values)
    
    def is_empty(self) -> bool:
        """バッファが空かチェック"""
        return len(self.values) == 0
    
    def is_full(self) -> bool:
        """バッファが満杯かチェック"""
        return len(self.values) >= self.max_size
    
    def clear(self):
        """バッファをクリア"""
        self.values.clear()
        self.timestamps.clear()
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """統計キャッシュを無効化"""
        self._stats_cache = None
        self._cache_timestamp = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        バッファの統計情報を取得（キャッシュ付き）
        
        Returns:
            統計情報
        """
        # キャッシュが有効な場合は返す
        if self._stats_cache and self._cache_timestamp:
            cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
            if cache_age < 1.0:  # 1秒間キャッシュ
                return self._stats_cache
        
        if self.is_empty():
            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "range": 0.0,
                "variance": 0.0
            }
        
        import numpy as np
        values_array = np.array(self.values)
        
        # NumPy型を明示的にPython標準型に変換
        stats = {
            "count": int(len(values_array)),
            "mean": float(np.mean(values_array)),
            "std": float(np.std(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "range": float(np.max(values_array) - np.min(values_array)),
            "variance": float(np.var(values_array))
        }
        
        # キャッシュに保存
        self._stats_cache = stats
        self._cache_timestamp = datetime.now()
        
        return stats
    
    def get_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        """
        タイムスタンプの範囲を取得
        
        Returns:
            (最古のタイムスタンプ, 最新のタイムスタンプ)またはNone
        """
        if self.is_empty():
            return None
        
        return (self.timestamps[0], self.timestamps[-1])
    
    def get_duration(self) -> float:
        """
        データの時間幅を秒単位で取得
        
        Returns:
            時間幅（秒）
        """
        time_range = self.get_time_range()
        if time_range:
            return float((time_range[1] - time_range[0]).total_seconds())
        return 0.0
    
    def resample(self, target_size: int) -> List[float]:
        """
        データをリサンプリング
        
        Args:
            target_size: 目標サイズ
            
        Returns:
            リサンプリングされた値のリスト
        """
        if self.is_empty():
            return []
        
        current_size = self.size()
        if current_size == target_size:
            return self.get_values()
        
        import numpy as np
        indices = np.linspace(0, current_size - 1, target_size)
        values_array = np.array(self.values)
        
        # 線形補間
        resampled = np.interp(indices, range(current_size), values_array)
        # NumPy配列をfloatのリストに変換
        return [float(v) for v in resampled]
    
    def get_derivative(self) -> List[float]:
        """
        微分値（変化率）を計算
        
        Returns:
            微分値のリスト
        """
        if self.size() < 2:
            return []
        
        derivatives = []
        for i in range(1, len(self.values)):
            time_delta = (self.timestamps[i] - self.timestamps[i-1]).total_seconds()
            if time_delta > 0:
                # 微分値をfloatとして計算
                derivative = float((float(self.values[i]) - float(self.values[i-1])) / time_delta)
            else:
                derivative = 0.0
            derivatives.append(derivative)
        
        return derivatives
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "values": self.get_values(),  # float型のリストとして返す
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "max_size": self.max_size,
            "statistics": self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OscillationBuffer':
        """辞書から復元"""
        buffer = cls(max_size=data.get("max_size", OSCILLATION_BUFFER_SIZE))
        
        values = data.get("values", [])
        timestamps = data.get("timestamps", [])
        
        # タイムスタンプを datetime に変換
        datetime_timestamps = []
        for ts in timestamps:
            if isinstance(ts, str):
                datetime_timestamps.append(datetime.fromisoformat(ts))
            else:
                datetime_timestamps.append(ts)
        
        # 値をfloat型に変換して追加
        float_values = [float(v) for v in values]
        buffer.add_multiple(float_values, datetime_timestamps)
        return buffer
