import os
from datetime import datetime, timedelta
import jwt
from app.auth import create_access_token, decode_token, SECRET_KEY, ALGORITHM

token = create_access_token(1, "admin_demo", "admin")
print("Tokens generated:", token)
print("Secret key:", SECRET_KEY)

try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("Raw decode:", decoded)
except Exception as e:
    print("PyJWT Decode Exception:", type(e), e)

try:
    print("App decode:", decode_token(token))
except Exception as e:
    print("Exception from app decode:", type(e), e)
