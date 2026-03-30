import requests

def verify_search_status():
    url = "http://localhost:8000/buscar"
    params = {"limite": 10}
    print(f"Calling search {url}...")
    try:
        # Note: This assumes the server is running. 
        # Since I can't be sure, I will also test the logic by importing main.py functions if possible.
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            exported_count = sum(1 for r in data['resultados'] if r.get('_exportado'))
            print(f"Total results: {len(data['resultados'])}")
            print(f"Marked as exported: {exported_count}")
        else:
            print(f"Error calling API: {response.status_code}")
    except Exception as e:
        print(f"API not reachable (expected if not running): {e}")

if __name__ == "__main__":
    verify_search_status()
