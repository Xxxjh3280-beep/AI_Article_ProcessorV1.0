"""
微信公众号文章自动洗稿工具
作者：你的名字
日期：2024-01-15
功能：批量处理markdown文章，使用AI重写为学校公告格式
"""
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ==============================
# 配置区域 - 只需要修改这里！
# ==============================

# 1. 文件夹配置（根据你的实际情况修改）
INPUT_FOLDER = "input"        # 原始文章存放的文件夹
OUTPUT_FOLDER = "output"      # 洗稿后文章存放的文件夹
PROCESSED_FOLDER = "processed"  # 已处理原文章的备份文件夹

# 2. AI服务配置（选择一种）
# 取消注释你要用的AI，并填入API密钥

# 选项A：字节豆包（推荐，免费额度多）
# AI_SERVICE = "doubao"
# API_KEY = "你的豆包API密钥"
# MODEL_ID = "ep-20250101000000-xxxxxx"  # 你的模型ID

# 选项B：DeepSeek
# AI_SERVICE = "deepseek"
# API_KEY = "sk-766a4f6bcad948189f3078ada7cffdea"
# MODEL_ID = "deepseek-chat"

# 选项C：智谱AI
AI_SERVICE = "glm"
API_KEY = "1fd53371653e4bb299bc011153a96e78.e3TfYj82Njx2rhmm"
MODEL_ID = "glm-4"

# 3. 洗稿风格配置
SCHOOL_NAME = "上海应用技术大学"  # 改成你的学校名
BULLETIN_STYLE = "正式、客观、简洁"
TARGET_WORD_COUNT = "200-400字"

# ==============================
# 主程序开始 - 不要修改下面的代码！
# ==============================

def setup_folders():
    """创建必要的文件夹"""
    folders = [INPUT_FOLDER, OUTPUT_FOLDER, PROCESSED_FOLDER, "logs"]
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
    print("✅ 文件夹结构创建完成")

def load_instructions():
    """加载洗稿指令"""
    try:
        with open("instructions.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        # 默认指令
        return f"""请将以下公众号文章改写成适合{SCHOOL_NAME}公告栏的正式通知：

改写要求：
1. 风格：{BULLETIN_STYLE}
2. 去掉所有营销、推广、广告内容
3. 去掉"关注公众号"、"阅读原文"等引流内容
4. 语言正式、客观、严谨
5. 保留核心信息，适当精简
6. 格式：使用Markdown格式，包含标题、段落、列表
7. 字数：{TARGET_WORD_COUNT}

请在开头添加：【{SCHOOL_NAME}公告栏】字样

改写后的文章："""

def get_ai_endpoint(service):
    """获取不同AI服务的API地址"""
    endpoints = {
        "doubao": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "deepseek": "https://api.deepseek.com/chat/completions",
        "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",  # 智谱API
        "qwen": "https://dashscope.aliyun.com/api/v1/services/aigc/text-generation/generation"
    }
    return endpoints.get(service, endpoints["glm"])  # 默认用智谱

def read_markdown_file(filepath):
    """读取markdown文件，自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
                # 简单验证是否读成功
                if len(content) > 10:
                    return content
        except:
            continue
    
    print(f"❌ 无法读取文件：{filepath}")
    return None

def call_ai_api(content, prompt, retry_count=3):
    """调用AI API进行洗稿"""
    endpoint = get_ai_endpoint(AI_SERVICE)
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 准备请求数据
    data = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "你是一个专业的学校公告编辑助手。"},
            {"role": "user", "content": prompt + "\n\n" + content[:4000]}  # 限制长度
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # 重试机制
    for attempt in range(retry_count):
        try:
            print(f"  正在请求AI服务（尝试 {attempt+1}/{retry_count}）...")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=45  # 45秒超时
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    ai_content = result["choices"][0]["message"]["content"]
                    print(f"  ✅ AI处理成功")
                    return ai_content
            
            print(f"  ⚠️ API返回错误：{response.status_code}")
            
        except requests.exceptions.Timeout:
            print(f"  ⏰ 请求超时")
        except Exception as e:
            print(f"  ❌ 网络错误：{str(e)}")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < retry_count - 1:
            wait_time = (attempt + 1) * 3  # 指数退避
            print(f"  等待{wait_time}秒后重试...")
            time.sleep(wait_time)
    
    return None

def save_result(original_filename, ai_content):
    """保存洗稿后的结果"""
    # 生成新文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"公告_{timestamp}_{original_filename}"
    output_path = os.path.join(OUTPUT_FOLDER, new_filename)
    
    # 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ai_content)
    
    return output_path, new_filename

def move_processed_file(filename):
    """移动已处理的原文件到processed文件夹"""
    original_path = os.path.join(INPUT_FOLDER, filename)
    processed_path = os.path.join(PROCESSED_FOLDER, filename)
    
    if os.path.exists(original_path):
        # 如果文件已存在，添加时间戳
        if os.path.exists(processed_path):
            timestamp = datetime.now().strftime("%H%M%S")
            name, ext = os.path.splitext(filename)
            processed_path = os.path.join(PROCESSED_FOLDER, f"{name}_{timestamp}{ext}")
        
        os.rename(original_path, processed_path)

def log_process(filename, status, message=""):
    """记录处理日志"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "status": status,
        "message": message
    }
    
    log_file = os.path.join("logs", f"process_{datetime.now().strftime('%Y%m%d')}.log")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def display_summary(total, success, failed):
    """显示处理摘要"""
    print("\n" + "="*50)
    print("📊 处理完成！")
    print("="*50)
    print(f"📁 总处理文件：{total} 个")
    print(f"✅ 成功洗稿：{success} 个")
    print(f"❌ 处理失败：{failed} 个")
    print(f"📂 输出位置：{os.path.abspath(OUTPUT_FOLDER)}")
    print("="*50)
    
    if success > 0:
        print("\n🎉 恭喜！洗稿任务已完成！")
        print(f"请查看 '{OUTPUT_FOLDER}' 文件夹获取结果。")
    
    if failed > 0:
        print("\n⚠️  注意：部分文件处理失败")
        print("失败的文件仍在 'input' 文件夹中，请检查后重新运行。")

def main():
    """主函数"""
    print("="*50)
    print("🏫 微信公众号文章自动洗稿工具")
    print("="*50)
    
    # 1. 初始化
    setup_folders()
    
    # 2. 加载洗稿指令
    rewrite_prompt = load_instructions()
    print(f"📝 加载洗稿指令：共{len(rewrite_prompt)}字")
    
    # 3. 检查API配置
    if API_KEY.startswith("你的") or API_KEY == "":
        print("❌ 错误：请先配置API密钥！")
        print("请打开 auto_rewrite.py 文件，修改 API_KEY 和 MODEL_ID")
        input("按回车键退出...")
        return
    
    # 4. 获取文件列表
    all_files = [f for f in os.listdir(INPUT_FOLDER) 
                 if f.lower().endswith(('.md', '.markdown', '.txt'))]
    
    if not all_files:
        print("❌ 错误：input 文件夹中没有找到文章文件！")
        print("请将爬取的文章文件放入 'input' 文件夹中")
        input("按回车键退出...")
        return
    
    print(f"📄 找到 {len(all_files)} 篇文章待处理")
    print("-"*50)
    
    # 5. 开始批量处理
    success_count = 0
    failed_count = 0
    
    for index, filename in enumerate(all_files, 1):
        print(f"\n[{index}/{len(all_files)}] 正在处理：{filename}")
        
        # 读取文件
        filepath = os.path.join(INPUT_FOLDER, filename)
        original_content = read_markdown_file(filepath)
        
        if not original_content:
            print(f"  ❌ 读取文件失败，跳过")
            failed_count += 1
            log_process(filename, "failed", "无法读取文件")
            continue
        
        print(f"  原文长度：{len(original_content)} 字符")
        
        # 调用AI洗稿
        ai_content = call_ai_api(original_content, rewrite_prompt)
        
        if ai_content:
            # 保存结果
            output_path, new_name = save_result(filename, ai_content)
            print(f"  💾 已保存为：{new_name}")
            print(f"  洗稿后长度：{len(ai_content)} 字符")
            
            # 移动原文件
            move_processed_file(filename)
            
            success_count += 1
            log_process(filename, "success", f"保存为 {new_name}")
        else:
            print(f"  ❌ AI处理失败，跳过此文件")
            failed_count += 1
            log_process(filename, "failed", "AI处理失败")
        
        # 避免API调用频率过高
        if index < len(all_files):
            wait_time = 2  # 等待2秒
            print(f"  等待 {wait_time} 秒处理下一篇文章...")
            time.sleep(wait_time)
    
    # 6. 显示结果
    display_summary(len(all_files), success_count, failed_count)
    
    # 7. 保持窗口打开
    if os.name == 'nt':  # Windows系统
        input("\n按回车键退出程序...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序运行出错：{str(e)}")
        input("按回车键退出...")