#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

import jwt
import requests


KEY_ID = os.environ.get("ASC_KEY_ID", "WDXGY9WX55")
ISSUER_ID = os.environ.get("ASC_ISSUER_ID", "2be0734f-943a-4d61-9dc9-5d9045c46fec")
P8_PATH = Path(os.environ.get("ASC_P8_PATH", f"~/.appstoreconnect/private_keys/AuthKey_{KEY_ID}.p8")).expanduser()
APP_ID = os.environ.get("APP_ID", "6770140985")
APP_VERSION = os.environ.get("APP_VERSION", "1.0")
BUILD_NUMBER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BUILD_NUMBER")


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


def version_id():
    response = require(
        api("GET", f"/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&filter[versionString]={APP_VERSION}&limit=1"),
        "Find App Store version",
    )
    versions = response.get("data", [])
    if versions:
        version = versions[0]
        print(f"Version {APP_VERSION}: {version['id']} state={version.get('attributes', {}).get('appStoreState')}")
        return version["id"]

    response = require(
        api(
            "POST",
            "/appStoreVersions",
            {
                "data": {
                    "type": "appStoreVersions",
                    "attributes": {"platform": "IOS", "versionString": APP_VERSION, "releaseType": "AFTER_APPROVAL"},
                    "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}},
                }
            },
        ),
        "Create App Store version",
    )
    return response["data"]["id"]


def update_review_notes(store_version_id):
    notes = (
        "Guideline 5.1.2(i): On first launch, the app waits until it becomes active, then shows the "
        "App Tracking Transparency system permission request before Google Mobile Ads is started "
        "and before any ad banner is loaded. GADDelayAppMeasurementInit is set to true. If the user "
        "does not allow tracking, the app still works and ads use non-personalized requests."
    )
    response = api("GET", f"/appStoreVersions/{store_version_id}/appStoreReviewDetail")
    if response.status_code == 200 and response.json().get("data"):
        detail_id = response.json()["data"]["id"]
        require(
            api(
                "PATCH",
                f"/appStoreReviewDetails/{detail_id}",
                {"data": {"type": "appStoreReviewDetails", "id": detail_id, "attributes": {"notes": notes}}},
            ),
            "Update review notes",
        )


def wait_for_build():
    if not BUILD_NUMBER:
        return None
    print(f"Waiting for build {BUILD_NUMBER} to become VALID...")
    for attempt in range(120):
        response = require(
            api("GET", f"/builds?filter[app]={APP_ID}&filter[version]={BUILD_NUMBER}&filter[processingState]=VALID&limit=1"),
            "Find processed build",
        )
        builds = response.get("data", [])
        if builds:
            build_id = builds[0]["id"]
            print(f"Build ready: {build_id}")
            return build_id
        print(f"  attempt {attempt + 1}/120, waiting 30s...")
        time.sleep(30)
    raise RuntimeError(f"Build {BUILD_NUMBER} did not become VALID within 60 minutes")


def attach_build(store_version_id, build_id):
    if not build_id:
        return
    require(
        api(
            "PATCH",
            f"/appStoreVersions/{store_version_id}",
            {
                "data": {
                    "type": "appStoreVersions",
                    "id": store_version_id,
                    "attributes": {"usesIdfa": True},
                    "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
                }
            },
        ),
        "Attach build",
    )
    api(
        "PATCH",
        f"/builds/{build_id}",
        {"data": {"type": "builds", "id": build_id, "attributes": {"usesNonExemptEncryption": False}}},
    )


def cancel_blocking_submissions():
    canceled = False
    for state in ("UNRESOLVED_ISSUES", "READY_FOR_REVIEW", "WAITING_FOR_REVIEW"):
        response = api("GET", f"/apps/{APP_ID}/reviewSubmissions?filter[platform]=IOS&filter[state]={state}&limit=20")
        if response.status_code >= 400:
            continue
        for submission in response.json().get("data", []):
            submission_id = submission["id"]
            result = api(
                "PATCH",
                f"/reviewSubmissions/{submission_id}",
                {"data": {"type": "reviewSubmissions", "id": submission_id, "attributes": {"canceled": True}}},
            )
            print(f"Cancel reviewSubmission {submission_id} state={state}: {result.status_code}")
            canceled = True
    return canceled


def submit(store_version_id):
    submission_id = None
    for attempt in range(5):
        response = api(
            "POST",
            "/reviewSubmissions",
            {
                "data": {
                    "type": "reviewSubmissions",
                    "attributes": {"platform": "IOS"},
                    "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}},
                }
            },
        )
        if response.status_code == 201:
            submission_id = response.json()["data"]["id"]
            break
        print(f"Create reviewSubmission attempt {attempt + 1}/5 failed")
        time.sleep(15)
    if not submission_id:
        raise RuntimeError("Could not create review submission")

    require(
        api(
            "POST",
            "/reviewSubmissionItems",
            {
                "data": {
                    "type": "reviewSubmissionItems",
                    "relationships": {
                        "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": submission_id}},
                        "appStoreVersion": {"data": {"type": "appStoreVersions", "id": store_version_id}},
                    },
                }
            },
        ),
        "Create review submission item",
    )
    require(
        api(
            "PATCH",
            f"/reviewSubmissions/{submission_id}",
            {"data": {"type": "reviewSubmissions", "id": submission_id, "attributes": {"submitted": True}}},
        ),
        "Submit for review",
    )
    print("=== SUBMITTED FOR REVIEW ===")


store_version_id = version_id()
update_review_notes(store_version_id)
build_id = wait_for_build()
attach_build(store_version_id, build_id)
if cancel_blocking_submissions():
    time.sleep(30)
    attach_build(store_version_id, build_id)
submit(store_version_id)
