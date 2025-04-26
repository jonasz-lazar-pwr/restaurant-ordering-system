import requests
import json

# Adres URL sandboxowego API PayU
sandbox_base_url = "https://secure.snd.payu.com/"
token_url = f"{sandbox_base_url}pl/standard/user/oauth/authorize"
payment_methods_url = f"{sandbox_base_url}api/v2_1/paymethods"
order_url = f"{sandbox_base_url}api/v2_1/orders"

# Informacje z panelu Sandbox PayU
client_id = "490096"
client_secret = "585ec418430275c1252a591b7ef07185"
merchant_pos_id = "490096"

access_token = None
order_id = None
redirect_uri = None


# Krok 1: Uzyskanie tokena dostępu
try:
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(token_url, data=auth_data)
    response.raise_for_status()  # Sprawdź, czy nie wystąpił błąd HTTP
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"Pomyślnie uzyskano token dostępu: {access_token}")
except requests.exceptions.RequestException as e:
    print(f"Błąd podczas uzyskiwania tokenu: {e}")
    if hasattr(response, 'status_code'):
        print(f"Kod statusu odpowiedzi: {response.status_code}")
    if hasattr(response, 'text'):
        print(f"Treść odpowiedzi:\n{response.text}")


# Krok 2: Uzyskanie informacji o wszystkich możliwych metodach płatności
if access_token:
    methods_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    
    try:
        response = requests.get(payment_methods_url, headers=methods_headers)
        response.raise_for_status()  # Sprawdź, czy nie wystąpił błąd HTTP
        methods_data = response.json()

        pay_by_links = methods_data.get("payByLinks", [])
        if pay_by_links:
            print("\nDostępne metody płatności (Pay By Link):")
            for method in pay_by_links:
                value = method.get("value")
                name = method.get("name")
                status_method = method.get("status")
                min_amount = method.get("minAmount")
                max_amount = method.get("maxAmount")
                brand_image_url = method.get("brandImageUrl")

                print("-" * 30)
                print(f"Nazwa: {name}")
                print(f"Wartość (ID): {value}")
                print(f"Status: {status_method}")
                if min_amount is not None:
                    print(f"Minimalna kwota: {min_amount / 100:.2f} PLN") # Kwoty są w groszach
                if max_amount is not None:
                    print(f"Maksymalna kwota: {max_amount / 100:.2f} PLN") # Kwoty są w groszach
                print(f"URL obrazu logo: {brand_image_url}")
            print("-" * 30)
        else:
            print("\nBrak dostępnych metod płatności Pay By Link.")

        card_tokens = methods_data.get("cardTokens", [])
        if card_tokens:
            print("\nZapisane karty płatnicze (Card Tokens):")
            print(json.dumps(card_tokens, indent=4)) # Wyświetlenie w formacie JSON
        else:
            print("\nBrak zapisanych kart płatniczych.")

        pex_tokens = methods_data.get("pexTokens", [])
        if pex_tokens:
            print("\nTokeny PEX:")
            print(json.dumps(pex_tokens, indent=4)) # Wyświetlenie w formacie JSON
        else:
            print("\nBrak tokenów PEX.")

        print()

    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas otrzymywania listy metod płatności: {e}")
        if hasattr(response, 'status_code'):
            print(f"Kod statusu odpowiedzi: {response.status_code}")
        if hasattr(response, 'text'):
            print(f"Treść odpowiedzi:\n{response.text}")


# Krok 3: Utworzenie zamówienia testowego (jeśli udało się uzyskać token)
if access_token:
    order_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    # Testowe dane zamówienia wzięte z dokumentacji PayU
    # Nie wszystkie obecne tu są obowiązkowe
    # Nie wszystkie opcjonalne są tu obecne
    # Ilość informacji do przesłania łatwo można modyfikować
    order_data = {
        "notifyUrl": "https://your.eshop.com/notify",  # Zmień na swój rzeczywisty URL
        "customerIp": "127.0.0.1",
        "merchantPosId": merchant_pos_id,  # Upewnij się, że to poprawny ID z sandboxa
        "description": "RTV market",
        "currencyCode": "PLN",
        "totalAmount": "21000",
        "buyer": {
            "email": "john.doe@example.com",
            "phone": "654111654",
            "firstName": "John",
            "lastName": "Doe",
            "language": "pl"
        },
        "products": [
            {
                "name": "Wireless Mouse for Laptop",
                "unitPrice": "15000",
                "quantity": "1"
            },
            {
                "name": "HDMI cable",
                "unitPrice": "6000",
                "quantity": "1"
            }
        ]
    }

    print(f"Sending order data: {order_data}")

    try:
        response = requests.post(order_url, headers=order_headers, json=order_data, allow_redirects=False)
        response.raise_for_status()
        order_response = response.json()
        order_id = order_response.get("orderId")
        redirect_uri = order_response.get("redirectUri")
        print(f"Pomyślnie utworzono zamówienie. ID zamówienia: {order_id}")
        print(f"Adres URL do przekierowania płatności ---> {redirect_uri}")

        # Tutaj może nastąpić przekierowanie

    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas tworzenia zamówienia: {e}")
        if hasattr(response, 'status_code'):
            print(f"Kod statusu odpowiedzi: {response.status_code}")
        if hasattr(response, 'text'):
            print(f"Odpowiedź serwera:\n{response.text}")


# Krok 4_1: Sprawdzenie statusu zamówienia (opcjonalnie)
if order_id and access_token:
    order_details_url = f"{sandbox_base_url}api/v2_1/orders/{order_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(order_details_url, headers=headers)
        response.raise_for_status()
        order_details = response.json()
        print(f"\nSzczegóły zamówienia {order_id}:")
        print(json.dumps(order_details, indent=4))
    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas pobierania szczegółów zamówienia: {e}")
        if hasattr(response, 'status_code'):
            print(f"Kod statusu odpowiedzi: {response.status_code}")
        if hasattr(response, 'text'):
            print(f"Odpowiedź serwera:\n{response.text}")


# # Krok 4_2: Anulowanie złożonego zamówienia (opcjonalnie)
# if order_id and access_token:
#     order_details_url = f"{sandbox_base_url}api/v2_1/orders/{order_id}"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
#     try:
#         response = requests.delete(order_details_url, headers=headers)
#         response.raise_for_status()
#         order_details = response.json()
#         print(f"\nAnulowanie zamówienia {order_id}:")
#         print(json.dumps(order_details, indent=4))
#     except requests.exceptions.RequestException as e:
#         print(f"Błąd podczas anulowania zamówienia: {e}")
#         if hasattr(response, 'status_code'):
#             print(f"Kod statusu odpowiedzi: {response.status_code}")
#         if hasattr(response, 'text'):
#             print(f"Odpowiedź serwera:\n{response.text}")


# refund_id = "NXXCRZFTFP250413GUEST000P01"

# # Krok 5: Stworzenie zwrotu wybranego zamówienia
# # Aktualnie w celach testów podaję ręcznie order_id poprzedniego zamówienia
# # Nie wpływa to na przyszłą implementację
# if refund_id and access_token:
#     order_refund_url = f"{sandbox_base_url}api/v2_1/orders/{refund_id}/refunds"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
#     refund_data = {
#         "refund": {
#             "description": "Test refund",
#             "currencyCode": "PLN"
#         }
#     }

#     try:
#         response = requests.post(order_refund_url, headers=headers, json=refund_data)
#         response.raise_for_status()
#         refund_details = response.json()
#         print(f"\nSzczegóły zwrotu {refund_id}:")
#         print(json.dumps(order_details, indent=4))
#     except requests.exceptions.RequestException as e:
#         print(f"Błąd podczas tworzenia zwrotu: {e}")
#         if hasattr(response, 'status_code'):
#             print(f"Kod statusu odpowiedzi: {response.status_code}")
#         if hasattr(response, 'text'):
#             print(f"Odpowiedź serwera:\n{response.text}")