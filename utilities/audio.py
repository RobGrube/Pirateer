import os
import sys
sys.path.append(r'C:\code\ffmpeg\bin')
import pydub
from pathlib import Path
from pydub import AudioSegment
pydub.AudioSegment.ffmpeg = r"C:/code/ffmpeg/bin/ffmpeg.exe"
pydub.AudioSegment.ffprobe = r"C:/code/ffmpeg/bin/ffprobe.exe"


BASE_PATH = Path(__file__).resolve().parent.parent
for f in os.listdir(f'{BASE_PATH}/sounds'):
    print(f)
    base, ext = os.path.splitext(f)
    if ext.lower() == '.m4a':
        m4a_file = f'{BASE_PATH}/sounds/{f}'
        wav_filename = f'{BASE_PATH}/sounds/{base}.wav'
        print(os.path.exists(m4a_file))
        track = AudioSegment.from_file(m4a_file, format='m4a')
        file_handle = track.export(wav_filename, format='wav')
