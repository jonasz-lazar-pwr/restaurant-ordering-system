# main.tf (root)

module "sns" {
  source           = "./modules/sns"
  topic_name       = var.sns_topic_name           # Nazwa tematu SNS do wysyłania powiadomień
  subscriber_email = var.sns_notification_email   # Adres email subskrybenta powiadomień z tematu SNS
}
