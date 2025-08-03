from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pydub import AudioSegment
import soundfile as sf
import librosa
import numpy as np
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def snap_to_scale(freq, scale_freqs):
    """Snap a frequency to the nearest frequency in the given scale"""
    if freq == 0:
        return freq
    
    # Convert to cents for better comparison
    freq_cents = 1200 * np.log2(freq / 440)  # A4 = 440Hz as reference
    scale_cents = [1200 * np.log2(f / 440) for f in scale_freqs]
    
    # Find nearest scale frequency
    differences = [abs(freq_cents - sc) for sc in scale_cents]
    nearest_idx = np.argmin(differences)
    
    return scale_freqs[nearest_idx]

def get_major_scale_frequencies():
    """Generate frequencies for C major scale across multiple octaves"""
    # C major scale note ratios
    note_ratios = [1.0, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8]  # C D E F G A B
    
    frequencies = []
    # Generate frequencies for multiple octaves (C2 to C7)
    for octave in range(2, 8):
        base_freq = 261.63 * (2 ** (octave - 4))  # C4 = 261.63 Hz
        for ratio in note_ratios:
            frequencies.append(base_freq * ratio)
    
    return sorted(frequencies)

def autotune_audio(y, sr, strength=0.8, scale_freqs=None):
    """
    Apply autotune effect to audio signal
    
    Parameters:
    - y: audio time series
    - sr: sample rate
    - strength: autotune strength (0.0 = no effect, 1.0 = full snap to scale)
    - scale_freqs: list of frequencies to snap to
    """
    if scale_freqs is None:
        scale_freqs = get_major_scale_frequencies()
    
    # Use librosa's piptrack for pitch detection
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
    
    # Get fundamental frequency for each frame
    fundamental_freqs = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        fundamental_freqs.append(pitch if pitch > 0 else 0)
    
    # Convert to numpy array
    fundamental_freqs = np.array(fundamental_freqs)
    
    # Apply autotune by shifting pitch towards nearest scale frequency
    autotuned_y = np.copy(y)
    
    # Process in overlapping windows
    hop_length = 512
    frame_length = 2048
    
    for i, freq in enumerate(fundamental_freqs):
        if freq > 0:  # Only process frames with detected pitch
            # Find the target frequency in the scale
            target_freq = snap_to_scale(freq, scale_freqs)
            
            # Calculate pitch shift in semitones
            if target_freq > 0 and freq > 0:
                # Calculate the pitch shift needed
                pitch_shift_cents = 1200 * np.log2(target_freq / freq)
                pitch_shift_semitones = pitch_shift_cents / 100
                
                # Apply strength factor
                pitch_shift_semitones *= strength
                
                # Get the audio segment for this frame
                start_sample = i * hop_length
                end_sample = min(start_sample + frame_length, len(y))
                
                if end_sample > start_sample:
                    # Extract and shift the audio segment
                    segment = y[start_sample:end_sample]
                    
                    # Apply pitch shift using librosa
                    if abs(pitch_shift_semitones) > 0.1:  # Only shift if significant
                        try:
                            shifted_segment = librosa.effects.pitch_shift(
                                segment, sr=sr, n_steps=pitch_shift_semitones
                            )
                            
                            # Blend the shifted segment back
                            autotuned_y[start_sample:end_sample] = shifted_segment[:len(autotuned_y[start_sample:end_sample])]
                        except:
                            # If pitch shift fails, keep original
                            pass
    
    return autotuned_y

def process_audio(input_path, output_path, filetype, strength=0.8):
    """
    Process the audio file with autotune effect
    """
    try:
        print(f"Loading audio file: {input_path}")
        
        # Load audio using librosa for better compatibility
        y, sr = librosa.load(input_path, sr=None)
        print(f"Loaded audio - Sample rate: {sr}, Duration: {len(y)/sr:.2f}s")
        
        # Apply autotune effect
        print(f"Applying autotune with strength: {strength}")
        autotuned_y = autotune_audio(y, sr, strength=strength)
        
        # Normalize audio to prevent clipping
        autotuned_y = librosa.util.normalize(autotuned_y)
        
        # Save the processed audio
        print(f"Saving processed audio to: {output_path}")
        sf.write(output_path, autotuned_y, sr)
        
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
    
    # Get autotune strength from form data
    strength = float(request.form.get('strength', 0.8))
    strength = max(0.1, min(1.0, strength))  # Clamp between 0.1 and 1.0
    
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
        output_filename = f"{file_id}_processed.wav"  # Always output as WAV for quality
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = process_audio(input_path, output_path, file_extension, strength)
        
        if success:
            return jsonify({
                'message': 'File processed successfully with autotune',
                'file_id': file_id,
                'original_name': filename,
                'processed_name': f"{filename.rsplit('.', 1)[0]}_autotuned.wav",
                'strength_used': strength
            }), 200
        else:
            return jsonify({'error': 'Failed to process audio with autotune'}), 500
    
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
    return jsonify({'status': 'AutoTune server is running'}), 200

if __name__ == '__main__':
    print("Starting AutoTune Flask server...")
    print("Make sure you have installed: pip install librosa soundfile")
    app.run(debug=True, port=5000)