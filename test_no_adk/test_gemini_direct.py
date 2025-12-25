
import asyncio
import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configuration
MODEL = "gemini-2.0-flash-exp"
AUDIO_FILE = "hi.pcm"
OUTPUT_FILE = "response.pcm"

async def main():
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"), http_options={"api_version": "v1alpha"})

    config = types.LiveConnectConfig(
        system_instruction=types.Content(parts=[types.Part(text="You are a helpful assistant. Please answer short and concise.")]),
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
            )
        ),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                prefix_padding_ms=150,
                silence_duration_ms=400,
            )
        )
    )

    print(f"Connecting to Gemini ({MODEL})...")
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("Connected!")
        
        # Initial Greeting
        await session.send(input="Hello", end_of_turn=True)

        async def receive_loop():
            with open(OUTPUT_FILE, "wb") as f:
                async for part in session.receive():
                    if part.server_content and part.server_content.model_turn:
                        for p in part.server_content.model_turn.parts:
                            if p.inline_data:
                                print(f"Received audio chunk: {len(p.inline_data.data)} bytes")
                                f.write(p.inline_data.data)
                            if p.text:
                                print(f"Received text: {p.text}")
                    
                    if part.server_content and part.server_content.turn_complete:
                        print("Turn complete")

        receive_task = asyncio.create_task(receive_loop())

        # Send Audio
        if os.path.exists(AUDIO_FILE):
             print(f"Sending {AUDIO_FILE}...")
             with open(AUDIO_FILE, "rb") as f:
                while chunk := f.read(1024): # streaming chunks
                    await session.send_realtime_input(media=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000"))
                    await asyncio.sleep(0.01) # Simulate real-time speed roughly
             print("Finished sending audio.")
        else:
            print(f"File {AUDIO_FILE} not found. Please generate it first.")
            return

        # Keep alive for a bit to receive response
        await asyncio.sleep(5) 
        print(f"Done. Response saved to {OUTPUT_FILE}")
        
        # Cancel receiver
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
