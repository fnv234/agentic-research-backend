import os, base64, requests
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# request token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}

resp = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
print("Status:", resp.status_code)
print("Response:", resp.text)
resp.raise_for_status()
token = resp.json().get("access_token")
print("Token acquired:", token)

# test project + model access
headers = {"Authorization": f"Bearer {token}"}
url = "https://api.forio.com/v2/run/mitcams/cyberriskmanagement-ransomware-2023;model=main"
resp = requests.post(url, headers=headers, json={"prevention_budget": 50})
print("Status:", resp.status_code)
print("Body:", resp.text)
