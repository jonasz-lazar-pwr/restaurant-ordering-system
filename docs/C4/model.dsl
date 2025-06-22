// model.dsl

model {
    group "Restauracja XYZ" {
        client = person "Klient" "Osoba składająca zamówienie w restauracji." "Person"
        staff = person "Personel Restauracji" "Kucharz/Kelner zarządzający zamówieniami." "Person"

        orderingSystem = softwareSystem "System Zamówień w Restauracji" "Główny system do obsługi zamówień." "SoftwareSystemInternal" {

            apiGateway = container "API Gateway" "Pojedynczy punkt wejścia do systemu." "Kong" "Gateway"

            authService = container "Auth Service" "Serwis do zarządzania użytkownikami i uwierzytelnianiem." "Python/FastAPI" "Microservice" {
                authApi = component "Auth Router" "Obsługuje żądania API dla /auth, /register itd." "FastAPI Router" "Component"
                authUserManager = component "User Manager" "Logika biznesowa do zarządzania użytkownikami." "FastAPI-Users Logic" "Component"
                authDbAdapter = component "User DB Adapter" "Abstrakcja dostępu do bazy danych użytkowników." "FastAPI-Users SQLAlchemy" "Component"
                authJwtStrategy = component "JWT Strategy" "Tworzy i waliduje tokeny JWT." "FastAPI-Users JWT" "Component"

                authApi -> authUserManager "Deleguje logikę uwierzytelniania"
                authUserManager -> authDbAdapter "Zarządza encjami użytkowników"
                authUserManager -> authJwtStrategy "Tworzy tokeny JWT"
            }

            orderService = container "Order Service" "Serwis do tworzenia i zarządzania zamówieniami przez klienta." "Python/FastAPI" "Microservice" {
                orderApi = component "Order Controller" "Obsługuje przychodzące żądania HTTP API." "FastAPI Router" "Component"
                orderRepository = component "Order Repository" "Zarządza logiką dostępu do danych zamówień." "SQLAlchemy" "Component"
                orderProducer = component "RabbitMQ Producer" "Publikuje zdarzenia dotyczące zamówień." "aio-pika" "Component"
                orderConsumer = component "RabbitMQ Consumer" "Nasłuchuje na zdarzenia dotyczące zmian statusu." "aio-pika" "Component"

                orderApi -> orderRepository "Używa do operacji na bazie danych"
                orderApi -> orderProducer "Wysyła wiadomość po utworzeniu zamówienia"
                orderConsumer -> orderRepository "Aktualizuje status zamówienia w bazie danych"
            }

            paymentService = container "Payment Service" "Serwis do obsługi płatności przez PayU." "Python/FastAPI" "Microservice" {
                paymentApi = component "PayU Webhook Controller" "Odbiera powiadomienia o statusie płatności." "FastAPI Router" "Component"
                paymentPayuClient = component "PayU Client" "Klient do komunikacji z zewnętrznym API PayU." "HTTP Client" "Component"
                paymentConsumer = component "RabbitMQ Consumer" "Nasłuchuje na zdarzenia utworzenia zamówienia." "aio-pika" "Component"
                paymentProducer = component "RabbitMQ Producer" "Publikuje zdarzenia o statusie płatności." "aio-pika" "Component"

                paymentConsumer -> paymentPayuClient "Inicjuje płatność"
                paymentApi -> paymentProducer "Deleguje publikację zdarzenia"
            }

            staffService = container "Staff Service" "Serwis do zarządzania zamówieniami przez personel." "Python/FastAPI" "Microservice" {
                staffApi = component "Staff Order Controller" "Obsługuje żądania API personelu." "FastAPI Router" "Component"
                staffRepository = component "Order Repository" "Zarządza logiką dostępu do danych zamówień." "SQLAlchemy" "Component"
                staffPermissions = component "Permission Validator" "Sprawdza uprawnienia personelu." "Custom Logic" "Component"
                staffProducer = component "RabbitMQ Producer" "Publikuje zdarzenia po zmianie statusu." "aio-pika" "Component"
                staffConsumer = component "RabbitMQ Consumer" "Nasłuchuje na zdarzenia." "aio-pika" "Component"

                staffApi -> staffPermissions "Sprawdza uprawnienia"
                staffApi -> staffRepository "Pobiera/Aktualizuje dane zamówień"
                staffApi -> staffProducer "Wysyła zdarzenie o zmianie statusu"
                staffConsumer -> staffRepository "Aktualizuje lokalną kopię danych"
            }

            notificationService = container "Notification Service" "Serwis do wysyłania powiadomień." "Python/FastAPI" "Microservice" {
                notificationConsumer = component "RabbitMQ Consumer" "Odbiera wszystkie zdarzenia." "aio-pika" "Component"
                notificationSnsClient = component "SNS Client" "Klient do wysyłania powiadomień przez AWS SNS." "boto3" "Component"
                notificationRepository = component "Notification Repository" "Zapisuje historię wysłanych powiadomień." "SQLAlchemy" "Component"

                notificationConsumer -> notificationSnsClient "Deleguje wysyłkę powiadomienia"
                notificationConsumer -> notificationRepository "Zapisuje log wysyłki"
            }

            messageBus = container "Broker Wiadomości" "Asynchroniczna komunikacja." "RabbitMQ" "MessageBus"
            database = container "Baza Danych" "Przechowuje dane w odizolowanych schematach." "PostgreSQL" "Database"

            apiGateway -> authService "Przekierowuje żądania uwierzytelniania" "HTTPS"
            apiGateway -> orderService "Przekierowuje żądania dot. zamówień" "HTTPS"
            apiGateway -> staffService "Przekierowuje żądania personelu" "HTTPS"

            authService -> database "Czyta/Zapisuje dane użytkowników" "JDBC"
            orderService -> database "Czyta/Zapisuje dane zamówień" "JDBC"
            staffService -> database "Czyta/Zapisuje dane zamówień" "JDBC"
            notificationService -> database "Zapisuje logi powiadomień" "JDBC"

            orderService -> messageBus "Publikuje 'order_created'" "AMQP"
            paymentService -> messageBus "Publikuje 'payment_status_changed'" "AMQP"
            staffService -> messageBus "Publikuje 'staff_status_changed'" "AMQP"

            messageBus -> paymentService "Dostarcza 'order_created'" "AMQP"
            messageBus -> orderService "Dostarcza zdarzenia o zmianie statusu" "AMQP"
            messageBus -> staffService "Dostarcza zdarzenia o zmianie statusu" "AMQP"
            messageBus -> notificationService "Dostarcza wszystkie zdarzenia" "AMQP"
        }
    }

    clientDevice = softwareSystem "Przeglądarka / Aplikacja" "Interfejs użytkownika." "SoftwareSystemExternal"
    paymentGateway = softwareSystem "PayU" "Zewnętrzny system do przetwarzania płatności." "SoftwareSystemExternal"
    notificationGateway = softwareSystem "AWS SNS" "Zewnętrzna usługa do wysyłania powiadomień." "SoftwareSystemExternal"

    client -> clientDevice "Używa"
    staff -> clientDevice "Używa"
    clientDevice -> orderingSystem "Wysyła żądania API" "HTTPS/JSON"
    orderingSystem -> paymentGateway "Przetwarza płatności" "HTTPS/JSON"
    paymentGateway -> orderingSystem "Odbiera powiadomienia" "Webhook"
    orderingSystem -> notificationGateway "Wysyła powiadomienia" "HTTPS/JSON"
    notificationGateway -> client "Dostarcza powiadomienie" "SMS"
}