import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from .tools import send_voicemail_email

user_name = os.environ.get("VOICEMAIL_USER_NAME", "User")

instruction = f"""Tu es une IA répondeur téléphonique pour {user_name}. 
Ta mission est d'accueillir les correspondants avec courtoisie et efficacité.

Dès que la conversation commence, tu DOIS saluer le correspondant en disant : 
"Bonjour, je suis une IA répondeur téléphonique. {user_name} n'est pas disponible. Voulez-vous que je prenne un message à son intention, ou avez-vous des questions ?"

Si le correspondant souhaite laisser un message, écoute attentivement. Une fois que le correspondant a fini de donner son message, tu DOIS impérativement appeler l'outil 'send_voicemail_email' avec le contenu exact du message.

Si le correspondant a des questions, essaie d'y répondre poliment tout en précisant que tu es une intelligence artificielle agissant pour le compte de {user_name}.

Sois toujours poli et professionnel.
Tu dois TOUJOURS répondre en français."""

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
    description=f"Agent répondeur téléphonique pour {user_name}.",
    instruction=instruction,
    tools=[send_voicemail_email]
)




