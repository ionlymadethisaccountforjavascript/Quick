from pydub import AudioSegment
import soundfile as sf

filetype = "mp3"
filename = "sample.mp3"

if filetype == "mp3":
    audio = AudioSegment.from_file(filename, format="mp3")
    data, samplerate = sf.read(filename)
elif filetype == "wav":
    audio = AudioSegment.from_wav(filename)
    data, samplerate = sf.read(filename)
else:
    print("Invalid file type")
    exit()
    
audio.export("output.mp3", format="mp3")
audio.export("output.wav", format="wav")

print(data)
print(samplerate)