import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

def _send_ses_email(subject: str, body_text: str, recipient: str, source: str, region: str) -> dict:
    """Helper function to send email via AWS SES."""
    charset = "UTF-8"
    client = boto3.client('ses', region_name=region)
    try:
        response = client.send_email(
            Destination={'ToAddresses': [recipient]},
            Message={
                'Body': {'Text': {'Charset': charset, 'Data': body_text}},
                'Subject': {'Charset': charset, 'Data': subject},
            },
            Source=source,
        )
        return {"status": "success", "message_id": response['MessageId']}
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return {"status": "error", "message": str(e.response['Error']['Message'])}

def send_questionnaire_summary(tool_context: ToolContext, nom_patient: str, summary: str, doctor_email: Optional[str] = None) -> dict:
    """
    Envoie par email la synthèse d'un questionnaire médical à un médecin.
    Cette fonction doit être appelée à la fin de l'entretien avec le patient.
    """
    message_id_hash = f"questionnaire|{nom_patient}|{summary[:50]}"
    sent_emails = tool_context.state.get("sent_emails", [])
    if message_id_hash in sent_emails:
        return {"status": "success", "message": "Synthèse déjà envoyée."}

    recipient = doctor_email or os.environ.get("VOICEMAIL_RECIPIENT_EMAIL")
    source = os.environ.get("AWS_SES_SOURCE_EMAIL")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not recipient or not source:
        return {"status": "error", "message": "Configuration email manquante."}

    subject = f"Synthèse Questionnaire Médical : {nom_patient}"
    body_text = (f"Voici la synthèse du questionnaire médical rempli par {nom_patient} :\r\n"
                 f"\r\n"
                 f"{summary}\r\n"
                 f"\r\n"
                 f"Ce document est une aide au diagnostic à valider lors de la consultation.")
    
    result = _send_ses_email(subject, body_text, recipient, source, region)
    if result["status"] == "success":
        sent_emails.append(message_id_hash)
        tool_context.state["sent_emails"] = sent_emails
    return result
