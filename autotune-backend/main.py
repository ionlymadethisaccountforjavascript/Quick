from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pydub import AudioSegment
import soundfile as sf
from werkzeug.utils import secure_filename
import uuid
import librosa
import scipy
import numpy as np
import resampy

# Mock crepe implementation since it fails to install due to SSL issues
class MockCrepe:
    @staticmethod
    def predict(y, sr, viterbi=True):
        # Simple pitch detection using librosa as fallback
        import librosa
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        frequency = np.mean(pitches, axis=0)
        magnitudes_mean = np.mean(magnitudes, axis=0)
        confidence = magnitudes_mean / np.max(magnitudes_mean) if np.max(magnitudes_mean) > 0 else np.zeros_like(magnitudes_mean)
        time = np.arange(len(frequency)) * librosa.get_duration(y=y, sr=sr) / len(frequency)
        activation = np.zeros((len(frequency), 360))  # Mock activation matrix
        return time, frequency, confidence, activation

# Use mock crepe
crepe = MockCrepe()
import pyrubberband as pyrb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import sklearn
import tensorflow as tf
import scipy.signal

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def autotune_audio(audio_file, output_file, strength=0.8, sample_rate=22050):
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

def process_audio(input_path, output_path, filetype, strength=0.8):
    """
    Process the audio file with autotune
    """
    try:
        print(f"Starting autotune processing for {input_path}")
        
        # Convert input to wav for processing if needed
        temp_wav = None
        if filetype == "mp3":
            audio = AudioSegment.from_file(input_path, format="mp3")
            temp_wav = input_path.replace('.mp3', '_temp.wav')
            audio.export(temp_wav, format="wav")
            processing_input = temp_wav
        else:
            processing_input = input_path
        
        # Apply autotune
        corrected_audio, sr, time, original_freq, corrected_freq, confidence = autotune_audio(
            processing_input, output_path, strength=strength
        )
        
        # Clean up temporary file
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)
        
        print(f"Successfully processed audio - Sample rate: {sr}, Audio length: {len(corrected_audio)}")
        return True
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get autotune strength from form data (default: 0.8)
    strength = float(request.form.get('strength', 0.8))
    strength = max(0.0, min(1.0, strength))  # Clamp between 0 and 1
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        # Save uploaded file
        input_filename = f"{file_id}_input.{file_extension}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Process the audio with autotune
        output_filename = f"{file_id}_processed.wav"  # Changed to wav for better quality
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = process_audio(input_path, output_path, file_extension, strength)
        
        if success:
            return jsonify({
                'message': 'File processed successfully',
                'file_id': file_id,
                'original_name': filename,
                'processed_name': f"{filename.rsplit('.', 1)[0]}_autotuned.wav",
                'strength_used': strength
            }), 200
        else:
            return jsonify({'error': 'Failed to process audio'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        output_filename = f"{file_id}_processed.wav"  # Updated to wav
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, 
                           download_name=f"{file_id}_autotuned.wav")
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'Server is running'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)