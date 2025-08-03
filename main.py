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
import transformers
import tensorflow as tf

audio = AudioSegment.from_file('./test.mp3',format = 'mp3')
#pitch detection
def detect_pitch(audio_file, sample_rate=22050):
    """
    Detect pitch using CREPE
    """
    y, sr = librosa.load(audio_file, sr=sample_rate)
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
    return time, frequency, confidence, y, sr
print(detect_pitch(audio.export('output.mp3',format='mp3')))