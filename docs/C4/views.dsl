// views.dsl

views {
    systemContext orderingSystem "SystemContext" "Diagram Kontekstu Systemu dla Systemu Zamawiania Jedzenia." {
        include *
        autolayout lr
    }

    container orderingSystem "Containers" "Diagram Kontenerów dla Systemu Zamawiania Jedzenia." {
        include *
        autolayout lr
    }

    component authService "AuthServiceComponents" "Diagram Komponentów dla Auth Service." {
        include *
        autolayout lr
    }

    component orderService "OrderServiceComponents" "Diagram Komponentów dla Order Service." {
        include *
        autolayout lr
    }

    component paymentService "PaymentServiceComponents" "Diagram Komponentów dla Payment Service." {
        include *
        autolayout lr
    }

    component staffService "StaffServiceComponents" "Diagram Komponentów dla Staff Service." {
        include *
        autolayout lr
    }

    component notificationService "NotificationServiceComponents" "Diagram Komponentów dla Notification Service." {
        include *
        autolayout lr
    }

    styles {
        element "Person" {
            shape Person
            background #08427b
            color #ffffff
        }
        element "SoftwareSystemInternal" {
            background #1168bd
            color #ffffff
        }
        element "SoftwareSystemExternal" {
            background #999999
            color #ffffff
        }
        element "Container" {
            background #438dd5
            color #ffffff
        }
        element "Gateway" {
            shape WebBrowser
        }
        element "Database" {
            shape Cylinder
            background #ff0000
        }
        element "MessageBus" {
            shape Pipe
            background #ff6600
        }
        element "Component" {
            background #85bbf0
            color #000000
        }
    }

    theme default
}