
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import pyaudio
import os
import sys
from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    sys.exit(1)

client = genai.Client(http_options={"api_version": "v1alpha"})
MODEL = "gemini-2.0-flash-exp"

# Audio config
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512

async def audio_loop():
    p = pyaudio.PyAudio()
    
    try:
        microphone = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        
        speaker = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=24000, 
            output=True,
        )

        print("Connecting to Gemini...")
        async with client.aio.live.connect(model=MODEL, config={"response_modalities": ["AUDIO"]}) as session:
             print("Connected! Start speaking.")
             
             async def send_audio():
                 while True:
                     try:
                         data = await asyncio.to_thread(microphone.read, CHUNK, exception_on_overflow=False)
                         await session.send_realtime_input(media=types.Blob(data=data, mime_type="audio/pcm"))
                     except asyncio.CancelledError:
                         break
                     except Exception as e:
                         print(f"Error sending audio: {e}")
                         break

             async def receive_audio():
                 while True:
                     try:
                         async for response in session.receive():
                             if response.server_content is None:
                                 continue
                             
                             model_turn = response.server_content.model_turn
                             if model_turn:
                                 for part in model_turn.parts:
                                     if part.inline_data:
                                         await asyncio.to_thread(speaker.write, part.inline_data.data)
                                         
                             if response.server_content.turn_complete:
                                 # Optional: logic for turn complete
                                 pass
                     except asyncio.CancelledError:
                        break
                     except Exception as e:
                        print(f"Error receiving audio: {e}")
                        break

             # Run concurrent tasks
             send_task = asyncio.create_task(send_audio())
             receive_task = asyncio.create_task(receive_audio())
             
             try:
                 await asyncio.gather(send_task, receive_task)
             except asyncio.CancelledError:
                 pass
             finally:
                 send_task.cancel()
                 receive_task.cancel()

    except Exception as e:
        print(f"Main loop error: {e}")
    finally:
        print("Closing streams...")
        try:
            if 'microphone' in locals():
                microphone.stop_stream()
                microphone.close()
            if 'speaker' in locals():
                speaker.stop_stream()
                speaker.close()
            p.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(audio_loop())
    except KeyboardInterrupt:
        print("\nExiting...")
