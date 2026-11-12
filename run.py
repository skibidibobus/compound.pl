"""
Compound — Główny Skrypt Startowy (run.py)
Uruchomienie jedną komendą: python3 run.py
"""

import os
import sys
import time
import webbrowser
import threading
from server import start_server, PORT
from fetcher import update_all_data

def main():
    print("""
    ┌───┐  
    │ ■ │   c o m p o u n d
    └───┘   rynki · sport · świat
    ──────────────────────────────────────────
    """)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "data.json")
    
    # Jeśli nie ma jeszcze data.json, wygeneruj pierwszy zrzut
    if not os.path.exists(data_file):
        print("[Inicjalizacja] Pierwsze uruchomienie: generowanie bazy danych...")
        try:
            update_all_data()
        except Exception as e:
            print(f"[Ostrzeżenie] Nie udało się pobrać danych początkowych: {e}")

    # Uruchomienie serwera w osobnym wątku
    server_thread = threading.Thread(target=start_server, kwargs={"port": PORT}, daemon=True)
    server_thread.start()
    
    # Krótkie opóźnienie na start gniazda sieciowego
    time.sleep(1)
    
    url = f"http://localhost:{PORT}"
    print(f"\n[Gotowe] Otwieranie przeglądarki: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
        
    print("\nSerwer działa. Możesz testować stronę w przeglądarce.")
    print("Naciśnij Ctrl+C w tym oknie, aby zakończyć.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZamykanie portalu Compound. Do widzenia!")
        sys.exit(0)

if __name__ == "__main__":
    main()
