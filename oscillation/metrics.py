"""
Oscillation metrics calculation
"""

from typing import List, Dict, Any, Optional
import numpy as np

from config.logging import get_logger

logger = get_logger(__name__)


def calculate_basic_metrics(values: List[float]) -> Dict[str, float]:
    """
    基本的な統計メトリクスを計算
    
    Args:
        values: 振動値のリスト
        
    Returns:
        基本メトリクス
    """
    if not values:
        return {
            "mean": 0.0,
            "std": 0.0,
            "variance": 0.0,
            "min": 0.0,
            "max": 0.0,
            "range": 0.0,
            "count": 0
        }
    
    values_array = np.array(values)
    
    # NumPy型を明示的にPython標準型に変換
    return {
        "mean": float(np.mean(values_array)),
        "std": float(np.std(values_array)),
        "variance": float(np.var(values_array)),
        "min": float(np.min(values_array)),
        "max": float(np.max(values_array)),
        "range": float(np.max(values_array) - np.min(values_array)),
        "count": int(len(values_array))  # intに変換
    }


def calculate_stability_metrics(values: List[float]) -> Dict[str, float]:
    """
    安定性メトリクスを計算
    
    Args:
        values: 振動値のリスト
        
    Returns:
        安定性メトリクス
    """
    if len(values) < 2:
        return {
            "stability": 1.0,
            "volatility": 0.0,
            "trend": 0.0
        }
    
    values_array = np.array(values)
    
    # 安定性（分散の逆数ベース）
    variance = np.var(values_array)
    stability = 1.0 / (1.0 + variance * 10.0)
    
    # ボラティリティ（連続する値の差の標準偏差）
    diffs = np.diff(values_array)
    volatility = float(np.std(diffs)) if len(diffs) > 0 else 0.0
    
    # トレンド（線形回帰の傾き）
    x = np.arange(len(values_array))
    slope, _ = np.polyfit(x, values_array, 1)
    
    # 全ての値を明示的にfloatに変換
    return {
        "stability": float(stability),
        "volatility": float(volatility),
        "trend": float(slope)
    }


def calculate_autocorrelation(values: List[float], max_lag: int = 10) -> Dict[str, Any]:
    """
    自己相関を計算
    
    Args:
        values: 振動値のリスト
        max_lag: 最大ラグ
        
    Returns:
        自己相関メトリクス
    """
    if len(values) < max_lag + 1:
        return {
            "autocorrelations": [],
            "first_order": 0.0,
            "randomness_score": 0.5
        }
    
    values_array = np.array(values)
    autocorrelations = []
    
    for lag in range(1, min(max_lag + 1, len(values) // 2)):
        if lag < len(values):
            corr = np.corrcoef(values_array[:-lag], values_array[lag:])[0, 1]
            # NaNチェックとfloat変換
            if np.isnan(corr):
                autocorrelations.append(0.0)
            else:
                autocorrelations.append(float(corr))
    
    first_order = autocorrelations[0] if autocorrelations else 0.0
    randomness_score = 1.0 - abs(first_order)
    
    return {
        "autocorrelations": autocorrelations,  # 既にfloatのリスト
        "first_order": float(first_order),
        "randomness_score": float(randomness_score)
    }


def calculate_spectral_analysis(values: List[float]) -> Dict[str, Any]:
    """
    スペクトル解析を実行
    
    Args:
        values: 振動値のリスト
        
    Returns:
        スペクトル解析結果
    """
    if len(values) < 4:
        return {
            "dominant_frequency": 0.0,
            "spectral_power": 0.0,
            "frequency_distribution": []
        }
    
    try:
        # FFT実行
        fft = np.fft.fft(values)
        frequencies = np.fft.fftfreq(len(values))
        power_spectrum = np.abs(fft) ** 2
        
        # 正の周波数のみ
        positive_freq_idx = frequencies > 0
        positive_freqs = frequencies[positive_freq_idx]
        positive_power = power_spectrum[positive_freq_idx]
        
        if len(positive_power) > 0:
            # 主要周波数
            dominant_idx = np.argmax(positive_power)
            dominant_frequency = float(positive_freqs[dominant_idx])
            
            # スペクトルパワー
            spectral_power = float(np.sum(positive_power))
            
            # 周波数分布（上位5つ）
            top_indices = np.argsort(positive_power)[-5:][::-1]
            frequency_distribution = []
            for idx in top_indices:
                if idx < len(positive_freqs):
                    freq_info = {
                        "frequency": float(positive_freqs[idx]),
                        "power": float(positive_power[idx]),
                        "relative_power": float(positive_power[idx] / spectral_power) if spectral_power > 0 else 0.0
                    }
                    frequency_distribution.append(freq_info)
        else:
            dominant_frequency = 0.0
            spectral_power = 0.0
            frequency_distribution = []
        
        return {
            "dominant_frequency": dominant_frequency,
            "spectral_power": spectral_power,
            "frequency_distribution": frequency_distribution
        }
        
    except Exception as e:
        logger.warning(f"Spectral analysis failed: {e}")
        return {
            "dominant_frequency": 0.0,
            "spectral_power": 0.0,
            "frequency_distribution": []
        }


def assess_pink_noise_quality(values: List[float]) -> Dict[str, float]:
    """
    1/fノイズ特性を評価
    
    Args:
        values: 振動値のリスト
        
    Returns:
        ピンクノイズ品質メトリクス
    """
    if len(values) < 8:
        return {
            "pink_noise_quality": 0.0,
            "spectral_slope": 0.0,
            "slope_deviation": 1.0
        }
    
    try:
        # FFT実行
        fft = np.fft.fft(values)
        frequencies = np.fft.fftfreq(len(values))
        power_spectrum = np.abs(fft) ** 2
        
        # 正の周波数のみ
        positive_freq_idx = (frequencies > 0) & (frequencies < 0.5)
        positive_freqs = frequencies[positive_freq_idx]
        positive_power = power_spectrum[positive_freq_idx]
        
        if len(positive_freqs) > 2:
            # ログスケールで線形回帰
            log_freq = np.log10(positive_freqs + 1e-10)
            log_power = np.log10(positive_power + 1e-10)
            
            # 無効値を除外
            valid_idx = np.isfinite(log_freq) & np.isfinite(log_power)
            if np.any(valid_idx):
                slope, _ = np.polyfit(log_freq[valid_idx], log_power[valid_idx], 1)
                
                # 理想的な1/fノイズは傾き-1
                ideal_slope = -1.0
                slope_deviation = abs(slope - ideal_slope)
                pink_noise_quality = max(0.0, 1.0 - slope_deviation)
            else:
                slope = 0.0
                slope_deviation = 1.0
                pink_noise_quality = 0.0
        else:
            slope = 0.0
            slope_deviation = 1.0
            pink_noise_quality = 0.0
        
        # 全ての値を明示的にfloatに変換
        return {
            "pink_noise_quality": float(pink_noise_quality),
            "spectral_slope": float(slope),
            "slope_deviation": float(slope_deviation)
        }
        
    except Exception as e:
        logger.warning(f"Pink noise assessment failed: {e}")
        return {
            "pink_noise_quality": 0.0,
            "spectral_slope": 0.0,
            "slope_deviation": 1.0
        }


def calculate_chaos_metrics(values: List[float]) -> Dict[str, float]:
    """
    カオス性メトリクスを計算
    
    Args:
        values: 振動値のリスト
        
    Returns:
        カオス性メトリクス
    """
    if len(values) < 10:
        return {
            "lyapunov_estimate": 0.0,
            "entropy": 0.0,
            "fractal_dimension": 1.0
        }
    
    try:
        values_array = np.array(values)
        
        # 簡易リアプノフ指数推定
        diffs = np.abs(np.diff(values_array))
        # ゼロ除算を防ぐ
        diffs_safe = np.where(diffs > 0, diffs, 1e-10)
        lyapunov_estimate = float(np.mean(np.log(diffs_safe)))
        
        # シャノンエントロピー
        hist, _ = np.histogram(values_array, bins=10)
        hist = hist / np.sum(hist)
        # ゼロ除算を防ぐ
        hist_safe = np.where(hist > 0, hist, 1e-10)
        entropy = float(-np.sum(hist_safe * np.log(hist_safe)))
        
        # ボックスカウント法による簡易フラクタル次元
        # （実装簡略化のため1.0-2.0の範囲に正規化）
        std = float(np.std(values_array))
        fractal_dimension = 1.0 + min(1.0, std)
        
        return {
            "lyapunov_estimate": float(lyapunov_estimate),
            "entropy": float(entropy),
            "fractal_dimension": float(fractal_dimension)
        }
        
    except Exception as e:
        logger.warning(f"Chaos metrics calculation failed: {e}")
        return {
            "lyapunov_estimate": 0.0,
            "entropy": 0.0,
            "fractal_dimension": 1.0
        }


def calculate_oscillation_metrics(values: List[float], entropy_source: Optional[Any] = None) -> Dict[str, Any]:
    """
    総合的な振動メトリクスを計算
    
    Args:
        values: 振動値のリスト
        entropy_source: エントロピー源（オプション）
        
    Returns:
        総合メトリクス
    """
    # 入力値の型確認と変換
    if isinstance(values, np.ndarray):
        values = values.tolist()
    
    # 各値をfloatに変換
    values = [float(v) for v in values]
    
    # データレベルの判定
    data_count = len(values)
    if data_count < 3:
        data_level = "insufficient"
    elif data_count < 5:
        data_level = "basic"
    elif data_count < 10:
        data_level = "intermediate"
    else:
        data_level = "full"
    
    # 基本メトリクス（常に計算）
    metrics = {
        "data_level": data_level,
        "total_samples": int(data_count)  # intに変換
    }
    
    if data_count < 3:
        metrics["error"] = "Insufficient data"
        return metrics
    
    # 基本統計
    basic = calculate_basic_metrics(values)
    metrics.update(basic)
    
    # 安定性メトリクス
    stability = calculate_stability_metrics(values)
    metrics.update(stability)
    
    # データが十分な場合は追加メトリクス
    if data_count >= 5:
        # 自己相関
        autocorr = calculate_autocorrelation(values)
        metrics["first_order_autocorr"] = autocorr["first_order"]
        metrics["entropy_randomness_score"] = autocorr["randomness_score"]
        
        if data_count >= 10:
            # スペクトル解析
            spectral = calculate_spectral_analysis(values)
            metrics["dominant_frequency"] = spectral["dominant_frequency"]
            
            # ピンクノイズ評価
            pink = assess_pink_noise_quality(values)
            metrics["pink_noise_quality"] = pink["pink_noise_quality"]
            
            # カオスメトリクス
            chaos = calculate_chaos_metrics(values)
            metrics.update(chaos)
    
    # エントロピー源情報（提供されている場合）
    if entropy_source and hasattr(entropy_source, 'assess_entropy_quality'):
        entropy_quality = entropy_source.assess_entropy_quality()
        metrics["secure_entropy_contribution"] = float(entropy_quality.get("success_rate", 0.0))
        metrics["entropy_source"] = str(entropy_quality.get("entropy_source", "unknown"))
        metrics["security_level"] = "high"
    
    # 警告メッセージ
    if data_level in ["basic", "intermediate"]:
        metrics["warning"] = f"Limited data ({data_count} samples) - results may be less accurate"
    
    return metrics
