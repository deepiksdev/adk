
import asyncio
import os
import pyaudio
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16000
RECEIVE_RATE = 24000
CHUNK_SIZE = 512

MODEL = "gemini-2.0-flash-exp"

async def main():
    p = pyaudio.PyAudio()

    try:
        # Open Input Stream (Mic)
        input_stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        logger.info(f"Microphone input opened: {SEND_RATE}Hz")

        # Open Output Stream (Speaker)
        output_stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )
        logger.info(f"Speaker output opened: {RECEIVE_RATE}Hz")

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"), http_options={"api_version": "v1alpha"})

        config = types.LiveConnectConfig(
            system_instruction=types.Content(parts=[types.Part(text="You are a helpful and concise voice assistant.")]),
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

        logger.info(f"Connecting to Gemini ({MODEL})...")
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            logger.info("Connected to Gemini! Start speaking...")

            async def send_audio_loop():
                try:
                    while True:
                        # Read from Mic
                        data = await asyncio.to_thread(input_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                        
                        # Send to Gemini
                        await session.send_realtime_input(media=types.Blob(data=data, mime_type=f"audio/pcm;rate={SEND_RATE}"))
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error in send_audio_loop: {e}")

            async def receive_audio_loop():
                try:
                    async for part in session.receive():
                        if part.server_content and part.server_content.model_turn:
                            for p in part.server_content.model_turn.parts:
                                if p.inline_data:
                                    # Write to Speaker
                                    await asyncio.to_thread(output_stream.write, p.inline_data.data)
                                    
                        if part.server_content and part.server_content.turn_complete:
                            # logger.info("Turn complete")
                            pass
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error in receive_audio_loop: {e}")

            # Run loops
            send_task = asyncio.create_task(send_audio_loop())
            receive_task = asyncio.create_task(receive_audio_loop())

            try:
                # Keep running until Ctrl+C
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping...")
            finally:
                send_task.cancel()
                receive_task.cancel()
                await asyncio.gather(send_task, receive_task, return_exceptions=True)

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # cleanup
        if 'input_stream' in locals():
            input_stream.stop_stream()
            input_stream.close()
        if 'output_stream' in locals():
            output_stream.stop_stream()
            output_stream.close()
        p.terminate()
        logger.info("Audio streams closed.")

if __name__ == "__main__":
    asyncio.run(main())
