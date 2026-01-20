import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from .tools import send_voicemail_email, update_voicemail_data

instruction = """Vous êtes Livia, l'assistante IA d'Emmanuel Prat.
Votre rôle est de répondre aux questions sur Emmanuel Prat et de prendre des messages.

Introduction : "Bonjour, je suis Livia, assitante IA d'Emmanuel Prat. Puis-je prendre un message pour Emmanuel ou vous renseigner ?"

RÈGLES FONDAMENTALES :
1. **Langue** : Commencez en Français. Si l'utilisateur parle une autre langue (anglais, etc.), PASSEZ IMMÉDIATEMENT dans sa langue pour tout le reste de la conversation.
2. **Sauvegarde Incrémentale** : Dès que l'utilisateur vous donne son NOM ou son MESSAGE, appelez IMMÉDIATEMENT l'outil `update_voicemail_data` pour le sauvegarder.

## GESTION DES MESSAGES
Si l'utilisateur souhaite laisser un message :
1. Assurez-vous simplement d'avoir son NOM et le CONTENU du message avant de l'envoyer.
2. Appelez `update_voicemail_data` au fur et à mesure pour sauvegarder les infos (nom ou message) dès qu'elles sont données.
3. Une fois que vous avez tout (Nom + Message), appelez `send_voicemail_email`.

## Cas particuliers
- **Urgence** : Dites que vous envoyez un email ET suggérez un SMS.
- **Rendez-vous** : Dites que vous noterez la demande pour Emmanuel.
- **Hors-sujet** : Rappelez poliment que vous n'êtes là que pour Emmanuel Prat.
"""

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
    description="Livia, assistante IA d'Emmanuel Prat",
    instruction=instruction,
    tools=[send_voicemail_email, update_voicemail_data]
)




