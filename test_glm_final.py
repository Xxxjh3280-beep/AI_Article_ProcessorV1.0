"""
智谱AI API连接测试
确保你的代码能正常工作
"""

import requests
import json
import time

print("=" * 50)
print("🧪 智谱GLM API 连接测试")
print("=" * 50)

# === 在这里填入你的API信息 ===
API_KEY = "1fd53371653e4bb299bc011153a96e78.e3TfYj82Njx2rhmm"  # 格式：abc123def456
MODEL_NAME = "glm-4"   # 或 glm-4

# 智谱API地址
url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 请求数据
data = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "system", 
            "content": "你是一个专业的学校公告编辑助手。请用正式、客观的语言回复。"
        },
        {
            "role": "user",
            "content": "你好！如果连接成功，请回复：『🎉 智谱AI连接成功！可以开始洗稿工作了。』"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 100
}

print(f"使用模型: {MODEL_NAME}")
print("正在发送请求到智谱AI...")

try:
    start_time = time.time()
    
    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=15  # 15秒超时
    )
    
    end_time = time.time()
    response_time = round(end_time - start_time, 2)
    
    print(f"响应时间: {response_time}秒")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        # 智谱的返回格式
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
            print("\n" + "✅" * 25)
            print("🎉 连接成功！AI回复：")
            print("-" * 40)
            print(reply)
            print("-" * 40)
            
            # 显示token使用情况
            if "usage" in result:
                usage = result["usage"]
                print(f"Token使用: 输入{usage.get('prompt_tokens', 0)} / 输出{usage.get('completion_tokens', 0)}")
                
        else:
            print("❌ 响应格式错误")
            print("完整响应：")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif response.status_code == 401:
        print("❌ 认证失败：API Key错误或已过期")
        print("请检查：")
        print("1. API Key是否正确")
        print("2. API Key是否已启用")
        print("3. 账户是否有余额")
        
    elif response.status_code == 429:
        print("❌ 请求频率过高，请稍后重试")
        
    elif response.status_code == 402:
        print("❌ 余额不足，请充值或领取免费额度")
        print("访问：https://open.bigmodel.cn/ 查看余额")
        
    else:
        print(f"❌ 连接失败，错误码：{response.status_code}")
        print("错误信息：")
        print(response.text)

except requests.exceptions.Timeout:
    print("❌ 请求超时，请检查网络连接")
    
except requests.exceptions.ConnectionError:
    print("❌ 网络连接错误，请检查网络")
    
except Exception as e:
    print(f"❌ 发生未知错误：{str(e)}")

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)
input("按回车键退出...")