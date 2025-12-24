import os
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def send_voicemail_email(correspondant_message: str) -> dict:
    """
    Sends an email with the content of a voicemail message using AWS SES.
    """
    recipient = os.environ.get("VOICEMAIL_RECIPIENT_EMAIL")
    source = os.environ.get("AWS_SES_SOURCE_EMAIL")
    region = os.environ.get("AWS_REGION", "us-east-1")
    user_name = os.environ.get("VOICEMAIL_USER_NAME", "User")

    if not recipient or not source:
        logger.error("SES configuration missing: VOICEMAIL_RECIPIENT_EMAIL or AWS_SES_SOURCE_EMAIL")
        return {"status": "error", "message": "Email configuration missing."}

    subject = f"Nouveau message vocal pour {user_name}"
    body_text = (f"Vous avez reçu un nouveau message vocal pour {user_name}:\r\n"
                 f"\r\n"
                 f"{correspondant_message}\r\n"
                 f"\r\n"
                 f"Bonne journée!")
    
    charset = "UTF-8"
    client = boto3.client('ses', region_name=region)

    try:
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
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return {"status": "error", "message": str(e.response['Error']['Message'])}
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return {"status": "success", "message_id": response['MessageId']}
