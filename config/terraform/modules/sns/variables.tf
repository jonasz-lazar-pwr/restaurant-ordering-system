# sns/variables.tf

variable "topic_name" {
  description = "The name of the SNS topic to be created."
  type        = string
}

variable "subscriber_email" {
  description = "The email address to subscribe to the SNS topic for notifications."
  type        = string
}