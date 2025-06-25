# variables.tf (root)

# === AWS region ===
variable "aws_region" {
  description = "The AWS region where all resources will be deployed."
  type        = string
}

# === SNS configuration ===
variable "sns_topic_name" {
  description = "Name for the SNS topic used for application notifications."
  type        = string
}

variable "sns_notification_email" {
  description = "The email address that will be subscribed to the SNS topic to receive notifications."
  type        = string
}
