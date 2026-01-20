import os
import unittest
from unittest.mock import patch, MagicMock
from agents.medical_agent.tools import send_voicemail_email

class TestVoicemailTools(unittest.TestCase):

    @patch('agents.medical_agent.tools.boto3.client')
    @patch.dict(os.environ, {
        "VOICEMAIL_RECIPIENT_EMAIL": "recipient@example.com",
        "AWS_SES_SOURCE_EMAIL": "source@example.com",
        "AWS_REGION": "us-east-1",
        "VOICEMAIL_USER_NAME": "TestUser"
    })
    def test_send_voicemail_email_success(self, mock_boto_client):
        # Setup mock
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        mock_ses.send_email.return_value = {'MessageId': '12345'}

        # Execute
        result = send_voicemail_email("Ceci est un message de test.")

        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message_id'], '12345')
        mock_ses.send_email.assert_called_once()
        
        args, kwargs = mock_ses.send_email.call_args
        self.assertEqual(kwargs['Source'], 'source@example.com')
        self.assertEqual(kwargs['Destination']['ToAddresses'], ['recipient@example.com'])
        self.assertIn("TestUser", kwargs['Message']['Subject']['Data'])
        self.assertIn("Ceci est un message de test.", kwargs['Message']['Body']['Text']['Data'])

    @patch('agents.medical_agent.tools.boto3.client')
    @patch.dict(os.environ, {
        "VOICEMAIL_RECIPIENT_EMAIL": "recipient@example.com",
        "AWS_SES_SOURCE_EMAIL": "source@example.com"
    })
    def test_send_voicemail_email_failure(self, mock_boto_client):
        # Setup mock to raise an error
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        from botocore.exceptions import ClientError
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'SES Error'}}, 'SendEmail'
        )

        # Execute
        result = send_voicemail_email("Test message failure.")

        # Verify
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'SES Error')

    @patch.dict(os.environ, {}, clear=True)
    def test_send_voicemail_email_missing_config(self):
        # Execute
        result = send_voicemail_email("Test message missing config.")

        # Verify
        self.assertEqual(result['status'], 'error')
        self.assertIn("configuration missing", result['message'])

if __name__ == '__main__':
    unittest.main()
