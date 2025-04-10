// model.dsl

model {
    // Użytkownik systemu
    user = person "Użytkownik" "Przegląda menu, składa i opłaca zamówienia, obsługuje płatności, przyjmuje zamówienia i zarządza systemem"

    // Zewnętrzne systemy
    sms_gateway = softwareSystem "Usługa SMS" "Wysyła powiadomienia do klientów"
    email_gateway = softwareSystem "Usługa e-mail" "Wysyła rachunki elektroniczne do klientów"
    payment_gateway = softwareSystem "Bramka płatności online" "Obsługuje płatności BLIK, PayU, itp."

    // Główny system
    system = softwareSystem "System Zamówień w Restauracji" "Pozwala klientom zamawiać dania, a obsłudze je realizować" {

        // --- Kontenery Aplikacyjne ---
        gateway = container "API Gateway" "Routing żądań do mikroserwisów, uwierzytelnianie, autoryzacja" "Kong"

        // --- Kontener Auth Service z Komponentami (Poziom 3) ---
        auth = container "Auth Service" "Uwierzytelnianie, logowanie, role" "FastAPI" {
            // Komponenty wewnętrzne Auth Service - Na podstawie kodu FastAPI
            routers = component "FastAPI Users Routers" "Obsługuje żądania HTTP dla /auth/* i /users/* używając fastapi-users" "FastAPI Users" {
                tags "Component"
            }
            authBackend = component "Authentication Backend" "Koordynuje proces uwierzytelniania JWT" "FastAPI Users" {
                tags "Component"
            }
            jwtStrategy = component "Custom JWT Strategy" "Generuje i waliduje tokeny JWT z rolą użytkownika" "Python / python-jose" {
                tags "Component"
            }
            userManager = component "User Manager" "Zarządza logiką tworzenia, aktualizacji i pobierania użytkowników" "FastAPI Users / Python" {
                tags "Component"
            }
            dbAdapter = component "SQLAlchemy User DB Adapter" "Adapter mapujący operacje User Managera na zapytania SQLAlchemy" "FastAPI Users / SQLAlchemy" {
                tags "Component"
            }

            // Relacje wewnętrzne między komponentami Auth Service
            routers -> userManager "Używa do rejestracji, pobierania/zarządzania użytkownikami" "FastAPI dependency injection"
            routers -> authBackend "Używa do logowania, weryfikacji tokenów" "FastAPI dependency injection"
            authBackend -> jwtStrategy "Deleguje tworzenie/odczyt tokenu" "Python call"
            userManager -> dbAdapter "Deleguje operacje bazodanowe na użytkownikach" "Python call"

            // Relacja komponentu DB Adapter do kontenera bazy danych
            // dbAdapter -> db_auth "Wykonuje operacje CRUD na tabeli 'users'" "SQLAlchemy / TCP"
        }

        order = container "Order Service" "Zamówienia, sesje stolików, statusy" "FastAPI"
        kitchen = container "Kitchen Service" "Obsługa zamówień kuchennych" "FastAPI"
        payment = container "Payment Service" "Integracja z bramkami płatności" "FastAPI"
        sms = container "SMS Service" "Wysyłanie powiadomień SMS" "FastAPI"
        email = container "E-mail Service" "Wysyłanie rachunków i e-maili" "FastAPI"

        // --- Kontenery Bazodanowe ---
        db_auth = container "Auth DB" "Baza danych użytkowników i ról" "PostgreSQL" {
            tags "Database"
        }
        db_orders = container "Orders DB" "Baza danych zamówień" "PostgreSQL" {
            tags "Database"
        }
        db_kitchen = container "Kitchen DB" "Baza danych kuchni" "PostgreSQL" {
            tags "Database"
        }
        db_payment = container "Payment DB" "Logi płatności" "PostgreSQL" {
            tags "Database"
        }
        db_sms = container "SMS DB" "Logi wysłanych SMS-ów" "PostgreSQL" {
            tags "Database"
        }
        db_email = container "Email DB" "Logi wysłanych e-maili" "PostgreSQL" {
            tags "Database"
        }

        // --- Relacje MIĘDZY KONTENERAMI (dla widoku Poziomu 2) ---

        // Gateway -> Serwisy
        gateway -> auth "Rejestracja, logowanie, JWT"
        gateway -> order "Zarządzanie zamówieniami"
        gateway -> kitchen "Zamówienia kuchenne"
        gateway -> payment "Rozpoczyna płatność"

        // Serwis -> Serwis (Backend -> Backend)
        order -> sms "Informuje o przyjęciu zamówienia"
        kitchen -> sms "Informuje o gotowym daniu"
        payment -> sms "Potwierdza płatność"
        payment -> email "Wysyła rachunek po płatności"

        // Serwis -> Baza danych
        auth -> db_auth "Czyta/Zapisuje dane uwierzytelniające"
        order -> db_orders "Czyta/Zapisuje dane zamówień"
        kitchen -> db_kitchen "Czyta/Zapisuje statusy zamówień kuchennych"
        sms -> db_sms "Czyta/Zapisuje logi wysłanych SMS-ów"
        email -> db_email "Czyta/Zapisuje logi wysłanych e-maili"
        payment -> db_payment "Czyta/Zapisuje logi płatności"

        // --- Relacja KOMPONENT -> KONTENER DB (dla widoku Poziomu 3 - Auth Service) ---
        system.auth.dbAdapter -> system.db_auth "Wykonuje operacje CRUD na tabeli 'users'" "SQLAlchemy"

        // Serwis -> Zewnętrzne systemy
        sms -> sms_gateway "Wysyła dane do powiadomień"
        email -> email_gateway "Wysyła dane do rachunków"
        payment -> payment_gateway "Wysyła dane do płatności"
    }

    // --- Relacje przechodzące przez granicę systemu ---

    // Relacja dla widoku kontekstu (Poziom 1)
    user -> system "Używa systemu do składania zamówień, zarządzania, etc."

    // Relacja Użytkownik -> Gateway (dla widoku Poziomu 2)
    user -> system.gateway "Wysyła żądania API (REST)"

    // Relacja Gateway -> Komponent (dla widoku Poziomu 3 - Auth Service)
    system.gateway -> system.auth.routers "Przekazuje żądania HTTP do obsługi przez FastAPI Users"
}