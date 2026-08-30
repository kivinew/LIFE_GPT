import urllib.request, os, sys

url = "https://nirsoft.net/utils/nircmd.exe"
local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "nircmd.exe")
os.makedirs(os.path.dirname(local), exist_ok=True)

print(f"Downloading from {url} to {local}")
urllib.request.urlretrieve(url, local)
size = os.path.getsize(local)
print(f"Downloaded {size} bytes")
print("SUCCESS" if size > 100 else "FAILED - small file")