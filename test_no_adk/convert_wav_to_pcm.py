
import wave

with wave.open("hi.wav", "rb") as wav_file:
    params = wav_file.getparams()
    print(f"Params: {params}")
    frames = wav_file.readframes(wav_file.getnframes())
    with open("hi.pcm", "wb") as pcm_file:
        pcm_file.write(frames)
    print("Created hi.pcm")
