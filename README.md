# aivoice-http-api

本ソフトウェアを用いて立ち上げたAPIを、第三者が利用可能な形で公開しないでください。A.I.VOICE Editor APIの利用規約に抵触する可能性があります(作者は、Cloudflare Accessによるアクセス制御を行い、第三者が利用できないようにしています)。

## 起動

```bash
uv run fastapi run
```

## API呼び出し

```bash
# ボイスプリセット一覧
curl https://aivoice.eyrin.jp/presets \
  -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET"

# ボイスプリセット
curl https://aivoice.eyrin.jp/presets/%E7%B5%90%E6%9C%88%20%E3%82%86%E3%81%8B%E3%82%8A \
  -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET"

# 音声合成
curl https://aivoice.eyrin.jp/synthesize -o output.wav \
  -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "こんにちは",
    "preset": {
      "PresetName": "結月 ゆかり",
      "MergedVoiceContainer": {"BasePitchVoiceName": "", "MergedVoices": []},
      "Volume": 1.0, "Speed": 1.0, "Pitch": 1.0, "PitchRange": 1.0,
      "MiddlePause": 150, "LongPause": 370,
      "Styles": [{"Name": "J", "Value": 0.0}, {"Name": "A", "Value": 0.0}, {"Name": "S", "Value": 0.0}]
    },
    "sample_rate": 44100
  }'
```
