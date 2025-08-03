import soundfile as sf
from pydub import AudioSegment

def process_audio(input_path, output_path, filetype):
    try:
        if filetype == "mp3":
            audio = AudioSegment.from_file(input_path, format="mp3")
            data, samplerate = sf.read(input_path)
        elif filetype == "wav":
            audio = AudioSegment.from_wav(input_path)
            data, samplerate = sf.read(input_path)

        audio.export(output_path, format="mp3")
        
        return True
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False