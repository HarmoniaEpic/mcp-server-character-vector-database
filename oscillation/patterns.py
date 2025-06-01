"""
Oscillation pattern data structures
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class OscillationPatternData:
    """振動パターンデータ（セキュアエントロピー統合版）"""
    amplitude: float
    frequency: float
    phase: float
    pink_noise_enabled: bool
    pink_noise_intensity: float
    spectral_slope: float
    damping_coefficient: float
    damping_type: str
    natural_frequency: float
    current_velocity: float
    target_value: float
    chaotic_enabled: bool
    lyapunov_exponent: float
    attractor_strength: float
    secure_entropy_enabled: bool = True
    secure_entropy_intensity: float = 0.15
    entropy_source_info: Optional[Dict[str, Any]] = None
    history: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（datetime を ISO 文字列に変換）"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        # historyの値を確実にfloatに変換
        data['history'] = [float(v) for v in self.history]
        # 数値フィールドを確実に標準型に変換
        data['amplitude'] = float(self.amplitude)
        data['frequency'] = float(self.frequency)
        data['phase'] = float(self.phase)
        data['pink_noise_intensity'] = float(self.pink_noise_intensity)
        data['spectral_slope'] = float(self.spectral_slope)
        data['damping_coefficient'] = float(self.damping_coefficient)
        data['natural_frequency'] = float(self.natural_frequency)
        data['current_velocity'] = float(self.current_velocity)
        data['target_value'] = float(self.target_value)
        data['lyapunov_exponent'] = float(self.lyapunov_exponent)
        data['attractor_strength'] = float(self.attractor_strength)
        data['secure_entropy_intensity'] = float(self.secure_entropy_intensity)
        data['pink_noise_enabled'] = bool(self.pink_noise_enabled)
        data['chaotic_enabled'] = bool(self.chaotic_enabled)
        data['secure_entropy_enabled'] = bool(self.secure_entropy_enabled)
        data['damping_type'] = str(self.damping_type)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OscillationPatternData':
        """辞書から復元（ISO 文字列を datetime に変換）"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                data['timestamp'] = datetime.now()
        # historyの値を確実にfloatに変換
        if 'history' in data and isinstance(data['history'], list):
            data['history'] = [float(v) for v in data['history']]
        return cls(**data)
    
    def add_to_history(self, value: float, max_history: int = 1000):
        """履歴に値を追加"""
        # 値を確実にfloatに変換
        self.history.append(float(value))
        # 履歴サイズ制限
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
    
    def get_recent_history(self, count: int = 10) -> List[float]:
        """最近の履歴を取得"""
        if not self.history:
            return []
        # float型のリストとして返す
        return [float(v) for v in self.history[-count:]]
    
    def calculate_stability(self) -> float:
        """安定性を計算"""
        if not self.history or len(self.history) < 2:
            return 1.0
        
        import numpy as np
        # NumPy配列に変換して計算
        history_array = np.array(self.history)
        variance = float(np.var(history_array))
        # 安定性をfloatとして返す
        return float(1.0 / (1.0 + variance * 10.0))
    
    def calculate_average_amplitude(self) -> float:
        """平均振幅を計算"""
        if not self.history:
            return float(self.amplitude)
        
        import numpy as np
        # 平均振幅をfloatとして返す
        return float(np.mean(np.abs(self.history)))
    
    def is_converging(self, threshold: float = 0.01) -> bool:
        """収束しているかチェック"""
        if len(self.history) < 10:
            return False
        
        recent = self.history[-10:]
        import numpy as np
        # 標準偏差をfloatとして計算
        std = float(np.std(recent))
        return std < threshold
    
    def get_phase_shift(self) -> float:
        """位相シフトを取得"""
        # floatとして返す
        return float(self.phase % (2 * 3.14159265359))  # 2π
    
    def update_velocity(self, new_position: float, time_delta: float):
        """速度を更新"""
        if self.history and time_delta > 0:
            old_position = float(self.history[-1])
            # 速度をfloatとして計算
            self.current_velocity = float((float(new_position) - old_position) / float(time_delta))
    
    def apply_damping(self) -> float:
        """減衰を適用"""
        if self.damping_type == "underdamped":
            damping_factor = float(1.0 - self.damping_coefficient * 0.1)
        elif self.damping_type == "critically_damped":
            damping_factor = float(1.0 - self.damping_coefficient * 0.5)
        elif self.damping_type == "overdamped":
            damping_factor = float(1.0 - self.damping_coefficient * 0.8)
        else:
            damping_factor = 1.0
        
        # 範囲内に収めてfloatとして返す
        return float(max(0.0, min(1.0, damping_factor)))
    
    def get_energy(self) -> float:
        """システムのエネルギーを計算"""
        # 運動エネルギー
        kinetic = float(0.5 * (float(self.current_velocity) ** 2))
        # ポテンシャルエネルギー
        if self.history:
            potential = float(0.5 * (float(self.history[-1]) ** 2))
        else:
            potential = 0.0
        # 合計エネルギーをfloatとして返す
        return float(kinetic + potential)
    
    def get_entropy_contribution(self) -> float:
        """エントロピー寄与度を取得"""
        if self.secure_entropy_enabled:
            return float(self.secure_entropy_intensity)
        return 0.0
    
    def clone(self) -> 'OscillationPatternData':
        """パターンのクローンを作成"""
        # historyのコピーも確実にfloat型で作成
        history_copy = [float(v) for v in self.history]
        
        return OscillationPatternData(
            amplitude=float(self.amplitude),
            frequency=float(self.frequency),
            phase=float(self.phase),
            pink_noise_enabled=self.pink_noise_enabled,
            pink_noise_intensity=float(self.pink_noise_intensity),
            spectral_slope=float(self.spectral_slope),
            damping_coefficient=float(self.damping_coefficient),
            damping_type=self.damping_type,
            natural_frequency=float(self.natural_frequency),
            current_velocity=float(self.current_velocity),
            target_value=float(self.target_value),
            chaotic_enabled=self.chaotic_enabled,
            lyapunov_exponent=float(self.lyapunov_exponent),
            attractor_strength=float(self.attractor_strength),
            secure_entropy_enabled=self.secure_entropy_enabled,
            secure_entropy_intensity=float(self.secure_entropy_intensity),
            entropy_source_info=self.entropy_source_info.copy() if self.entropy_source_info else None,
            history=history_copy,
            timestamp=self.timestamp
        )
