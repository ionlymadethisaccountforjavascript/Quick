# AutoTune Pro - Setup Guide

This guide will help you set up the full-stack AutoTune Pro application with React frontend and Python Flask backend.

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.7 or higher)
- npm or yarn

## Backend Setup (Python Flask)

1. **Create a new directory for the backend:**
   ```bash
   mkdir autotune-backend
   cd autotune-backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the Flask server file:**
   - Save the Flask backend code as `app.py` in the `autotune-backend` directory

5. **Install additional system dependencies:**
   - For pydub to work with MP3 files, you may need to install FFmpeg:
   ```bash
   # On Windows (using chocolatey):
   choco install ffmpeg
   
   # On macOS (using homebrew):
   brew install ffmpeg
   
   # On Ubuntu/Debian:
   sudo apt update
   sudo apt install ffmpeg
   ```

6. **Run the Flask server:**
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`

## Frontend Setup (React)

1. **Navigate to your React project directory:**
   ```bash
   cd path/to/your/react-project
   ```

2. **Install additional dependencies if needed:**
   ```bash
   npm install @react-three/fiber three
   ```

3. **Replace your homepage.js file:**
   - Replace the content of `src/homepage.js` with the updated code

4. **Start the React development server:**
   ```bash
   npm start
   ```
   The frontend will be available at `http://localhost:3000`

## Project Structure

```
autotune-project/
├── autotune-backend/
│   ├── venv/
│   ├── uploads/          # Uploaded files
│   ├── processed/        # Processed files
│   ├── app.py           # Flask server
│   └── requirements.txt
└── react-frontend/      # Your existing React app
    ├── src/
    │   ├── homepage.js  # Updated component
    │   ├── App.js
    │   ├── Silk.js
    │   └── ShinyText.js
    └── package.json
```

## How It Works

1. **File Upload:** User uploads an MP3 or WAV file through the React interface
2. **API Call:** React sends the file to the Flask backend via POST request
3. **Processing:** Flask saves the file and runs your Python audio processing logic
4. **Response:** Backend returns a processed file ID and metadata
5. **Download:** User can download the processed file through another API endpoint

## Adding Your Autotune Logic

To add your actual autotune processing logic, modify the `process_audio` function in `app.py`:

```python
def process_audio(input_path, output_path, filetype):
    """
    Add your autotune processing logic here
    """
    try:
        if filetype == "mp3":
            audio = AudioSegment.from_file(input_path, format="mp3")
            data, samplerate = sf.read(input_path)
        elif filetype == "wav":
            audio = AudioSegment.from_wav(input_path)
            data, samplerate = sf.read(input_path)
        
        # ADD YOUR AUTOTUNE LOGIC HERE
        # Example: Apply pitch correction algorithms
        # processed_data = your_autotune_function(data, samplerate)
        
        # Export the processed audio
        audio.export(output_path, format="mp3")
        
        return True
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False
```

## Troubleshooting

1. **CORS Issues:** Make sure Flask-CORS is installed and configured
2. **File Upload Errors:** Check file permissions in upload/processed directories
3. **FFmpeg Issues:** Ensure FFmpeg is properly installed for MP3 support
4. **Port Conflicts:** Make sure ports 3000 and 5000 are available

## Security Note

This is a development setup. For production:
- Add proper authentication
- Implement file size limits
- Add input validation
- Use environment variables for configuration
- Set up proper logging
- Implement cleanup for old files