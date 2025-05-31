"""
Tests for oscillation analysis
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from oscillation.patterns import OscillationPatternData
from oscillation.buffer import OscillationBuffer
from oscillation.metrics import (
    calculate_basic_metrics,
    calculate_stability_metrics,
    calculate_autocorrelation,
    calculate_spectral_analysis,
    assess_pink_noise_quality,
    calculate_chaos_metrics,
    calculate_oscillation_metrics
)


class TestOscillationPatternData:
    """Test oscillation pattern data"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = OscillationPatternData(
            amplitude=0.5,
            frequency=1.0,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.2,
            spectral_slope=-1.0,
            damping_coefficient=0.8,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5
        )
        
        assert pattern.amplitude == 0.5
        assert pattern.frequency == 1.0
        assert pattern.secure_entropy_enabled is True
        assert pattern.secure_entropy_intensity == 0.15
        assert isinstance(pattern.timestamp, datetime)
    
    def test_to_from_dict(self):
        """Test serialization and deserialization"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=1.57,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.1,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5,
            history=[0.1, 0.2, 0.3]
        )
        
        # Convert to dict
        data = pattern.to_dict()
        assert isinstance(data["timestamp"], str)
        
        # Recreate from dict
        new_pattern = OscillationPatternData.from_dict(data)
        assert new_pattern.amplitude == pattern.amplitude
        assert new_pattern.frequency == pattern.frequency
        assert new_pattern.history == pattern.history
    
    def test_add_to_history(self):
        """Test adding values to history"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5
        )
        
        # Add values
        for i in range(10):
            pattern.add_to_history(i * 0.1)
        
        assert len(pattern.history) == 10
        assert pattern.history[-1] == 0.9
    
    def test_history_limit(self):
        """Test history size limit"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5
        )
        
        # Add more than limit
        for i in range(1100):
            pattern.add_to_history(i * 0.001, max_history=1000)
        
        assert len(pattern.history) == 1000
    
    def test_calculate_stability(self):
        """Test stability calculation"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5,
            history=[0.1, 0.1, 0.1, 0.1, 0.1]  # Stable values
        )
        
        stability = pattern.calculate_stability()
        assert stability > 0.9  # Should be very stable
        
        # Add varying values
        pattern.history = [0.1, 0.5, -0.3, 0.8, -0.6]
        stability = pattern.calculate_stability()
        assert stability < 0.5  # Should be less stable
    
    def test_is_converging(self):
        """Test convergence detection"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5
        )
        
        # Not enough data
        pattern.history = [0.1, 0.1]
        assert pattern.is_converging() is False
        
        # Converged values
        pattern.history = [0.5] * 20
        assert pattern.is_converging(threshold=0.01) is True
        
        # Not converged
        pattern.history = [i * 0.1 for i in range(20)]
        assert pattern.is_converging(threshold=0.01) is False
    
    def test_apply_damping(self):
        """Test damping application"""
        # Underdamped
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.5,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5
        )
        
        damping = pattern.apply_damping()
        assert 0.9 <= damping <= 1.0
        
        # Critically damped
        pattern.damping_type = "critically_damped"
        damping = pattern.apply_damping()
        assert 0.7 <= damping <= 0.8
        
        # Overdamped
        pattern.damping_type = "overdamped"
        damping = pattern.apply_damping()
        assert 0.5 <= damping <= 0.7
    
    def test_get_energy(self):
        """Test energy calculation"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.5,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5,
            history=[0.3]
        )
        
        energy = pattern.get_energy()
        assert energy > 0
        
        # Energy should be sum of kinetic and potential
        kinetic = 0.5 * (0.5 ** 2)
        potential = 0.5 * (0.3 ** 2)
        assert abs(energy - (kinetic + potential)) < 0.001
    
    def test_clone(self):
        """Test pattern cloning"""
        pattern = OscillationPatternData(
            amplitude=0.3,
            frequency=0.5,
            phase=0.0,
            pink_noise_enabled=True,
            pink_noise_intensity=0.15,
            spectral_slope=-1.0,
            damping_coefficient=0.7,
            damping_type="underdamped",
            natural_frequency=2.0,
            current_velocity=0.0,
            target_value=0.0,
            chaotic_enabled=False,
            lyapunov_exponent=0.1,
            attractor_strength=0.5,
            history=[0.1, 0.2, 0.3]
        )
        
        clone = pattern.clone()
        assert clone.amplitude == pattern.amplitude
        assert clone.history == pattern.history
        assert clone is not pattern
        assert clone.history is not pattern.history


class TestOscillationBuffer:
    """Test oscillation buffer"""
    
    def test_initialization(self, oscillation_buffer):
        """Test buffer initialization"""
        assert oscillation_buffer.max_size == 100
        assert len(oscillation_buffer.values) == 0
        assert len(oscillation_buffer.timestamps) == 0
    
    def test_add_single_value(self, oscillation_buffer):
        """Test adding single value"""
        oscillation_buffer.add(0.5)
        
        assert len(oscillation_buffer.values) == 1
        assert oscillation_buffer.values[0] == 0.5
        assert isinstance(oscillation_buffer.timestamps[0], datetime)
    
    def test_add_multiple_values(self, oscillation_buffer):
        """Test adding multiple values"""
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        oscillation_buffer.add_multiple(values)
        
        assert len(oscillation_buffer.values) == 5
        assert list(oscillation_buffer.values) == values
    
    def test_buffer_limit(self, oscillation_buffer):
        """Test buffer size limit"""
        # Add more than max size
        for i in range(150):
            oscillation_buffer.add(i * 0.01)
        
        assert len(oscillation_buffer.values) == 100
        assert oscillation_buffer.values[0] == 0.5  # First 50 removed
    
    def test_get_recent(self, oscillation_buffer):
        """Test getting recent values"""
        for i in range(20):
            oscillation_buffer.add(i * 0.1)
        
        recent = oscillation_buffer.get_recent(5)
        assert recent == [1.5, 1.6, 1.7, 1.8, 1.9]
    
    def test_get_statistics(self, oscillation_buffer):
        """Test statistics calculation"""
        # Empty buffer
        stats = oscillation_buffer.get_statistics()
        assert stats["count"] == 0
        assert stats["mean"] == 0.0
        
        # Add values
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        oscillation_buffer.add_multiple(values)
        
        stats = oscillation_buffer.get_statistics()
        assert stats["count"] == 5
        assert abs(stats["mean"] - 0.3) < 0.001
        assert stats["min"] == 0.1
        assert stats["max"] == 0.5
        assert stats["range"] == 0.4
    
    def test_statistics_cache(self, oscillation_buffer):
        """Test statistics caching"""
        values = [0.1, 0.2, 0.3]
        oscillation_buffer.add_multiple(values)
        
        # First call
        stats1 = oscillation_buffer.get_statistics()
        
        # Second call should use cache
        stats2 = oscillation_buffer.get_statistics()
        assert stats1 == stats2
        
        # Add new value should invalidate cache
        oscillation_buffer.add(0.4)
        stats3 = oscillation_buffer.get_statistics()
        assert stats3["count"] == 4
    
    def test_get_time_range(self, oscillation_buffer):
        """Test time range calculation"""
        # Empty buffer
        assert oscillation_buffer.get_time_range() is None
        
        # Add values with timestamps
        start_time = datetime.now()
        timestamps = [start_time + timedelta(seconds=i) for i in range(5)]
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        oscillation_buffer.add_multiple(values, timestamps)
        
        time_range = oscillation_buffer.get_time_range()
        assert time_range[0] == timestamps[0]
        assert time_range[1] == timestamps[-1]
    
    def test_get_duration(self, oscillation_buffer):
        """Test duration calculation"""
        start_time = datetime.now()
        timestamps = [start_time + timedelta(seconds=i*10) for i in range(5)]
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        oscillation_buffer.add_multiple(values, timestamps)
        
        duration = oscillation_buffer.get_duration()
        assert abs(duration - 40.0) < 0.01  # 4 intervals of 10 seconds
    
    def test_resample(self, oscillation_buffer):
        """Test resampling"""
        values = [0.0, 0.25, 0.5, 0.75, 1.0]
        oscillation_buffer.add_multiple(values)
        
        # Resample to same size
        resampled = oscillation_buffer.resample(5)
        assert resampled == values
        
        # Resample to smaller size
        resampled = oscillation_buffer.resample(3)
        assert len(resampled) == 3
        assert resampled[0] == 0.0
        assert resampled[-1] == 1.0
        
        # Resample to larger size
        resampled = oscillation_buffer.resample(9)
        assert len(resampled) == 9
    
    def test_get_derivative(self, oscillation_buffer):
        """Test derivative calculation"""
        start_time = datetime.now()
        timestamps = [start_time + timedelta(seconds=i) for i in range(5)]
        values = [0.0, 0.1, 0.3, 0.6, 1.0]
        oscillation_buffer.add_multiple(values, timestamps)
        
        derivatives = oscillation_buffer.get_derivative()
        assert len(derivatives) == 4
        
        # Check approximate derivatives
        assert abs(derivatives[0] - 0.1) < 0.01  # (0.1-0.0)/1
        assert abs(derivatives[1] - 0.2) < 0.01  # (0.3-0.1)/1
    
    def test_to_from_dict(self, oscillation_buffer):
        """Test serialization and deserialization"""
        values = [0.1, 0.2, 0.3]
        oscillation_buffer.add_multiple(values)
        
        # Convert to dict
        data = oscillation_buffer.to_dict()
        assert "values" in data
        assert "timestamps" in data
        assert "max_size" in data
        assert "statistics" in data
        
        # Create from dict
        new_buffer = OscillationBuffer.from_dict(data)
        assert new_buffer.get_values() == values
        assert new_buffer.max_size == oscillation_buffer.max_size


class TestOscillationMetrics:
    """Test oscillation metrics calculations"""
    
    def test_calculate_basic_metrics(self):
        """Test basic metrics calculation"""
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        metrics = calculate_basic_metrics(values)
        
        assert metrics["count"] == 5
        assert abs(metrics["mean"] - 0.3) < 0.001
        assert metrics["min"] == 0.1
        assert metrics["max"] == 0.5
        assert metrics["range"] == 0.4
        
        # Empty values
        metrics = calculate_basic_metrics([])
        assert metrics["count"] == 0
        assert metrics["mean"] == 0.0
    
    def test_calculate_stability_metrics(self):
        """Test stability metrics calculation"""
        # Stable values
        values = [0.5] * 10
        metrics = calculate_stability_metrics(values)
        assert metrics["stability"] > 0.99
        assert metrics["volatility"] < 0.01
        assert abs(metrics["trend"]) < 0.01
        
        # Unstable values
        values = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7]
        metrics = calculate_stability_metrics(values)
        assert metrics["stability"] < 0.5
        assert metrics["volatility"] > 0.3
        
        # Trending values
        values = list(range(10))
        metrics = calculate_stability_metrics(values)
        assert metrics["trend"] > 0.9
    
    def test_calculate_autocorrelation(self):
        """Test autocorrelation calculation"""
        # Periodic signal
        t = np.linspace(0, 4*np.pi, 50)
        values = np.sin(t).tolist()
        
        metrics = calculate_autocorrelation(values, max_lag=10)
        assert len(metrics["autocorrelations"]) > 0
        assert abs(metrics["first_order"]) > 0.8  # Strong correlation
        assert metrics["randomness_score"] < 0.3
        
        # Random signal
        np.random.seed(42)
        values = np.random.randn(50).tolist()
        metrics = calculate_autocorrelation(values, max_lag=10)
        assert abs(metrics["first_order"]) < 0.3  # Weak correlation
        assert metrics["randomness_score"] > 0.7
    
    def test_calculate_spectral_analysis(self):
        """Test spectral analysis"""
        # Single frequency signal
        t = np.linspace(0, 1, 100)
        frequency = 5.0
        values = np.sin(2 * np.pi * frequency * t).tolist()
        
        metrics = calculate_spectral_analysis(values)
        assert abs(metrics["dominant_frequency"] - frequency/100) < 0.1
        assert metrics["spectral_power"] > 0
        assert len(metrics["frequency_distribution"]) > 0
        
        # Too few values
        metrics = calculate_spectral_analysis([0.1, 0.2])
        assert metrics["dominant_frequency"] == 0.0
    
    def test_assess_pink_noise_quality(self):
        """Test pink noise assessment"""
        # Generate approximate 1/f noise
        np.random.seed(42)
        n = 128
        white = np.random.randn(n)
        fft_white = np.fft.fft(white)
        
        # Apply 1/f filter
        freqs = np.fft.fftfreq(n)
        freqs[0] = 1e-10  # Avoid division by zero
        fft_pink = fft_white / np.sqrt(np.abs(freqs))
        pink = np.real(np.fft.ifft(fft_pink)).tolist()
        
        metrics = assess_pink_noise_quality(pink)
        assert metrics["pink_noise_quality"] > 0.3
        assert metrics["spectral_slope"] < -0.5
        
        # White noise should have poor pink quality
        white_values = np.random.randn(128).tolist()
        metrics = assess_pink_noise_quality(white_values)
        assert metrics["pink_noise_quality"] < 0.5
    
    def test_calculate_chaos_metrics(self):
        """Test chaos metrics calculation"""
        # Regular signal
        t = np.linspace(0, 10, 100)
        values = np.sin(t).tolist()
        
        metrics = calculate_chaos_metrics(values)
        assert "lyapunov_estimate" in metrics
        assert "entropy" in metrics
        assert "fractal_dimension" in metrics
        
        # Chaotic signal (logistic map)
        def logistic_map(x, r=3.9):
            return r * x * (1 - x)
        
        x = 0.1
        chaotic_values = []
        for _ in range(100):
            x = logistic_map(x)
            chaotic_values.append(x)
        
        metrics = calculate_chaos_metrics(chaotic_values)
        assert metrics["entropy"] > 1.0  # Higher entropy for chaotic signal
    
    def test_calculate_oscillation_metrics_full(self, entropy_source):
        """Test full oscillation metrics calculation"""
        # Generate test signal
        t = np.linspace(0, 10, 100)
        values = (0.3 * np.sin(2*np.pi*0.5*t) + 0.1*np.random.randn(100)).tolist()
        
        metrics = calculate_oscillation_metrics(values, entropy_source)
        
        assert metrics["data_level"] == "full"
        assert metrics["total_samples"] == 100
        assert "mean" in metrics
        assert "stability" in metrics
        assert "first_order_autocorr" in metrics
        assert "dominant_frequency" in metrics
        assert "pink_noise_quality" in metrics
        assert "entropy" in metrics
        assert "secure_entropy_contribution" in metrics
    
    def test_calculate_oscillation_metrics_limited(self):
        """Test oscillation metrics with limited data"""
        # Very few samples
        values = [0.1, 0.2]
        metrics = calculate_oscillation_metrics(values)
        assert metrics["data_level"] == "insufficient"
        assert "error" in metrics
        
        # Basic level
        values = [0.1, 0.2, 0.3, 0.4]
        metrics = calculate_oscillation_metrics(values)
        assert metrics["data_level"] == "basic"
        assert "mean" in metrics
        assert "stability" in metrics
        
        # Intermediate level
        values = list(range(8))
        metrics = calculate_oscillation_metrics(values)
        assert metrics["data_level"] == "intermediate"
        assert "warning" in metrics
