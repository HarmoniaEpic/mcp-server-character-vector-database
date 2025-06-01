"""
Secure enhanced pink noise generator
"""

from typing import List

from config.logging import get_logger
from .entropy import SecureEntropySource

logger = get_logger(__name__)


class SecureEnhancedPinkNoiseGenerator:
    """セキュアエントロピー強化版1/fノイズジェネレータ"""
    
    def __init__(self, entropy_source: SecureEntropySource, octaves: int = 5):
        """
        初期化
        
        Args:
            entropy_source: セキュアエントロピー源
            octaves: オクターブ数（周波数帯域の数）
        """
        self.entropy_source = entropy_source
        self.octaves = octaves
        self.max_key = (1 << octaves) - 1
        self.key = 0
        self.white_values = []
        self.pink_values = []
        
        # セキュアエントロピーで初期化
        for i in range(octaves):
            secure_entropy = self.entropy_source.get_normalized_entropy()
            self.white_values.append(secure_entropy * 2.0 - 1.0)  # -1 to 1 range
            self.pink_values.append(0.0)
    
    def generate_secure_pink_noise(self) -> float:
        """セキュアエントロピーベースの1/fノイズ生成"""
        # Voss-McCartney アルゴリズム + セキュアエントロピー
        last_key = self.key
        self.key += 1
        
        if self.key > self.max_key:
            self.key = 0
        
        # 変更されたビットを特定
        diff = last_key ^ self.key
        
        # セキュアエントロピーで各オクターブを更新
        for i in range(self.octaves):
            if (diff & (1 << i)) != 0:
                secure_entropy = self.entropy_source.get_normalized_entropy()
                self.white_values[i] = secure_entropy * 2.0 - 1.0
        
        # ピンクノイズの合成
        pink_value = sum(self.white_values) / self.octaves
        
        # セキュア振動成分の追加
        thermal_component = self.entropy_source.get_thermal_oscillation(0.1)
        
        # 1/f特性を強化
        enhanced_pink = pink_value * 0.8 + thermal_component * 0.2
        
        # スムージング
        if self.pink_values:
            last_value = self.pink_values[-1]
            smoothed = last_value * 0.7 + enhanced_pink * 0.3
            self.pink_values.append(smoothed)
            
            # バッファサイズ制限
            if len(self.pink_values) > 100:
                self.pink_values.pop(0)
            
            return smoothed
        else:
            self.pink_values.append(enhanced_pink)
            return enhanced_pink
    
    def reset(self):
        """ジェネレータのリセット"""
        self.key = 0
        self.white_values = []
        self.pink_values = []
        
        # セキュアエントロピーで再初期化
        for i in range(self.octaves):
            secure_entropy = self.entropy_source.get_normalized_entropy()
            self.white_values.append(secure_entropy * 2.0 - 1.0)
            self.pink_values.append(0.0)
    
    def get_history(self, length: int = 10) -> List[float]:
        """過去の値の取得"""
        if len(self.pink_values) >= length:
            return self.pink_values[-length:]
        else:
            return self.pink_values.copy()
    
    def get_spectral_characteristics(self) -> dict:
        """スペクトル特性の取得"""
        if not self.pink_values:
            return {
                "average": 0.0,
                "variance": 0.0,
                "history_length": 0
            }
        
        import numpy as np
        
        values = np.array(self.pink_values)
        return {
            "average": float(np.mean(values)),
            "variance": float(np.var(values)),
            "std_deviation": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "history_length": len(self.pink_values),
            "octaves": self.octaves
        }
