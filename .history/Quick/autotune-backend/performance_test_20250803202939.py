import time
import librosa
import numpy as np
import psutil
import os
from main import autotune_audio, get_major_scale_frequencies
from optimized_autotune import autotune_audio_optimized, get_scale_frequencies

def measure_performance(func, *args, **kwargs):
    """Measure execution time and memory usage of a function"""
    process = psutil.Process(os.getpid())
    
    # Memory before
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Time execution
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    # Memory after
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    
    execution_time = end_time - start_time
    memory_used = mem_after - mem_before
    
    return result, execution_time, memory_used

def test_autotune_performance():
    """Compare performance between original and optimized autotune"""
    
    # Load a test audio file
    print("Loading test audio...")
    try:
        # Try to load from sample.mp3 if it exists
        if os.path.exists("../sample.mp3"):
            y, sr = librosa.load("../sample.mp3", sr=44100)
        else:
            # Generate synthetic audio for testing
            print("No sample file found, generating synthetic audio...")
            duration = 10  # 10 seconds
            sr = 44100
            t = np.linspace(0, duration, int(sr * duration))
            
            # Generate a melody with some off-key notes
            freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]  # C major scale
            y = np.zeros_like(t)
            
            for i, freq in enumerate(freqs):
                start_time = i * duration / len(freqs)
                end_time = (i + 1) * duration / len(freqs)
                mask = (t >= start_time) & (t < end_time)
                y[mask] = 0.3 * np.sin(2 * np.pi * freq * t[mask])
            
            # Add some noise and off-key notes
            y += 0.1 * np.random.normal(0, 1, len(y))
        
        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        
        print(f"Test audio: {len(y)/sr:.2f}s at {sr}Hz")
        
    except Exception as e:
        print(f"Error loading test audio: {e}")
        return
    
    # Test original implementation
    print("\n" + "="*50)
    print("TESTING ORIGINAL IMPLEMENTATION")
    print("="*50)
    
    try:
        result_original, time_original, mem_original = measure_performance(
            autotune_audio, y, sr, strength=0.8
        )
        print(f"Original Implementation:")
        print(f"  Execution time: {time_original:.2f} seconds")
        print(f"  Memory usage: {mem_original:.2f} MB")
        print(f"  Success: ✓")
    except Exception as e:
        print(f"Original Implementation failed: {e}")
        time_original = float('inf')
        mem_original = float('inf')
    
    # Test optimized implementation
    print("\n" + "="*50)
    print("TESTING OPTIMIZED IMPLEMENTATION")
    print("="*50)
    
    try:
        result_optimized, time_optimized, mem_optimized = measure_performance(
            autotune_audio_optimized, y, sr, strength=0.8, scale_type='major'
        )
        print(f"Optimized Implementation:")
        print(f"  Execution time: {time_optimized:.2f} seconds")
        print(f"  Memory usage: {mem_optimized:.2f} MB")
        print(f"  Success: ✓")
    except Exception as e:
        print(f"Optimized Implementation failed: {e}")
        time_optimized = float('inf')
        mem_optimized = float('inf')
    
    # Performance comparison
    print("\n" + "="*50)
    print("PERFORMANCE COMPARISON")
    print("="*50)
    
    if time_original != float('inf') and time_optimized != float('inf'):
        speedup = time_original / time_optimized
        print(f"Speed improvement: {speedup:.2f}x faster")
        
        if speedup > 1:
            print(f"  ✓ Optimized version is {speedup:.2f}x faster")
        else:
            print(f"  ⚠ Original version is {1/speedup:.2f}x faster")
    
    if mem_original != float('inf') and mem_optimized != float('inf'):
        memory_improvement = mem_original / mem_optimized
        print(f"Memory efficiency: {memory_improvement:.2f}x more efficient")
        
        if memory_improvement > 1:
            print(f"  ✓ Optimized version uses {memory_improvement:.2f}x less memory")
        else:
            print(f"  ⚠ Original version uses {1/memory_improvement:.2f}x less memory")
    
    # Feature comparison
    print("\n" + "="*50)
    print("FEATURE COMPARISON")
    print("="*50)
    
    print("Original Implementation:")
    print("  ✓ Basic autotune functionality")
    print("  ✓ Major scale support")
    print("  ⚠ Frame-by-frame processing")
    print("  ⚠ Uses librosa.piptrack (slower)")
    print("  ⚠ No caching")
    
    print("\nOptimized Implementation:")
    print("  ✓ Enhanced autotune functionality")
    print("  ✓ Multiple scale support (major, minor, pentatonic)")
    print("  ✓ Optimized pitch detection (autocorrelation)")
    print("  ✓ Binary search for frequency lookup")
    print("  ✓ Scale frequency caching")
    print("  ✓ Overlap-add processing")
    print("  ✓ Low-pass filtering for artifact reduction")
    print("  ✓ Memory-efficient processing")
    print("  ✓ Better error handling")

def test_scale_generation():
    """Test scale generation performance"""
    print("\n" + "="*50)
    print("SCALE GENERATION PERFORMANCE")
    print("="*50)
    
    # Test original scale generation
    start_time = time.time()
    for _ in range(100):
        original_scales = get_major_scale_frequencies()
    original_time = time.time() - start_time
    
    # Test optimized scale generation (with caching)
    start_time = time.time()
    for _ in range(100):
        optimized_scales = get_scale_frequencies('major', 'C')
    optimized_time = time.time() - start_time
    
    print(f"Original scale generation (100 iterations): {original_time:.4f}s")
    print(f"Optimized scale generation (100 iterations): {optimized_time:.4f}s")
    print(f"Speedup: {original_time/optimized_time:.2f}x")

if __name__ == "__main__":
    print("AUTOTUNE PERFORMANCE TEST")
    print("="*50)
    
    test_scale_generation()
    test_autotune_performance()
    
    print("\n" + "="*50)
    print("TEST COMPLETED")
    print("="*50) 