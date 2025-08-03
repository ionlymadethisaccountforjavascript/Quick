#importing all libraries
import librosa
import soundfile as sf
import scipy
import numpy as np
import aubio
import crepe
import resampy
import pyrubberband as pyrb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import sklearn
import pydub
from pydub import AudioSegment
from pydub.playback import play
import tensorflow as tf

audio = AudioSegment.from_file('./sample.mp3',format = 'mp3')
#pitch detection
def detect_pitch(audio_file, sample_rate=22050):
    """
    Detect pitch using CREPE
    """
    y, sr = librosa.load(audio_file, sr=sample_rate)
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
    return time, frequency, confidence, y, sr
print(detect_pitch(audio.export('output.mp3',format='mp3')))

# Add this to your existing imports
import scipy.signal

# Define musical note frequencies (12-tone equal temperament)
def get_note_frequencies():
    """
    Generate note frequencies for 12-tone equal temperament
    Returns frequencies for notes from C0 to C8
    """
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    frequencies = {}
    
    for octave in range(9):  # C0 to C8
        for i, note in enumerate(notes):
            # A4 = 440 Hz is our reference
            # Formula: f = 440 * 2^((n-69)/12) where n is MIDI note number
            midi_note = octave * 12 + i
            freq = 440.0 * (2 ** ((midi_note - 69) / 12))
            frequencies[f"{note}{octave}"] = freq
    
    return frequencies

def find_closest_note(frequency, note_frequencies):
    """
    Find the closest musical note to a given frequency
    """
    if frequency <= 0:
        return 0, 0
    
    min_diff = float('inf')
    closest_freq = 0
    
    for note, note_freq in note_frequencies.items():
        diff = abs(frequency - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_freq = note_freq
    
    return closest_freq, min_diff

def autotune_audio(audio_file, output_file, strength=1.0, sample_rate=22050):
    """
    Apply autotune effect to audio
    
    Parameters:
    - audio_file: path to input audio file
    - output_file: path to output audio file
    - strength: autotune strength (0.0 = no effect, 1.0 = full correction)
    - sample_rate: sample rate for processing
    """
    
    # Load audio
    y, sr = librosa.load(audio_file, sr=sample_rate)
    
    # Get note frequencies
    note_frequencies = get_note_frequencies()
    
    # Detect pitch using CREPE
    print("Detecting pitch...")
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
    
    # Create corrected frequency array
    corrected_frequencies = []
    
    print("Correcting pitch...")
    for i, freq in enumerate(frequency):
        if confidence[i] > 0.5:  # Only correct if confidence is high enough
            closest_freq, _ = find_closest_note(freq, note_frequencies)
            # Apply correction based on strength
            corrected_freq = freq + strength * (closest_freq - freq)
            corrected_frequencies.append(corrected_freq)
        else:
            corrected_frequencies.append(freq)  # Keep original if low confidence
    
    corrected_frequencies = np.array(corrected_frequencies)
    
    # Calculate pitch shift ratios
    pitch_ratios = []
    for i, (original, corrected) in enumerate(zip(frequency, corrected_frequencies)):
        if original > 0 and confidence[i] > 0.5:
            ratio = corrected / original
            pitch_ratios.append(ratio)
        else:
            pitch_ratios.append(1.0)  # No change
    
    # Apply pitch correction using pyrubberband
    print("Applying pitch correction...")
    
    # We need to apply pitch shifting in chunks that correspond to the time resolution
    # of our pitch detection
    corrected_audio = np.copy(y)
    
    # Calculate samples per time step
    hop_length = 512  # CREPE default
    samples_per_step = hop_length
    
    for i in range(len(pitch_ratios) - 1):
        start_sample = i * samples_per_step
        end_sample = min((i + 1) * samples_per_step, len(y))
        
        if end_sample > start_sample:
            chunk = y[start_sample:end_sample]
            
            # Apply pitch shift if ratio is significantly different from 1.0
            if abs(pitch_ratios[i] - 1.0) > 0.01:
                # Convert ratio to semitones for pyrubberband
                semitones = 12 * np.log2(pitch_ratios[i])
                
                try:
                    shifted_chunk = pyrb.pitch_shift(chunk, sr, semitones)
                    corrected_audio[start_sample:end_sample] = shifted_chunk
                except:
                    # If pitch shift fails, keep original
                    pass
    
    # Save the corrected audio
    sf.write(output_file, corrected_audio, sr)
    print(f"Autotuned audio saved to {output_file}")
    
    return corrected_audio, sr, time, frequency, corrected_frequencies, confidence

def plot_pitch_correction(time, original_freq, corrected_freq, confidence):
    """
    Plot the original vs corrected pitch
    """
    plt.figure(figsize=(12, 8))
    
    # Only plot frequencies where confidence is high
    mask = confidence > 0.5
    
    plt.subplot(2, 1, 1)
    plt.plot(time[mask], original_freq[mask], 'b-', alpha=0.7, label='Original Pitch')
    plt.plot(time[mask], corrected_freq[mask], 'r-', alpha=0.7, label='Corrected Pitch')
    plt.ylabel('Frequency (Hz)')
    plt.title('Pitch Correction')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(time, confidence, 'g-', alpha=0.7)
    plt.ylabel('Confidence')
    plt.xlabel('Time (s)')
    plt.title('Pitch Detection Confidence')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

# Usage example:
def apply_autotune_to_file(input_file, strength=0.8):
    """
    Complete autotune pipeline
    """
    output_file = input_file.replace('.mp3', '_autotuned.wav')
    
    # Apply autotune
    corrected_audio, sr, time, original_freq, corrected_freq, confidence = autotune_audio(
        input_file, output_file, strength=strength
    )
    
    # Plot results
    plot_pitch_correction(time, original_freq, corrected_freq, confidence)
    
    print(f"Original file: {input_file}")
    print(f"Autotuned file: {output_file}")
    print(f"Autotune strength: {strength}")
    
    return output_file

# Replace your existing code with this:
if __name__ == "__main__":
    # Load your audio file
    audio = AudioSegment.from_file('./sample.mp3', format='mp3')
    
    # Export to temporary file for processing
    temp_file = 'temp_audio.wav'
    audio.export(temp_file, format='wav')
    
    # Apply autotune with different strength levels
    print("Applying light autotune (strength=0.3)...")
    light_autotune = apply_autotune_to_file(temp_file, strength=0.3)
    
    print("\nApplying medium autotune (strength=0.6)...")
    medium_autotune = apply_autotune_to_file(temp_file, strength=0.6)
    
    print("\nApplying heavy autotune (strength=1.0)...")
    heavy_autotune = apply_autotune_to_file(temp_file, strength=1.0)
    
    # Clean up temporary file
    import os
    os.remove(temp_file)
