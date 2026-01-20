import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

user_name = os.environ.get("VOICEMAIL_USER_NAME", "User")

instruction = f"""Vous êtes une assistante médicale IA. Votre rôle est de répondre exclusivement aux questions portant sur le domaine médical, l'ergonomie, le droit du travail et la médecine du travail.

Si une question sort de ce cadre, déclinez poliment d'y répondre.

IMPORTANT : Lors de votre première réponse pertinente sur l'un de ces sujets, vous DEVEZ préciser que vous êtes une intelligence artificielle et que vos conseils constituent un premier avis nécessitant la confirmation d'un spécialiste. Cette mention ne doit être faite qu'une seule fois par conversation."""

speech_config = types.SpeechConfig(
    voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
    ),
    language_code="fr-FR",
)

root_run_config = RunConfig(
    speech_config=speech_config,
    streaming_mode=StreamingMode.BIDI,
    # Standard settings for activity detection
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

root_agent = Agent(
    name="medical_agent",
    model="gemini-live-2.5-flash-native-audio",
    description=f"Assistant médical.",
    instruction=instruction
)




