import jwt
key = "mysecretkey_should_be_at_least_32_chars"
token = jwt.encode({"sub": "1"}, key, algorithm="HS256")
print(type(token), token)
try:
    print(jwt.decode(token, key, algorithms=["HS256"]))
except Exception as e:
    print("Error:", e)
