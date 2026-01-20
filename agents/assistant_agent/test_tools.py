import os
import unittest
from unittest.mock import patch, MagicMock
from agents.assistant_agent.tools import send_voicemail_email, update_voicemail_data
from google.adk.tools import ToolContext

class TestVoicemailTools(unittest.TestCase):

    def test_update_voicemail_data(self):
        # Setup mock ToolContext
        mock_context = MagicMock(spec=ToolContext)
        mock_context.state = {}

        # 1. Update Name only
        result = update_voicemail_data(mock_context, name="Alice")
        self.assertIn("Alice", mock_context.state["caller_name"])
        self.assertNotIn("message", mock_context.state)
        self.assertIn("name", result)

        # 2. Update Message only
        result = update_voicemail_data(mock_context, message="Hello World")
        self.assertIn("Hello World", mock_context.state["message"])
        self.assertIn("message", result)
        
        # 3. Update Both
        mock_context.state = {} # Reset
        result = update_voicemail_data(mock_context, name="Bob", message="Hi")
        self.assertEqual(mock_context.state["caller_name"], "Bob")
        self.assertEqual(mock_context.state["message"], "Hi")
        self.assertIn("name", result)
        self.assertIn("message", result)

        # 4. No update
        result = update_voicemail_data(mock_context)
        self.assertEqual(result, "No data provided to update.")

    @patch('agents.assistant_agent.tools.boto3.client')
    # ... existing tests ...
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
        result = send_voicemail_email(
            correspondant_message="Ceci est un message de test.",
            correspondant_name="Jean Dupont",
            correspondant_email="jean@example.com",
            correspondant_phone="0123456789"
        )

        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message_id'], '12345')
        mock_ses.send_email.assert_called_once()
        
        args, kwargs = mock_ses.send_email.call_args
        self.assertEqual(kwargs['Source'], 'source@example.com')
        self.assertEqual(kwargs['Destination']['ToAddresses'], ['recipient@example.com'])
        self.assertIn("Jean Dupont", kwargs['Message']['Subject']['Data'])
        body = kwargs['Message']['Body']['Text']['Data']
        self.assertIn("Ceci est un message de test.", body)
        self.assertIn("Jean Dupont", body)
        # self.assertIn("jean@example.com", body)  # Removed from body
        # self.assertIn("0123456789", body)        # Removed from body

    @patch('agents.assistant_agent.tools.boto3.client')
    @patch.dict(os.environ, {
        "VOICEMAIL_RECIPIENT_EMAIL": "recipient@example.com",
        "AWS_SES_SOURCE_EMAIL": "source@example.com",
        "AWS_REGION": "us-east-1",
        "VOICEMAIL_USER_NAME": "TestUser"
    })
    def test_send_voicemail_email_defaults(self, mock_boto_client):
        # Setup mock
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        mock_ses.send_email.return_value = {'MessageId': '67890'}

        # Execute with only required argument
        result = send_voicemail_email(correspondant_message="Juste un message.")

        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message_id'], '67890')
        
        args, kwargs = mock_ses.send_email.call_args
        self.assertIn("Inconnu", kwargs['Message']['Subject']['Data'])
        body = kwargs['Message']['Body']['Text']['Data']
        self.assertIn("Juste un message.", body)
        self.assertIn("Inconnu", body)
        # Should not have None displayed
        self.assertNotIn("None", body)

    @patch('agents.assistant_agent.tools.boto3.client')
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
