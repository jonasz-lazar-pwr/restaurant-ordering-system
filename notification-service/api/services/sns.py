import boto3
from botocore.exceptions import ClientError
from api.core.config import settings

sns_client = boto3.client(
    "sns",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)

def publish_notification(message: str, subject: str = "Notification"):
    try:
        response = sns_client.publish(
            TopicArn=settings.sns_topic_arn,
            Message=message,
            Subject=subject
        )
        return {"message_id": response["MessageId"]}
    except ClientError as e:
        return {"error": str(e)}
