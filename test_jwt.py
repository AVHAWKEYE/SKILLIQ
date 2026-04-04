import jwt
key = "mysecret"
token = jwt.encode({"sub": 1}, key, algorithm="HS256")
print(type(token), token)
try:
    print(jwt.decode(token, key, algorithms=["HS256"]))
except Exception as e:
    print("Error:", e)
