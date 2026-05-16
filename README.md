# HeatCheck

iPhone の内部温度をリアルタイム表示する iOS アプリ。女の子キャラが温度に応じて話します。

## 機能

- 🌡️ リアルタイム温度表示
- 👧 女の子キャラクターが温度に応じて話す
- 🎮 ユーザーアクション（扇風機、冷房など）
- 🧊 冷却のコツ表示
- 🔊 音声合成（日本語）

## 設定

- Bundle ID: `com.tokyonasu.HeatCheck`
- Team ID: `83VGKGSQUH`
- Minimum iOS: 15.0

## ビルド

Mac で Xcode を開いて Build & Run。

```bash
xcodebuild -scheme HeatCheck -configuration Release -archivePath build/HeatCheck.xcarchive archive
```
