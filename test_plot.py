from tools import plot_function

print("=" * 50)
print("测试: 绘制 y = x^2")
print("=" * 50)

result = plot_function("x^2", -5, 5)

print(f"结果: {result}")

if not result.startswith("错误") and not result.startswith("绘图失败"):
    print(f"图片已保存到: {result}")
    import os
    size = os.path.getsize(result)
    print(f"文件大小: {size} 字节")
else:
    print("绘图失败")