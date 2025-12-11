import requests

api_key = "sk-766a4f6bcad948189f3078ada7cffdea"

response = requests.post(
    "https://api.deepseek.com/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "你好，请回复'API连接成功'"}
        ]
    }
)

if response.status_code == 200:
    print("✅ API连接成功！")
    print("回复：", response.json()["choices"][0]["message"]["content"])
else:
    print("❌ API连接失败")
    print("错误码：", response.status_code)
    print("错误信息：", response.text)