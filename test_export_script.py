import requests
import os

def test_export():
    url = "http://localhost:8000/exportar"
    params = {
        "limite": 5,
        "solo_curp": "true"
    }
    print(f"Calling {url} with params {params}...")
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            filename = response.headers.get("content-disposition", "").split("filename=")[-1]
            print(f"Success! Filename: {filename}")
            with open("test_solo_curp.xlsx", "wb") as f:
                f.write(response.content)
            print("File saved as test_solo_curp.xlsx")
            
            import pandas as pd
            df = pd.read_excel("test_solo_curp.xlsx")
            print("Excel content columns:", df.columns.tolist())
            print("Excel content (first 5 rows):")
            print(df.head())
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_export()
