# sns/main.tf

resource "aws_sns_topic" "this" {
  name         = var.topic_name                   # Nazwa tematu SNS (unikalna w ramach konta i regionu)
  display_name = "Restaurant Ordering System"     # Nazwa wyświetlana tematu (np. w powiadomieniach)
}

resource "aws_sns_topic_subscription" "email_subscriber" {
  topic_arn = aws_sns_topic.this.arn             # ARN tematu SNS, do którego subskrypcja jest dodawana
  protocol  = "email"                            # Protokół subskrypcji (email)
  endpoint  = var.subscriber_email               # Punkt końcowy subskrypcji (adres email odbiorcy)
}
