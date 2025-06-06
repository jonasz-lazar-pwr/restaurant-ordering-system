# === api/services/sns.py ===

"""
SNS service.

Provides a function to send notifications to the configured AWS SNS topic.
"""

import boto3
from botocore.client import BaseClient
from api.core.config import settings

# Instantiate the SNS client eagerly at module load time
sns_client: BaseClient = boto3.client(
    "sns",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    aws_session_token=settings.AWS_SESSION_TOKEN,
)


def send_notification_to_sns(recipient_email: str, message: str) -> dict:
    """
    Publishes a notification message to the SNS topic.

    Args:
        recipient_email (str): Email address of the notification recipient.
        message (str): Notification message body.

    Returns:
        dict: Response from AWS SNS publish operation.
    """
    return sns_client.publish(
        TopicArn=settings.AWS_SNS_TOPIC_ARN,
        Message=message,
        Subject=f"New notification for {recipient_email}"
    )
