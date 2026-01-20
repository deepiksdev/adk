import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

def update_voicemail_data(tool_context: ToolContext, name: Optional[str] = None, message: Optional[str] = None) -> str:
    """
    Saves the correspondent's name or message to the session state.
    Call this tool immediately when the user provides either piece of information.
    """
    saved_items = []
    if name:
        tool_context.state["caller_name"] = name
        saved_items.append("name")
    if message:
        tool_context.state["message"] = message
        saved_items.append("message")
    
    if not saved_items:
        return "No data provided to update."
        
    return f"Data saved successfully: {', '.join(saved_items)}."

def send_voicemail_email(correspondant_message: str, correspondant_name: str = "Inconnu", correspondant_email: str = None, correspondant_phone: str = None) -> dict:
    """
    Sends an email with the content of a voicemail message using AWS SES.
    """
    recipient = os.environ.get("VOICEMAIL_RECIPIENT_EMAIL")
    source = os.environ.get("AWS_SES_SOURCE_EMAIL")
    region = os.environ.get("AWS_REGION", "us-east-1")
    print("REGION",region)
    user_name = os.environ.get("VOICEMAIL_USER_NAME", "User")

    print(f"DEBUG: Starting send_voicemail_email with message: {correspondant_message}")
    if not recipient or not source:
        print(f"DEBUG: Missing config. Recipient: {recipient}, Source: {source}")
        logger.error("SES configuration missing: VOICEMAIL_RECIPIENT_EMAIL or AWS_SES_SOURCE_EMAIL")
        return {"status": "error", "message": "Email configuration missing."}

    print(f"DEBUG: Config loaded. Recipient: {recipient}, Source: {source}, Region: {region}")

    subject = f"Nouveau message vocal de {correspondant_name}"
    
    contact_info = ""
    if correspondant_email:
        contact_info += f"Email: {correspondant_email}\r\n"
    if correspondant_phone:
        contact_info += f"Tél: {correspondant_phone}\r\n"
        
    body_text = (f"Vous avez reçu un nouveau message vocal de la part de {correspondant_name}:\r\n"
                 f"\r\n"
                 f"{contact_info}"
                 f"\r\n"
                 f"Message:\r\n"
                 f"{correspondant_message}\r\n"
                 f"\r\n"
                 f"Bonne journée!")
    
    charset = "UTF-8"
    print("DEBUG: Creating boto3 client...")
    client = boto3.client('ses', region_name=region)
    print("DEBUG: Boto3 client created.",boto3)

    try:
        print("DEBUG: Sending email via SES...")
        response = client.send_email(
            Destination={
                'ToAddresses': [recipient],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': charset,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=source,
        )
        print(f"DEBUG: Email sent response: {response}")
    except ClientError as e:
        print(f"DEBUG: ClientError caught: {e}")
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return {"status": "error", "message": str(e.response['Error']['Message'])}
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return {"status": "success", "message_id": response['MessageId']}
