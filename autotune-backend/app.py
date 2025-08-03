from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pydub import AudioSegment
import soundfile as sf
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

def process_audio(input_path, output_path, filetype):
    """
    Process the audio file - currently just converts between formats
    You can add your autotune logic here
    """
    try:
        if filetype == "mp3":
            audio = AudioSegment.from_file(input_path, format="mp3")
            data, samplerate = sf.read(input_path)
        elif filetype == "wav":
            audio = AudioSegment.from_wav(input_path)
            data, samplerate = sf.read(input_path)
        else:
            raise ValueError("Invalid file type")
        
        # For now, just export the same audio
        # TODO: Add your autotune processing logic here
        audio.export(output_path, format="mp3")
        
        print(f"Processed audio - Sample rate: {samplerate}, Data shape: {data.shape}")
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
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        # Save uploaded file
        input_filename = f"{file_id}_input.{file_extension}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Process the audio
        output_filename = f"{file_id}_processed.mp3"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = process_audio(input_path, output_path, file_extension)
        
        if success:
            return jsonify({
                'message': 'File processed successfully',
                'file_id': file_id,
                'original_name': filename,
                'processed_name': f"{filename.rsplit('.', 1)[0]}_autotuned.mp3"
            }), 200
        else:
            return jsonify({'error': 'Failed to process audio'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        output_filename = f"{file_id}_processed.mp3"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, 
                           download_name=f"{file_id}_autotuned.mp3")
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'Server is running'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)