import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from tools import solve_math, plot, set_timeout
import json
load_dotenv()

# 初始化 LLM 客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 读取 System Prompt
with open("system_prompt.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


def run_agent(user_input: str) -> str:
    # 1. 调用 LLM
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.1
    )
    
    llm_output = response.choices[0].message.content
    print(f"\n[LLM 输出]\n{llm_output}")
    
    # 2. 提取 JSON（假设 LLM 输出就在代码块中或纯文本中）
    #    尝试匹配 ```json ... ``` 或直接解析整个文本
    try:
        # 若 LLM 按要求输出纯 JSON，直接解析
        tasks = json.loads(llm_output)
    except json.JSONDecodeError:
        # 兼容性：尝试从 ```json 代码块中提取
        match = re.search(r'```json\s*(.*?)\s*```', llm_output, re.DOTALL)
        if not match:
            return "错误：无法解析 LLM 输出，请检查 system prompt。"
        try:
            tasks = json.loads(match.group(1))
        except json.JSONDecodeError:
            return "错误：LLM 输出的 JSON 格式不正确。"
    
    # 标准化为列表（支持单个任务或任务数组）
    if isinstance(tasks, dict):
        tasks = [tasks]
    
    results = []
    for task in tasks:
        task_type = task.get("type")
        if task_type == "solve":
            code = task.get("code", "")
            if not code:
                results.append("错误：solve 任务缺少 code")
                continue
            set_timeout(60)
            res = solve_math(code)
            results.append(f"计算结果：\n{res}")
        elif task_type == "plot":
            expr = task.get("expr", "")
            x_min = task.get("x_min", -10)
            x_max = task.get("x_max", 10)
            if not expr:
                results.append("错误：plot 任务缺少 expr")
                continue
            set_timeout(120)
            filepath = plot(expr, x_min, x_max)
            if filepath.startswith("错误") or filepath.startswith("绘图失败"):
                results.append(filepath)
            else:
                results.append(f"图片已生成：{filepath}")
        else:
            results.append(f"未知任务类型：{task_type}")
    
    return "\n\n".join(results)


if __name__ == "__main__":
    print("=" * 50)
    print("数学助手 Agent")
    print("=" * 50)
    print("输入数学问题，或输入 exit 退出")
    
    while True:
        user_input = input("\n请输入：")
        if user_input.lower() in ["exit", "quit"]:
            print("再见！")
            break
        
        result = run_agent(user_input)
        print(f"\n{result}")