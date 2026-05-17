import sys

sys.path.insert(0, "scripts")
import create_asc_app as asc


APP_INFO_LOC_ID = "969d44f2-5d18-4113-ad85-65ea79ae7495"
VERSION_ID = "535532a8-fe4d-48f4-aeb0-2578dc88269e"
VERSION_LOC_ID = "c7f8773f-224d-4fe7-bc80-257366fbfefd"
PRIVACY_URL = "https://github.com/snarfnet/HeatCheck/blob/main/PRIVACY.md"
SUPPORT_URL = "https://github.com/snarfnet/HeatCheck/issues"


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
                "subtitle": "スマホの熱さをやさしく通知",
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
                    "発熱スマホお知らせは、スマホの熱さの目安を見やすく確認できるアプリです。\n\n"
                    "温度の状態に合わせて女の子の表情と服装が変わり、今の状態をやさしく知らせます。"
                    "暑くなってきた時は、扇風機、冷房、低電力モードなどの冷却アクションもすぐ記録できます。\n\n"
                    "スマホが熱い気がする時、ゲームや動画のあとに状態を見たい時、充電中の発熱が気になる時に使えます。\n\n"
                    "※表示される温度は端末状態から推定した目安です。医療、修理、故障診断を目的としたものではありません。"
                ),
                "keywords": "スマホ温度,発熱,熱い,冷却,バッテリー,端末温度,温度計,スマートフォン,熱対策,節電",
                "promotionalText": "スマホの熱さを、女の子が表情と服装で知らせます。",
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
                "usesIdfa": True,
            },
        }
    },
)

print("ASC metadata updated")
