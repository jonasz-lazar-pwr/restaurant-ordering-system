// views.dsl

views {
    // --- Widok Kontekstu Systemu (Poziom 1) ---
    systemContext system "SystemContext" "Diagram kontekstowy (Poziom 1) pokazujący interakcje Systemu Zamówień w Restauracji z użytkownikami i systemami zewnętrznymi." {
        // Include all top-level elements (people, software systems)
        include *
        description "Diagram Kontekstowy C4 - Poziom 1"
    }

    // --- Widok Kontenerów (Poziom 2) ---
    container system "Containers" "Diagram kontenerów (Poziom 2) pokazujący główne bloki budujące System Zamówień w Restauracji." {
        // Include everything by default for a container view (people, external systems, internal containers)
        include *
        description "Diagram Kontenerów C4 - Poziom 2"
    }

    // --- Widok Komponentów dla Auth Service (Poziom 3) ---
    component system.auth "AuthComponents" "Diagram komponentów (Poziom 3) dla Usługi Autoryzacyjnej (Auth Service)." {
        // Include all components within auth service, plus connected elements (gateway, db_auth)
        include *
        description "Diagram Komponentów C4 - Poziom 3 (Auth Service)"
    }

    // Dołączanie stylów
    !include styles.dsl
}