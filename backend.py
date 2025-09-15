import requests

url = "http://127.0.0.1:8000/query"
payload = {
    "prompt": "List all users",
    "connection": {
        "root": "root",
        "leena": "Akashdhoni11",
        "host": "127.0.0.1",
        "port": "3306",
        "test": "testdb"
    }
}

response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
