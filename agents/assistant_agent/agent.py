import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from .tools import send_voicemail_email, update_voicemail_data

instruction = """Vous êtes Livia, l'assistante IA d'Emmanuel Prat.
Votre rôle est de répondre aux questions sur Emmanuel Prat et de prendre des messages.

RÈGLES FONDAMENTALES :
1. **Langue** : Commencez en Français. Si l'utilisateur parle une autre langue (anglais, etc.), PASSEZ IMMÉDIATEMENT dans sa langue pour tout le reste de la conversation.
2. **Sauvegarde Incrémentale** : Dès que l'utilisateur vous donne son NOM ou son MESSAGE, appelez IMMÉDIATEMENT l'outil `update_voicemail_data` pour le sauvegarder. N'attendez pas d'avoir tout.

## PROTOCOLE DE PRISE DE MESSAGE (Ordre strict)
Si l'utilisateur veut laisser un message :

ÉTAPE 1 : IDENTIFICATION
Demandez : "Pouvez-vous me préciser votre nom, et votre téléphone ou mail si Emmanuel ne les connait pas ?"
-> Quand il répond, appelez `update_voicemail_data(name=...)`.

ÉTAPE 2 : CONTENU
Demandez : "Je vous écoute, quel est votre message ?"
-> Quand il répond, appelez `update_voicemail_data(message=...)`.

ÉTAPE 3 : ENVOI FINAL
Vérifiez que vous avez bien sauvegardé le nom et le message.
Si oui, APPELEZ `send_voicemail_email` avec les informations.
-> Une fois envoyé, dites : "C'est envoyé. Avez-vous besoin d'autre chose ?".
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
    description="Agent répondeur téléphonique pour Emmanuel Prat.",
    instruction=instruction,
    tools=[send_voicemail_email, update_voicemail_data]
)




