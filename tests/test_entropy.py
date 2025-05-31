"""
Tests for secure entropy generation
"""

import pytest
import time
from security.entropy import SecureEntropySource
from security.pink_noise import SecureEnhancedPinkNoiseGenerator


class TestSecureEntropySource:
    """Test secure entropy source"""
    
    def test_initialization(self, entropy_source):
        """Test entropy source initialization"""
        assert entropy_source is not None
        assert entropy_source.entropy_source == "secure_combined"
        assert len(entropy_source.entropy_buffer) > 0
        assert entropy_source.buffer_size == 1000
    
    def test_get_secure_entropy(self, entropy_source):
        """Test secure entropy generation"""
        # Test different byte counts
        for bytes_count in [1, 4, 8, 16]:
            entropy = entropy_source.get_secure_entropy(bytes_count)
            assert isinstance(entropy, int)
            assert entropy >= 0
            assert entropy < (1 << (bytes_count * 8))
    
    def test_get_normalized_entropy(self, entropy_source):
        """Test normalized entropy generation"""
        for _ in range(100):
            normalized = entropy_source.get_normalized_entropy()
            assert isinstance(normalized, float)
            assert 0.0 <= normalized <= 1.0
    
    def test_get_pink_noise_component(self, entropy_source):
        """Test pink noise component generation"""
        for history_length in [3, 5, 10]:
            component = entropy_source.get_pink_noise_component(history_length)
            assert isinstance(component, float)
            assert -0.1 <= component <= 0.1  # Expected range after scaling
    
    def test_get_thermal_oscillation(self, entropy_source):
        """Test thermal oscillation generation"""
        for amplitude in [0.05, 0.1, 0.2]:
            oscillation = entropy_source.get_thermal_oscillation(amplitude)
            assert isinstance(oscillation, float)
            assert -amplitude <= oscillation <= amplitude
    
    def test_assess_entropy_quality(self, entropy_source):
        """Test entropy quality assessment"""
        quality = entropy_source.assess_entropy_quality()
        
        assert isinstance(quality, dict)
        assert "entropy_source" in quality
        assert "success_rate" in quality
        assert "architecture" in quality
        assert "system" in quality
        assert "secure_mode" in quality
        assert "entropy_sources" in quality
        
        assert quality["secure_mode"] is True
        assert isinstance(quality["entropy_sources"], list)
        assert len(quality["entropy_sources"]) > 0
    
    def test_entropy_uniqueness(self, entropy_source):
        """Test that entropy values are unique"""
        values = []
        for _ in range(100):
            values.append(entropy_source.get_secure_entropy(4))
        
        # Should have high uniqueness
        unique_values = len(set(values))
        assert unique_values > 95  # Allow for some collisions but expect mostly unique
    
    def test_entropy_distribution(self, entropy_source):
        """Test entropy distribution properties"""
        import numpy as np
        
        values = []
        for _ in range(1000):
            values.append(entropy_source.get_normalized_entropy())
        
        values_array = np.array(values)
        mean = np.mean(values_array)
        std = np.std(values_array)
        
        # Should be roughly uniform distribution
        assert 0.4 <= mean <= 0.6
        assert 0.2 <= std <= 0.35
    
    def test_buffer_refill(self, entropy_source):
        """Test entropy buffer refilling"""
        # Drain the buffer
        initial_size = len(entropy_source.entropy_buffer)
        for _ in range(initial_size + 100):
            entropy_source.get_normalized_entropy()
        
        # Buffer should have been refilled
        assert len(entropy_source.entropy_buffer) > 0
    
    def test_emergency_fallback(self, entropy_source):
        """Test emergency entropy fallback"""
        # Force a failure scenario (can't easily test without mocking)
        # Just ensure the method exists and returns valid data
        entropy = entropy_source._get_emergency_entropy(4)
        assert isinstance(entropy, int)
        assert entropy >= 0
        assert entropy < (1 << 32)


class TestSecureEnhancedPinkNoiseGenerator:
    """Test secure enhanced pink noise generator"""
    
    def test_initialization(self, pink_noise_generator):
        """Test pink noise generator initialization"""
        assert pink_noise_generator is not None
        assert pink_noise_generator.octaves == 5
        assert pink_noise_generator.key == 0
        assert len(pink_noise_generator.white_values) == 5
        assert len(pink_noise_generator.pink_values) == 0
    
    def test_generate_secure_pink_noise(self, pink_noise_generator):
        """Test secure pink noise generation"""
        values = []
        for _ in range(100):
            value = pink_noise_generator.generate_secure_pink_noise()
            assert isinstance(value, float)
            assert -1.0 <= value <= 1.0
            values.append(value)
        
        # Should have some variation
        assert min(values) < -0.1
        assert max(values) > 0.1
    
    def test_pink_noise_spectral_properties(self, pink_noise_generator):
        """Test pink noise spectral properties"""
        import numpy as np
        
        # Generate longer sequence
        values = []
        for _ in range(1000):
            values.append(pink_noise_generator.generate_secure_pink_noise())
        
        # Check autocorrelation properties
        values_array = np.array(values)
        autocorr = np.correlate(values_array, values_array, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]
        
        # Pink noise should have long-range correlations
        assert abs(autocorr[10]) > 0.1  # Still correlated at lag 10
    
    def test_reset(self, pink_noise_generator):
        """Test pink noise generator reset"""
        # Generate some values
        for _ in range(10):
            pink_noise_generator.generate_secure_pink_noise()
        
        assert pink_noise_generator.key > 0
        assert len(pink_noise_generator.pink_values) > 0
        
        # Reset
        pink_noise_generator.reset()
        
        assert pink_noise_generator.key == 0
        assert len(pink_noise_generator.pink_values) == 0
    
    def test_get_history(self, pink_noise_generator):
        """Test getting pink noise history"""
        # Generate some values
        generated = []
        for _ in range(20):
            value = pink_noise_generator.generate_secure_pink_noise()
            generated.append(value)
        
        # Get history
        history = pink_noise_generator.get_history(10)
        assert len(history) == 10
        assert history == generated[-10:]
    
    def test_get_spectral_characteristics(self, pink_noise_generator):
        """Test spectral characteristics calculation"""
        # Generate some values
        for _ in range(50):
            pink_noise_generator.generate_secure_pink_noise()
        
        chars = pink_noise_generator.get_spectral_characteristics()
        
        assert isinstance(chars, dict)
        assert "average" in chars
        assert "variance" in chars
        assert "std_deviation" in chars
        assert "min" in chars
        assert "max" in chars
        assert "history_length" in chars
        assert "octaves" in chars
        
        assert chars["history_length"] <= 100
        assert chars["octaves"] == 5
    
    def test_voss_mccartney_algorithm(self, pink_noise_generator):
        """Test Voss-McCartney algorithm implementation"""
        # The key should cycle through values
        keys_seen = set()
        for _ in range(40):
            keys_seen.add(pink_noise_generator.key)
            pink_noise_generator.generate_secure_pink_noise()
        
        # Should have seen multiple key values
        assert len(keys_seen) > 10
        
        # Key should wrap around
        max_key = pink_noise_generator.max_key
        pink_noise_generator.key = max_key
        pink_noise_generator.generate_secure_pink_noise()
        assert pink_noise_generator.key == 0


class TestEntropyIntegration:
    """Test integration between entropy and pink noise"""
    
    def test_entropy_pink_noise_integration(self, entropy_source):
        """Test integration of entropy source with pink noise generator"""
        generator = SecureEnhancedPinkNoiseGenerator(entropy_source)
        
        # Generate values using both components
        mixed_values = []
        for _ in range(100):
            pink = generator.generate_secure_pink_noise()
            thermal = entropy_source.get_thermal_oscillation(0.1)
            mixed = pink * 0.7 + thermal * 0.3
            mixed_values.append(mixed)
        
        # Should produce reasonable distribution
        import numpy as np
        mixed_array = np.array(mixed_values)
        assert -0.5 <= np.min(mixed_array) <= 0.5
        assert -0.5 <= np.max(mixed_array) <= 0.5
        assert 0.05 <= np.std(mixed_array) <= 0.3
    
    def test_entropy_quality_tracking(self, entropy_source):
        """Test entropy quality tracking over time"""
        initial_quality = entropy_source.assess_entropy_quality()
        initial_success_rate = initial_quality["success_rate"]
        
        # Generate many values
        for _ in range(1000):
            entropy_source.get_secure_entropy(4)
            entropy_source.get_normalized_entropy()
        
        final_quality = entropy_source.assess_entropy_quality()
        final_success_rate = final_quality["success_rate"]
        
        # Success rate should be very high
        assert final_success_rate >= 0.99
        
        # Total entropy bits should have increased
        assert final_quality["total_entropy_bits"] > initial_quality["total_entropy_bits"]
