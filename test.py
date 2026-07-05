"""测试 run_wolfram 工具的四种输出模式"""
import os
from tools import ToolExecutor

# 创建共享实例(只注册一次)
executor = ToolExecutor()

def test_math_text():
    """测试数学文本计算"""
    result = executor._run_wolfram(
        code="Integrate[Sin[x], x]",
        output_type="math_text"
    )
    print(f"[数学文本] 积分结果: {result}\n")

def test_plot_image():
    """测试数学图像 (3D 曲面)"""
    result = executor._run_wolfram(
        code="Plot3D[Sin[x] * Cos[y], {x, -3, 3}, {y, -3, 3}]",
        output_type="plot_image"
    )
    print(f"[数学图像] 保存路径: {result}\n")

def test_wolfram_expression_image():
    """测试 Wolfram 表达式渲染为图片"""
    result = executor._run_wolfram(
        code="Integrate[E^(-x^2), {x, 0, Infinity}]",
        output_type="wolfram_expression_image"
    )
    print(f"[Wolfram表达式] 保存路径: {result}\n")


if __name__ == "__main__":
    test_math_text()
    test_plot_image()
    test_wolfram_expression_image()
    print("所有测试完成!")
    print("plots/       文件夹存放数学图像")
    print("expressions/ 文件夹存放表达式图片")