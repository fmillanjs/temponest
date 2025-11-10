import jwt
import sys

with open('/tmp/token.txt', 'r') as f:
    token = f.read().strip()

secret = "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING"

try:
    decoded = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_signature": True, "verify_exp": True})
    print("✅ Token verified successfully!")
    print(f"User: {decoded.get('email')}")
    print(f"Tenant: {decoded.get('tenant_id')}")
    print(f"Permissions: {len(decoded.get('permissions', []))} permissions")
except jwt.ExpiredSignatureError:
    print("❌ Token expired")
    sys.exit(1)
except jwt.InvalidTokenError as e:
    print(f"❌ Invalid token: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
