"""
Secure entropy generation module
"""

import hashlib
import os
import platform
import secrets
import time
from typing import Dict, Any

from config.logging import get_logger

logger = get_logger(__name__)


class SecureEntropySource:
    """セキュアエントロピー取得クラス（secrets模듈ベース）"""
    
    def __init__(self):
        """初期化とシステム情報検出"""
        self.arch = platform.machine().lower()
        self.system = platform.system().lower()
        self.has_rdrand = False
        self.has_rdseed = False
        self.entropy_source = "secure_combined"  # セキュアな複合エントロピー
        self.entropy_buffer = []
        self.buffer_size = 1000
        self.quality_metrics = {
            "total_entropy_bits": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "entropy_rate": 0.0
        }
        
        logger.info(f"Initializing SecureEntropySource on {self.system} {self.arch}")
        
        # セキュアなCPU機能検出（読み取り専用）
        self._detect_cpu_features_safe()
        self._prefill_buffer()
    
    def _detect_cpu_features_safe(self):
        """セキュアなCPU機能検出（subprocess不使用）"""
        try:
            # Linux/FreeBSD: /proc/cpuinfo読み取り
            if self.system in ['linux', 'freebsd'] and os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    self.has_rdrand = 'rdrand' in cpuinfo
                    self.has_rdseed = 'rdseed' in cpuinfo
                    
                    if self.has_rdseed:
                        logger.info("CPU features: RDSEED detected (using secure fallback)")
                    elif self.has_rdrand:
                        logger.info("CPU features: RDRAND detected (using secure fallback)")
                    
            # Windows: 保守的な検出（subprocess不使用）
            elif self.system == 'windows':
                # レジストリやWMI経由の安全な検出も可能だが、
                # セキュリティを優先してFalseに設定
                self.has_rdrand = False
                self.has_rdseed = False
                logger.info("Windows: Using secure entropy fallback")
            
            # その他のOS
            else:
                self.has_rdrand = False
                self.has_rdseed = False
                logger.info("Unknown OS: Using secure entropy fallback")
                
        except Exception as e:
            logger.warning(f"CPU feature detection failed: {e}. Using secure fallback.")
            self.has_rdrand = False
            self.has_rdseed = False
        
        # 実際にはハードウェア命令は使用せず、検出情報のみ記録
        logger.info(f"CPU features detected (informational only): RDRAND={self.has_rdrand}, RDSEED={self.has_rdseed}")
    
    def get_secure_entropy(self, bytes_count: int = 8) -> int:
        """セキュアエントロピー取得のメイン関数"""
        try:
            # 複数のエントロピー源を組み合わせた高品質エントロピー
            return self._get_combined_secure_entropy(bytes_count)
        except Exception as e:
            logger.warning(f"Secure entropy generation failed: {e}. Using emergency fallback.")
            self.quality_metrics["failed_calls"] += 1
            return self._get_emergency_entropy(bytes_count)
    
    def _get_combined_secure_entropy(self, bytes_count: int) -> int:
        """複数エントロピー源の組み合わせによる高品質エントロピー"""
        # ビット数を計算
        bit_count = bytes_count * 8
        bit_mask = (1 << bit_count) - 1
        
        # 1. secrets モジュール（暗号学的に安全）
        entropy1 = secrets.randbits(bit_count)
        
        # 2. os.urandom（OS提供のエントロピー）
        entropy_bytes = os.urandom(bytes_count)
        entropy2 = int.from_bytes(entropy_bytes, byteorder='little')
        
        # 3. 高解像度時間ベース（マイクロ秒 + ナノ秒）
        time_ns = time.time_ns()
        entropy3 = hash(time_ns) & bit_mask
        
        # 4. メモリアドレスベース
        dummy_object = object()
        memory_entropy = hash(id(dummy_object)) & bit_mask
        
        # 5. プロセス固有情報
        process_entropy = hash(os.getpid() + time.process_time_ns()) & bit_mask
        
        # XORとrotationで組み合わせ（適切なビット幅で）
        combined = entropy1 ^ entropy2
        combined ^= self._rotate_left(entropy3, 8, bit_count)
        combined ^= self._rotate_left(memory_entropy, 16, bit_count) 
        combined ^= self._rotate_left(process_entropy, 24, bit_count)
        
        # 最終的にビットマスクを適用して範囲内に収める
        combined &= bit_mask
        
        # 追加のハッシュ混合
        # to_bytesの前にサイズチェック
        if combined >= (1 << bit_count):
            combined &= bit_mask
        
        try:
            combined_bytes = combined.to_bytes(bytes_count, byteorder='little', signed=False)
        except OverflowError:
            # フォールバック：combinedをハッシュ化してからバイト列に変換
            combined_hash = hashlib.sha256(str(combined).encode()).digest()
            combined_bytes = combined_hash[:bytes_count]
        
        final_hash = hashlib.blake2b(combined_bytes, digest_size=bytes_count).digest()
        final_entropy = int.from_bytes(final_hash, byteorder='little')
        
        self.quality_metrics["successful_calls"] += 1
        self.quality_metrics["total_entropy_bits"] += bit_count
        
        return final_entropy
    
    def _rotate_left(self, value: int, shift: int, width: int = 64) -> int:
        """左回転によるビット混合"""
        # widthビットにマスク
        value &= ((1 << width) - 1)
        shift = shift % width
        return ((value << shift) | (value >> (width - shift))) & ((1 << width) - 1)
    
    def _get_emergency_entropy(self, bytes_count: int) -> int:
        """緊急時のフォールバックエントロピー"""
        try:
            # secrets が利用できない場合の最終フォールバック
            entropy_bytes = os.urandom(bytes_count)
            return int.from_bytes(entropy_bytes, byteorder='little')
        except Exception as e:
            # 最後の手段：時間ベース
            logger.error(f"All entropy sources failed: {e}. Using time-based fallback.")
            time_based = int(time.time_ns()) ^ hash(os.getpid())
            return time_based & ((1 << (bytes_count * 8)) - 1)
    
    def _prefill_buffer(self):
        """エントロピーバッファの事前充填"""
        logger.info("Prefilling secure entropy buffer...")
        for _ in range(self.buffer_size):
            try:
                entropy = self.get_secure_entropy(4)  # 32bit
                normalized = (entropy % 1000000) / 1000000.0  # 0.0-1.0 正規化
                self.entropy_buffer.append(normalized)
            except Exception as e:
                logger.warning(f"Buffer prefill failed: {e}")
                # フォールバック
                fallback_entropy = hash(time.time_ns() + os.getpid()) & 0xFFFFFFFF
                normalized = (fallback_entropy % 1000000) / 1000000.0
                self.entropy_buffer.append(normalized)
    
    def get_normalized_entropy(self) -> float:
        """正規化されたエントロピー値を取得（0.0-1.0）"""
        if len(self.entropy_buffer) < 10:
            self._prefill_buffer()
        
        if self.entropy_buffer:
            return self.entropy_buffer.pop()
        else:
            # 緊急フォールバック
            entropy = self.get_secure_entropy(4)
            return (entropy % 1000000) / 1000000.0
    
    def get_pink_noise_component(self, history_length: int = 5) -> float:
        """1/fゆらぎ近似コンポーネントの生成"""
        components = []
        weights = []
        
        # 複数のエントロピー値を異なる重みで組み合わせ
        for i in range(history_length):
            component = self.get_normalized_entropy()
            weight = 1.0 / (i + 1)  # 1/f 特性近似
            components.append(component)
            weights.append(weight)
        
        # 重み付き平均
        if weights:
            weighted_sum = sum(c * w for c, w in zip(components, weights))
            weight_sum = sum(weights)
            result = weighted_sum / weight_sum - 0.5  # -0.5 to 0.5 range
            return result * 0.2  # 振幅調整
        
        return 0.0
    
    def get_thermal_oscillation(self, base_amplitude: float = 0.1) -> float:
        """セキュア乱数ベースの振動成分"""
        # 複数のエントロピー値を組み合わせて自然な振動を生成
        e1 = self.get_normalized_entropy()
        e2 = self.get_normalized_entropy()
        e3 = self.get_normalized_entropy()
        
        # 3つの値で複合振動を生成
        oscillation = (e1 * 0.5 + e2 * 0.3 + e3 * 0.2) - 0.5
        
        return oscillation * base_amplitude
    
    def assess_entropy_quality(self) -> Dict[str, Any]:
        """エントロピー品質の評価"""
        if self.quality_metrics["successful_calls"] + self.quality_metrics["failed_calls"] > 0:
            success_rate = self.quality_metrics["successful_calls"] / (
                self.quality_metrics["successful_calls"] + self.quality_metrics["failed_calls"]
            )
        else:
            success_rate = 0.0
        
        return {
            "entropy_source": self.entropy_source,
            "success_rate": success_rate,
            "has_rdrand": self.has_rdrand,  # 情報として残すが使用しない
            "has_rdseed": self.has_rdseed,  # 情報として残すが使用しない
            "architecture": self.arch,
            "system": self.system,
            "secure_mode": True,
            "buffer_size": len(self.entropy_buffer),
            "total_entropy_bits": self.quality_metrics["total_entropy_bits"],
            "entropy_sources": ["secrets", "os_urandom", "time_ns", "memory_hash", "process_hash"]
        }
