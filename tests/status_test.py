import os, base64, requests
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Step 1: Request token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}

token_resp = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
print("Token status:", token_resp.status_code)
print("Token body:", token_resp.text)
token_resp.raise_for_status()
token = token_resp.json().get("access_token")
print("✅ Token acquired")

# Step 2: Test project + model access
headers = {"Authorization": f"Bearer {token}"}
url = "https://api.forio.com/v2/run/mitcams/cyberriskmanagement-ransomware-2023;model=main"
resp = requests.post(url, headers=headers, json={"prevention_budget": 50})
print("Run status:", resp.status_code)
print("Run body:", resp.text)
