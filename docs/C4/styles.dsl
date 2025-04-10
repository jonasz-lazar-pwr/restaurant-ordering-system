// styles.dsl

styles {
    // Styl dla Użytkowników Zewnętrznych
    element "Person" {
        shape Person
        background #5191FA
        color #ffffff
    }
    // Styl dla Systemu Głównego i Zewnętrznych
    element "Software System" {
        background #8A2BE2
        color #ffffff
        shape Box
    }
    // Styl dla kontenerów aplikacyjnych
    element "Container" {
        background #9a28f8
        color #ffffff
        shape Box
    }
    // Styl dla kontenerów oznaczonych tagiem "Database"
    element "Database" {
        shape Cylinder
        background #4b0082
        color #ffffff
    }
    // Styl dla Komponentów
    element "Component" {
        background #B36AFB
        color #ffffff
        shape Component
    }
}