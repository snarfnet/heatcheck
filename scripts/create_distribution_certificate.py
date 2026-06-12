#!/usr/bin/env python3
import base64
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import jwt
import requests


KEY_ID = os.environ.get("ASC_KEY_ID", "WDXGY9WX55")
ISSUER_ID = os.environ.get("ASC_ISSUER_ID", "2be0734f-943a-4d61-9dc9-5d9045c46fec")
P8_PATH = Path(os.environ.get("ASC_P8_PATH", f"~/.appstoreconnect/private_keys/AuthKey_{KEY_ID}.p8")).expanduser()
KEYCHAIN = os.environ.get("BUILD_KEYCHAIN", "build.keychain")
KEYCHAIN_PASSWORD = os.environ["KEYCHAIN_PASSWORD"]
WORK_DIR = Path("/tmp/heatcheck-signing")
KEY_PATH = WORK_DIR / "distribution.key"
CSR_PATH = WORK_DIR / "distribution.csr"
CERT_PATH = WORK_DIR / "distribution.cer"


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


def run(args):
    print("+", " ".join(str(arg) for arg in args), flush=True)
    subprocess.run(args, check=True)


def generate_csr():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    run(["openssl", "genrsa", "-out", str(KEY_PATH), "2048"])
    run([
        "openssl",
        "req",
        "-new",
        "-key",
        str(KEY_PATH),
        "-out",
        str(CSR_PATH),
        "-subj",
        "/CN=HeatCheck CI Distribution/O=TokyoNasu/C=JP",
    ])


def list_distribution_certs():
    seen = set()
    certs = []
    for cert_type in ("DISTRIBUTION", "IOS_DISTRIBUTION"):
        data = require(api("GET", f"/certificates?filter[certificateType]={cert_type}&limit=200"), "List certificates")
        for cert in data.get("data", []):
            if cert["id"] not in seen:
                seen.add(cert["id"])
                certs.append(cert)
    return certs


def parse_date(value):
    if not value:
        return datetime.max
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def delete_oldest_certificate():
    candidates = []
    for cert in list_distribution_certs():
        detail = require(api("GET", f"/certificates/{cert['id']}"), "Get certificate").get("data", cert)
        attrs = detail.get("attributes", {})
        candidates.append((parse_date(attrs.get("expirationDate")), cert["id"]))
    if not candidates:
        return False
    _, cert_id = sorted(candidates, key=lambda item: item[0])[0]
    require(api("DELETE", f"/certificates/{cert_id}"), "Delete oldest certificate")
    return True


def create_certificate_once(cert_type):
    return require(
        api(
            "POST",
            "/certificates",
            {
                "data": {
                    "type": "certificates",
                    "attributes": {"certificateType": cert_type, "csrContent": CSR_PATH.read_text()},
                }
            },
        ),
        f"Create {cert_type} certificate",
    )["data"]


def create_certificate():
    last_error = None
    for cert_type in ("DISTRIBUTION", "IOS_DISTRIBUTION"):
        try:
            return create_certificate_once(cert_type)
        except RuntimeError as error:
            last_error = error
    if last_error and any(word in str(last_error).lower() for word in ("maximum", "limit", "reached", "already have")):
        if delete_oldest_certificate():
            for cert_type in ("DISTRIBUTION", "IOS_DISTRIBUTION"):
                try:
                    return create_certificate_once(cert_type)
                except RuntimeError as error:
                    last_error = error
    raise last_error or RuntimeError("Certificate creation failed")


def import_certificate(cert):
    content = cert.get("attributes", {}).get("certificateContent")
    if not content:
        raise RuntimeError("Created certificate did not include certificateContent")
    CERT_PATH.write_bytes(base64.b64decode(content))
    run(["security", "import", str(KEY_PATH), "-k", KEYCHAIN, "-T", "/usr/bin/codesign", "-T", "/usr/bin/security"])
    run(["security", "import", str(CERT_PATH), "-k", KEYCHAIN, "-T", "/usr/bin/codesign", "-T", "/usr/bin/security"])
    run(["security", "set-key-partition-list", "-S", "apple-tool:,apple:", "-s", "-k", KEYCHAIN_PASSWORD, KEYCHAIN])
    print(f"ASC_CERTIFICATE_ID={cert['id']}")


generate_csr()
import_certificate(create_certificate())
