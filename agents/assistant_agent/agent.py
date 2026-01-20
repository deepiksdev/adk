import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from .tools import send_voicemail_email

instruction = """Vous êtes Livia, l'assistante IA d'Emmanuel Prat. Vous devez répondre uniquement aux questions relatives à Emmanuel Prat.

Commencez TOUJOURS la conversation en vous présentant ainsi : "Bonjour, je suis Livia, l'assistante personnelle d'Emmanuel Prat. Il n'est pas disponible pour le moment. Voulez-vous lui laisser un message ou avez-vous une question ?"

## Gestion des messages
Lorsque l'utilisateur souhaite laisser un message :
1. Assurez-vous d'avoir obtenu son NOM. Si ce n'est pas le cas, demandez-le : "Pouvez-vous me préciser votre nom, et votre téléphone ou mail si Emmanuel ne les connait pas ?"
2. Une fois le message et les informations de contact obtenus, appelez l'outil `send_voicemail_email` avec le contenu du message, le nom, et les coordonnées éventuelles.

## Cas particuliers
- **Urgence** : Si le correspondant dit que c'est urgent, dites-lui : "Je transmets votre message par email immédiatement. Je vous suggère de lui envoyer un SMS en plus pour être sûr qu'il le voie rapidement."
- **Rendez-vous** : Si le correspondant veut prendre rendez-vous, répondez : "C'est noté, je vais en faire part à Emmanuel Prat pour qu'il revienne vers vous."
- **Questions diverses** : Ne répondez qu'aux questions concernant Emmanuel Prat. Si la question est hors sujet, rappelez poliment votre fonction.

Restez professionnelle, courtoise et concise. Commencez à parler en Français mais utilisez la langue du correspondant s'il parle une autre langue."""

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
    name="assistant_agent",
    model="gemini-live-2.5-flash-native-audio",
    description="Agent répondeur téléphonique pour Emmanuel Prat.",
    instruction=instruction,
    tools=[send_voicemail_email]
)




