import json
import os
import time
from pathlib import Path

import jwt
import requests


KEY_ID = os.environ.get("ASC_KEY_ID", "WDXGY9WX55")
ISSUER_ID = os.environ.get("ASC_ISSUER_ID", "2be0734f-943a-4d61-9dc9-5d9045c46fec")
P8_PATH = Path(os.environ.get("ASC_P8_PATH", r"C:\tmp\asc_key.p8"))

BUNDLE_ID = os.environ.get("APP_BUNDLE_ID", "com.tokyonasu.HeatCheck")
APP_NAME = os.environ.get("APP_NAME", "発熱スマホお知らせ")
DEV_BUNDLE_NAME = os.environ.get("DEV_BUNDLE_NAME", "HeatCheck")
APP_SKU = os.environ.get("APP_SKU", "HeatCheck2026")
APP_VERSION = os.environ.get("APP_VERSION", "1.0")


private_key = P8_PATH.read_text(encoding="utf-8")


def token():
    now = int(time.time())
    payload = {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": KEY_ID})


def request(method, path, **kwargs):
    for _ in range(6):
        response = requests.request(
            method,
            f"https://api.appstoreconnect.apple.com/v1{path}",
            headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
            timeout=90,
            **kwargs,
        )
        if response.status_code not in (401, 429, 500, 502, 503, 504):
            return response
        time.sleep(10)
    return response


def json_request(method, path, **kwargs):
    response = request(method, path, **kwargs)
    try:
        body = response.json()
    except Exception:
        body = {}
    return response, body


def must(response, body, action):
    if response.status_code not in (200, 201):
        raise RuntimeError(f"{action} failed: {response.status_code} {response.text[:600]}")
    return body


def find_or_create_bundle_id():
    response, body = json_request("GET", f"/bundleIds?filter[identifier]={BUNDLE_ID}&limit=1")
    must(response, body, "Bundle ID lookup")
    if body.get("data"):
        return body["data"][0]["id"]

    payload = {
        "data": {
            "type": "bundleIds",
            "attributes": {
                "identifier": BUNDLE_ID,
                "name": DEV_BUNDLE_NAME,
                "platform": "IOS",
            },
        }
    }
    response, body = json_request("POST", "/bundleIds", json=payload)
    return must(response, body, "Bundle ID create")["data"]["id"]


def find_or_create_app():
    response, body = json_request("GET", f"/apps?filter[bundleId]={BUNDLE_ID}&limit=1")
    must(response, body, "App lookup")
    if body.get("data"):
        return body["data"][0]["id"]

    payload = {
        "data": {
            "type": "apps",
            "attributes": {
                "bundleId": BUNDLE_ID,
                "name": APP_NAME,
                "primaryLocale": "ja",
                "sku": APP_SKU,
            },
        }
    }
    response, body = json_request("POST", "/apps", json=payload)
    return must(response, body, "App create")["data"]["id"]


def find_or_create_version(app_id):
    response, body = json_request("GET", f"/apps/{app_id}/appStoreVersions?filter[platform]=IOS&limit=200")
    must(response, body, "Version lookup")
    for version in body.get("data", []):
        if version.get("attributes", {}).get("versionString") == APP_VERSION:
            return version["id"]

    payload = {
        "data": {
            "type": "appStoreVersions",
            "attributes": {"platform": "IOS", "versionString": APP_VERSION},
            "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
        }
    }
    response, body = json_request("POST", "/appStoreVersions", json=payload)
    return must(response, body, "Version create")["data"]["id"]


def main():
    bundle_resource_id = find_or_create_bundle_id()
    app_id = find_or_create_app()
    version_id = find_or_create_version(app_id)
    result = {
        "bundleResourceId": bundle_resource_id,
        "appId": app_id,
        "versionId": version_id,
        "bundleId": BUNDLE_ID,
        "name": APP_NAME,
        "sku": APP_SKU,
        "version": APP_VERSION,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
