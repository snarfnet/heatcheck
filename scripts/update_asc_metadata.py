import sys

sys.path.insert(0, "scripts")
import create_asc_app as asc


APP_INFO_LOC_ID = "969d44f2-5d18-4113-ad85-65ea79ae7495"
VERSION_ID = "535532a8-fe4d-48f4-aeb0-2578dc88269e"
VERSION_LOC_ID = "c7f8773f-224d-4fe7-bc80-257366fbfefd"
PRIVACY_URL = "https://github.com/snarfnet/HeatCheck/blob/main/PRIVACY.md"
SUPPORT_URL = "https://snarfnet.github.io/app-support/"


def request(method, path, payload):
    response, body = asc.json_request(method, path, json=payload)
    if response.status_code >= 300:
        raise RuntimeError(f"{method} {path} failed: {response.status_code} {response.text[:1000]}")
    return body


request(
    "PATCH",
    f"/appInfoLocalizations/{APP_INFO_LOC_ID}",
    {
        "data": {
            "type": "appInfoLocalizations",
            "id": APP_INFO_LOC_ID,
            "attributes": {
                "name": "発熱スマホお知らせ",
                "subtitle": "スマホの熱状態をやさしく表示",
                "privacyPolicyUrl": PRIVACY_URL,
            },
        }
    },
)

request(
    "PATCH",
    f"/appStoreVersionLocalizations/{VERSION_LOC_ID}",
    {
        "data": {
            "type": "appStoreVersionLocalizations",
            "id": VERSION_LOC_ID,
            "attributes": {
                "description": (
                    "発熱スマホお知らせは、iOSが提供する端末の熱状態を見やすく表示するアプリです。\n\n"
                    "状態に合わせて女の子の表情と服装が変わり、今の目安をやさしく知らせます。"
                    "熱を持っている時は、明るさを下げる、ケースを外す、充電や重いアプリを休ませるなどの対策を確認できます。\n\n"
                    "このアプリは端末内部の実測温度を表示しません。"
                    "iOSの熱状態をもとにした目安表示で、医療、修理、故障診断を目的としたものではありません。"
                ),
                "keywords": "スマホ熱状態,発熱,熱い,冷却,バッテリー,熱対策,節電,iOS熱状態,スマートフォン",
                "promotionalText": "iOSの熱状態の目安を、女の子が表情と服装で知らせます。",
                "supportUrl": SUPPORT_URL,
            },
        }
    },
)

request(
    "PATCH",
    f"/appStoreVersions/{VERSION_ID}",
    {
        "data": {
            "type": "appStoreVersions",
            "id": VERSION_ID,
            "attributes": {
                "copyright": "Copyright 2026 tokyonasu",
                "usesIdfa": False,
            },
        }
    },
)

print("ASC metadata updated")
