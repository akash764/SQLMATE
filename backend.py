import requests

url = "http://127.0.0.1:8000/query"
payload = {
    "prompt": "List all users",
    "connection": {
        "user": "YOUR_USER",
        "password": "YOUR_PASSWORD",
        "host": "YOUR_HOST",
        "port": "YOUR_PORT",
        "database": "YOUR_DATABASE"
    }
}

response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
