import requests

def test_headers():
    url = "http://localhost:8000/exportar"
    params = {"limite": 10}
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_headers()
