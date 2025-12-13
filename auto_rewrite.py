"""
微信公众号文章自动洗稿工具
作者：你的名字
日期：2024-01-15
功能：批量处理markdown文章，使用AI重写为学校公告格式
优化：移除冗余配置、按价值分类保存、优化文件名。
     **临时移除**：原文链接提取与追加功能（因原始数据缺失）。
"""
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import re # 引入正则表达式库

# ==============================
# 配置区域 - 只需要修改这里！
# ==============================

# 1. 文件夹配置（根据你的实际情况修改）
INPUT_FOLDER = "input"        # 原始文章存放的文件夹
OUTPUT_FOLDER = "output"      # 洗稿后文章存放的主文件夹
PROCESSED_FOLDER = "processed"  # 已处理原文章的备份文件夹

# 2. AI服务配置（选择一种）
# 选项C：智谱AI (已沿用您文件中的配置)
AI_SERVICE = "glm"
API_KEY = "1fd53371653e4bb299bc011153a96e78.e3TfYj82Njx2rhmm"
MODEL_ID = "glm-4"

# 3. 新增子文件夹配置
VALUABLE_FOLDER = Path(OUTPUT_FOLDER) / "valuable"
VALUELESS_FOLDER = Path(OUTPUT_FOLDER) / "valueless"

# ==============================
# 主程序开始
# ==============================

def setup_folders():
    """创建必要的文件夹"""
    # 确保主输出文件夹和分类子文件夹存在
    Path(OUTPUT_FOLDER).mkdir(exist_ok=True)
    VALUABLE_FOLDER.mkdir(exist_ok=True)
    VALUELESS_FOLDER.mkdir(exist_ok=True)

    folders = [INPUT_FOLDER, PROCESSED_FOLDER, "logs"]
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
    print("✅ 文件夹结构创建完成")

def load_instructions():
    """加载洗稿指令 (仅加载文件内容)"""
    try:
        with open("instructions.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ 无法加载 instructions.txt 文件：{e}")
        return None

def get_ai_endpoint(service):
    """获取不同AI服务的API地址"""
    endpoints = {
        "doubao": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "deepseek": "https://api.deepseek.com/chat/completions",
        "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "qwen": "https://dashscope.aliyun.com/api/v1/services/aigc/text-generation/generation"
    }
    return endpoints.get(service, endpoints["glm"])

def read_markdown_file(filepath):
    """
    读取markdown文件，自动检测编码。
    返回: content
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
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
            {"role": "system", "content": prompt}, # 将整个 instructions.txt 作为系统指令
            {"role": "user", "content": "请根据以上规则，处理并改写以下公众号文章：\n\n" + content[:8000]} # 限制长度
        ],
        "temperature": 0.3, # 降低温度，确保AI严格遵循指令
        "max_tokens": 2000
    }
    
    for attempt in range(retry_count):
        try:
            print(f"  正在请求AI服务（尝试 {attempt+1}/{retry_count}）...")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=60 # 延长超时时间
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    ai_content = result["choices"][0]["message"]["content"]
                    print(f"  ✅ AI处理成功")
                    return ai_content
            
            print(f"  ⚠️ API返回错误：{response.status_code}. 详细信息: {response.text}")
            
        except requests.exceptions.Timeout:
            print(f"  ⏰ 请求超时")
        except Exception as e:
            print(f"  ❌ 网络错误：{str(e)}")
        
        if attempt < retry_count - 1:
            wait_time = (attempt + 1) * 5 # 更长的指数退避
            print(f"  等待{wait_time}秒后重试...")
            time.sleep(wait_time)
    
    return None

def sanitize_filename(text):
    """清理字符串，使其适合作为文件名"""
    text = re.sub(r'[\\/:*?"<>|]+', '_', text) # 替换非法字符
    text = text.strip()
    return text[:100] # 限制长度

def save_result(original_filename, ai_content):
    """
    保存洗稿后的结果，并根据内容分类保存到不同文件夹，使用新的命名格式。
    """
    
    # 1. 判断文章价值和提取标题
    # 根据 AI 输出是否以 【无价值】 开头来判断
    is_valuable = not ai_content.strip().startswith("【无价值】")
    
    if is_valuable:
        # 有价值文章：提取洗稿后的标题（通常是第一行）
        try:
            # 找到第一个非空行作为标题
            title_line = [line.strip() for line in ai_content.split('\n') if line.strip()][0]
            # 移除模板前缀，如【服务通知】
            match = re.search(r"【.*?】\s*(.*)", title_line)
            if match:
                title = match.group(1).strip()
            else:
                title = title_line
            # 使用清理后的标题
            new_title = sanitize_filename(title)
            target_folder = VALUABLE_FOLDER
        except Exception:
            new_title = sanitize_filename(f"有价值文章_{datetime.now().strftime('%H%M%S')}")
            target_folder = VALUABLE_FOLDER
            
    else:
        # 无价值文章：从输出中提取原标题
        # 匹配格式：【无价值】 原因标签：[文章原标题]
        match = re.search(r"【无价值】.*?：\s*(.*)", ai_content)
        if match:
            original_title = match.group(1).strip()
            new_title = "无价值_" + sanitize_filename(original_title)
        else:
            new_title = sanitize_filename(f"无价值文章_{datetime.now().strftime('%H%M%S')}")
        target_folder = VALUELESS_FOLDER

    # 2. 提取日期信息
    # 洗稿日期
    rewrite_date = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    # 3. 构造新文件名
    # 格式: [文章标题]_[洗稿日期].md
    new_filename = f"{new_title}_{rewrite_date}.md"
    output_path = target_folder / new_filename
    
    # 4. 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ai_content.strip() + "\n")
    
    return output_path, new_filename, target_folder.name

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
    print(f"📂 有价值输出位置：{VALUABLE_FOLDER.absolute()}")
    print(f"📂 无价值输出位置：{VALUELESS_FOLDER.absolute()}")
    print("="*50)
    
    if success > 0:
        print("\n🎉 恭喜！洗稿任务已完成！")
        print(f"请查看 '{OUTPUT_FOLDER}' 文件夹获取分类结果。")
    
    if failed > 0:
        print("\n⚠️  注意：部分文件处理失败")
        print("失败的文件仍在 'input' 文件夹中，请检查后重新运行。")

def main():
    """主函数"""
    print("="*50)
    print("🏫 微信公众号文章自动洗稿工具 (稳定版)")
    print("="*50)
    
    # 1. 初始化
    setup_folders()
    
    # 2. 加载洗稿指令
    rewrite_prompt = load_instructions()
    if not rewrite_prompt:
        return
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
        
        # 读取文件，现在只返回 content
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
            # 保存结果，现在不传递链接
            output_path, new_name, category = save_result(filename, ai_content)
            print(f"  💾 已保存至 {category} 文件夹为：{new_name}")
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