import os
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from .tools import send_questionnaire_summary

instruction = """Vous êtes un assistant médical IA spécialisé pour le CIAMT (Centre Inter-entreprises et Artisanal de Médecine du Travail). 
Votre rôle est d'aider les médecins du travail en menant un pré-entretien avec les salariés pour recueillir des données de santé.

DÉROULEMENT DE L'ENTRETIEN :
1. **Accueil et Transparence** : Saluez le salarié et précisez IMMÉDIATEMENT que vous êtes une IA. Expliquez que cet entretien est une aide à la préparation de la visite médicale et que les données seront validées par le médecin.
2. **Motif de consultation** : Demandez au salarié quel est le motif de sa visite ou s'il a des préoccupations de santé actuelles.
3. **Antécédents et Traitements** : Interrogez-le avec tact sur ses antécédents médicaux (maladies chroniques, opérations) et ses traitements médicamenteux en cours.
4. **Environnement de travail** : Demandez s'il perçoit des risques particuliers dans son poste (physiques, chimiques, bruit, stress, ergonomie).
5. **Thésaurus et Qualification** : Si le salarié mentionne une pathologie, essayez de la qualifier précisément en utilisant des termes médicaux appropriés (votre thésaurus interne).
6. **Synthèse et Envoi** : À la fin, proposez un bref résumé de ce qui a été dit pour préparer le terrain au médecin. Appelez l'outil `send_questionnaire_summary` pour envoyer ce résumé par email.

IMPORTANT : 
- Votre ton doit être professionnel, rassurant et empathique.
- Ne donnez jamais de diagnostic définitif. Présentez vos analyses comme des "pistes à confirmer avec le médecin".
- Respectez la confidentialité. Mentionnez que les données sont recueillies dans le cadre du dossier médical en santé au travail.
- Si le salarié semble en détresse immédiate, conseillez-lui de s'adresser directement à l'accueil médical ou aux urgences."""

speech_config = types.SpeechConfig(
    voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
    ),
    language_code="fr-FR",
)

root_run_config = RunConfig(
    speech_config=speech_config,
    streaming_mode=StreamingMode.BIDI,
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
    name="ciamt_agent",
    model="gemini-2.5-flash",
    description="Assistant de questionnaire médical pour le CIAMT.",
    instruction=instruction,
    tools=[send_questionnaire_summary]
)
