import requests

url = "http://127.0.0.1:8000/api/auth/login"
params = {"username": "admin_demo", "password": "Admin@123"}
response = requests.post(url, params=params)
print("Status Code:", response.status_code)
print("Response JSON:", response.text)
