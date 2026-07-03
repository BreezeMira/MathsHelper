import os
from dotenv import load_dotenv
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl, wlexpr

load_dotenv()

# 从 .env 读取 Mathematica 内核路径
kernel_path = os.getenv("MATHEMATICA_KERNEL_PATH")

if not kernel_path:
    print("错误：请在 .env 中设置 MATHEMATICA_KERNEL_PATH")
    exit(1)

print(f"使用内核路径：{kernel_path}")

session = WolframLanguageSession(kernel_path)

print("正在连接 Mathematica 引擎...")

# 测试1：简单计算
result1 = session.evaluate(wl.Sin(wl.Pi))
print(f"sin(π) = {result1}")

# 测试2：解方程
result2 = session.evaluate(wlexpr("Solve[x^2 - 4 == 0, x]"))
print(f"Solve[x^2 - 4 == 0, x] = {result2}")

# 关闭会话
session.terminate()
print("测试完成")