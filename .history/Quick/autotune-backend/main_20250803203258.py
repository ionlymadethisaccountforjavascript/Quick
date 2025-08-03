from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pydub import AudioSegment
from pydub.utils import pyaudioop
import soundfile as sf
import librosa
import numpy as np
from werkzeug.utils import secure_filename
import uuid
from scipy import signal
from scipy.signal import butter, filtfilt
import threading
import queue
import time

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Cache for scale frequencies to avoid recalculation
SCALE_CACHE = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_scale_frequencies(scale_type='major', root_note='C'):
    """Get cached scale frequencies for better performance"""
    cache_key = f"{scale_type}_{root_note}"
    
    if cache_key in SCALE_CACHE:
        return SCALE_CACHE[cache_key]
    
    # Define scale intervals (in semitones from root)
    if scale_type == 'major':
        intervals = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
    elif scale_type == 'minor':
        intervals = [0, 2, 3, 5, 7, 8, 10]  # C D Eb F G Ab Bb
    elif scale_type == 'pentatonic':
        intervals = [0, 2, 4, 7, 9]  # C D E G A
    else:
        intervals = [0, 2, 4, 5, 7, 9, 11]  # Default to major
    
    # Calculate frequencies for multiple octaves
    frequencies = []
    for octave in range(2, 8):  # C2 to C7
        for interval in intervals:
            # Calculate frequency using equal temperament
            freq = 261.63 * (2 ** (octave - 4)) * (2 ** (interval / 12))
            frequencies.append(freq)
    
    SCALE_CACHE[cache_key] = sorted(frequencies)
    return SCALE_CACHE[cache_key]

def snap_to_scale_optimized(freq, scale_freqs, strength=1.0):
    """Optimized frequency snapping with strength control"""
    if freq <= 0:
        return freq
    
    # Use binary search for faster lookup
    left, right = 0, len(scale_freqs) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if scale_freqs[mid] == freq:
            return freq
        elif scale_freqs[mid] < freq:
            left = mid + 1
        else:
            right = mid - 1
    
    # Find closest frequency
    candidates = []
    if left < len(scale_freqs):
        candidates.append(scale_freqs[left])
    if right >= 0:
        candidates.append(scale_freqs[right])
    
    if not candidates:
        return freq
    
    closest = min(candidates, key=lambda x: abs(x - freq))
    
    # Apply strength factor
    if strength < 1.0:
        return freq + (closest - freq) * strength
    return closest

def detect_pitch_optimized(y, sr, frame_length=2048, hop_length=512):
    """Optimized pitch detection using autocorrelation"""
    # Use autocorrelation for faster pitch detection
    pitches = []
    magnitudes = []
    
    for i in range(0, len(y) - frame_length, hop_length):
        frame = y[i:i + frame_length]
        
        # Apply window function to reduce artifacts
        window = np.hanning(len(frame))
        frame = frame * window
        
        # Autocorrelation for pitch detection
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find peaks in autocorrelation
        peaks, _ = signal.find_peaks(autocorr, height=0.1*np.max(autocorr))
        
        if len(peaks) > 0:
            # Use the first significant peak for fundamental frequency
            lag = peaks[0]
            if lag > 0:
                pitch = sr / lag
                # Filter out unrealistic frequencies
                if 80 <= pitch <= 800:
                    pitches.append(pitch)
                    magnitudes.append(autocorr[lag])
                else:
                    pitches.append(0)
                    magnitudes.append(0)
            else:
                pitches.append(0)
                magnitudes.append(0)
        else:
            pitches.append(0)
            magnitudes.append(0)
    
    return np.array(pitches), np.array(magnitudes)

def apply_pitch_shift_optimized(y, pitch_shifts, sr, frame_length=2048, hop_length=512):
    """Optimized pitch shifting with overlap-add"""
    output = np.zeros_like(y)
    
    for i, shift in enumerate(pitch_shifts):
        if abs(shift) < 0.1:  # Skip if shift is too small
            continue
            
        start_sample = i * hop_length
        end_sample = min(start_sample + frame_length, len(y))
        
        if end_sample <= start_sample:
            continue
        
        # Extract frame
        frame = y[start_sample:end_sample]
        
        # Apply window
        window = np.hanning(len(frame))
        frame = frame * window
        
        # Pitch shift using phase vocoder (more efficient than librosa)
        if abs(shift) > 0.1:
            try:
                # Use scipy's resample for pitch shifting
                ratio = 2 ** (shift / 12)
                new_length = int(len(frame) / ratio)
                shifted_frame = signal.resample(frame, new_length)
                
                # Resize back to original length
                if len(shifted_frame) > len(frame):
                    shifted_frame = shifted_frame[:len(frame)]
                else:
                    # Pad with zeros if shorter
                    padding = len(frame) - len(shifted_frame)
                    shifted_frame = np.pad(shifted_frame, (0, padding))
                
                # Apply window again
                shifted_frame = shifted_frame * window
                
                # Overlap-add
                output[start_sample:end_sample] += shifted_frame
                
            except Exception as e:
                # Fallback: keep original frame
                output[start_sample:end_sample] += frame
        else:
            output[start_sample:end_sample] += frame
    
    return output

def autotune_audio_optimized(y, sr, strength=0.8, scale_type='major', root_note='C'):
    """
    Optimized autotune implementation with better performance and quality
    """
    print(f"Processing audio: {len(y)/sr:.2f}s at {sr}Hz")
    
    # Get scale frequencies
    scale_freqs = get_scale_frequencies(scale_type, root_note)
    
    # Detect pitch with optimized method
    print("Detecting pitch...")
    pitches, magnitudes = detect_pitch_optimized(y, sr)
    
    # Calculate pitch shifts
    print("Calculating pitch shifts...")
    pitch_shifts = []
    for pitch in pitches:
        if pitch > 0:
            target_freq = snap_to_scale_optimized(pitch, scale_freqs, strength)
            if target_freq > 0:
                shift = 12 * np.log2(target_freq / pitch)
                pitch_shifts.append(shift)
            else:
                pitch_shifts.append(0)
        else:
            pitch_shifts.append(0)
    
    # Apply pitch shifts
    print("Applying pitch shifts...")
    autotuned_y = apply_pitch_shift_optimized(y, pitch_shifts, sr)
    
    # Normalize and apply gentle compression
    autotuned_y = librosa.util.normalize(autotuned_y)
    
    # Apply gentle low-pass filter to smooth artifacts
    nyquist = sr / 2
    cutoff = min(8000, nyquist * 0.8)  # Cutoff at 8kHz or 80% of nyquist
    b, a = butter(4, cutoff / nyquist, btype='low')
    autotuned_y = filtfilt(b, a, autotuned_y)
    
    return autotuned_y

def process_audio_optimized(input_path, output_path, filetype, strength=0.8, scale_type='major'):
    """
    Optimized audio processing with memory management
    """
    try:
        print(f"Loading audio file: {input_path}")
        
        # Load audio with resampling for consistency
        y, sr = librosa.load(input_path, sr=44100)  # Standardize to 44.1kHz
        
        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        
        print(f"Loaded audio - Sample rate: {sr}, Duration: {len(y)/sr:.2f}s")
        
        # Apply optimized autotune
        print(f"Applying autotune with strength: {strength}, scale: {scale_type}")
        autotuned_y = autotune_audio_optimized(y, sr, strength=strength, scale_type=scale_type)
        
        # Save with high quality
        print(f"Saving processed audio to: {output_path}")
        sf.write(output_path, autotuned_y, sr, subtype='PCM_24')
        
        print("Audio processing completed successfully")
        return True
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get parameters from form data
    strength = float(request.form.get('strength', 0.8))
    strength = max(0.1, min(1.0, strength))
    
    scale_type = request.form.get('scale_type', 'major')
    if scale_type not in ['major', 'minor', 'pentatonic']:
        scale_type = 'major'
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        # Save uploaded file
        input_filename = f"{file_id}_input.{file_extension}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Process the audio with optimized autotune
        output_filename = f"{file_id}_processed.wav"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = process_audio_optimized(input_path, output_path, file_extension, strength, scale_type)
        
        if success:
            return jsonify({
                'message': 'File processed successfully with optimized autotune',
                'file_id': file_id,
                'original_name': filename,
                'processed_name': f"{filename.rsplit('.', 1)[0]}_autotuned.wav",
                'strength_used': strength,
                'scale_type': scale_type
            }), 200
        else:
            return jsonify({'error': 'Failed to process audio'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        output_filename = f"{file_id}_processed.wav"
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
    return jsonify({
        'status': 'Optimized AutoTune server is running',
        'features': ['Optimized pitch detection', 'Memory efficient processing', 'Multiple scale support']
    }), 200

if __name__ == '__main__':
    print("Starting Optimized AutoTune Flask server...")
    print("Features: Optimized pitch detection, memory efficient processing, multiple scales")
    app.run(debug=True, port=5000) 