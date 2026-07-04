# test_plot.py
"""
测试绘图功能: 使用 run_wolfram 工具绘制一个多元函数的 3D 图像。
请确保 .env 文件中已正确设置 WOLFRAMSCRIPT_PATH。
"""

import os
import sys
from tools import ToolExecutor

def main():
    # 初始化工具执行器
    executor = ToolExecutor()
    
    # 要测试的绘图代码 (多元函数 3D 图)
    # 这里绘制 f(x, y) = sin(x) * cos(y) 的图像
    code = "Plot3D[Sin[x] * Cos[y], {x, -3, 3}, {y, -3, 3}]"
    
    print(f"执行绘图代码: {code}")
    print("输出类型: image")
    
    # 调用 run_wolfram 工具，output_type 设为 "image"
    result = executor._run_wolfram(code=code, output_type="image")
    
    # 检查结果
    if os.path.exists(result) and os.path.isfile(result):
        print(f"\n绘图成功! 图片已保存至: {result}")
        print("你可以用图片查看器打开该文件查看图像。")
        # 可选: 尝试自动打开图片 (仅 Windows/Mac/Linux 可能有效)
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(result)
            elif platform.system() == "Darwin":  # macOS
                os.system(f'open "{result}"')
            else:
                os.system(f'xdg-open "{result}"')
        except Exception:
            pass
    else:
        print(f"\n绘图失败或未生成文件。返回结果: {result}")

if __name__ == "__main__":
    main()