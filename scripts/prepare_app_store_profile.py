#!/usr/bin/env python3
import base64
import os
import time
from pathlib import Path

import jwt
import requests


KEY_ID = os.environ.get("ASC_KEY_ID", "WDXGY9WX55")
ISSUER_ID = os.environ.get("ASC_ISSUER_ID", "2be0734f-943a-4d61-9dc9-5d9045c46fec")
P8_PATH = Path(os.environ.get("ASC_P8_PATH", f"~/.appstoreconnect/private_keys/AuthKey_{KEY_ID}.p8")).expanduser()
BUNDLE_ID = os.environ.get("APP_BUNDLE_ID", "com.tokyonasu.HeatCheck")
PROFILE_NAME = os.environ.get("PROFILE_NAME", "HeatCheck App Store")
REFRESH_PROFILE = os.environ.get("REFRESH_PROFILE", "").lower() in {"1", "true", "yes"}


def make_token():
    now = int(time.time())
    return jwt.encode(
        {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        P8_PATH.read_text(encoding="utf-8"),
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )


def api(method, path, payload=None):
    response = requests.request(
        method,
        f"https://api.appstoreconnect.apple.com/v1{path}",
        headers={"Authorization": f"Bearer {make_token()}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    print(method, path.split("?")[0][-70:], response.status_code, flush=True)
    if response.status_code >= 400:
        print(response.text[:1000], flush=True)
    return response


def require(response, action):
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"{action} failed: {response.status_code} {response.text[:1000]}")
    return response.json() if response.text else {}


def first_data(response, label):
    data = response.get("data")
    if not data:
        raise RuntimeError(f"No {label} found")
    return data[0] if isinstance(data, list) else data


bundle = first_data(require(api("GET", f"/bundleIds?filter[identifier]={BUNDLE_ID}&limit=1"), "Find bundle ID"), "bundle ID")

seen = set()
certs = []
for cert_type in ("IOS_DISTRIBUTION", "DISTRIBUTION"):
    for cert in require(api("GET", f"/certificates?filter[certificateType]={cert_type}&limit=200"), "List certificates").get("data", []):
        if cert["id"] not in seen:
            seen.add(cert["id"])
            certs.append(cert)
if not certs:
    raise RuntimeError("No distribution certificates found")

profiles = require(api("GET", f"/profiles?filter[name]={PROFILE_NAME}&limit=20"), "List profiles").get("data", [])
active_profiles = [profile for profile in profiles if profile.get("attributes", {}).get("profileState") == "ACTIVE"]

if REFRESH_PROFILE:
    for profile in profiles:
        require(api("DELETE", f"/profiles/{profile['id']}"), "Delete old profile")
    active_profiles = []

if active_profiles:
    profile = active_profiles[0]
else:
    profile = first_data(
        require(
            api(
                "POST",
                "/profiles",
                {
                    "data": {
                        "type": "profiles",
                        "attributes": {"name": PROFILE_NAME, "profileType": "IOS_APP_STORE"},
                        "relationships": {
                            "bundleId": {"data": {"type": "bundleIds", "id": bundle["id"]}},
                            "certificates": {"data": [{"type": "certificates", "id": cert["id"]} for cert in certs]},
                        },
                    }
                },
            ),
            "Create profile",
        ),
        "created profile",
    )

content = profile.get("attributes", {}).get("profileContent")
if not content:
    profile = first_data(require(api("GET", f"/profiles?filter[name]={PROFILE_NAME}&limit=1"), "Reload profile"), "profile")
    content = profile["attributes"]["profileContent"]

profiles_dir = Path.home() / "Library" / "MobileDevice" / "Provisioning Profiles"
profiles_dir.mkdir(parents=True, exist_ok=True)
out = profiles_dir / "HeatCheck_App_Store.mobileprovision"
out.write_bytes(base64.b64decode(content))
print(f"PROFILE_PATH={out}")
print(f"PROFILE_NAME={PROFILE_NAME}")
