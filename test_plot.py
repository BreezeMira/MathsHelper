from tools import plot_function, query_wolfram_with_plot

print("=" * 60)
print("测试：绘制 y = x^2 图像")
print("=" * 60)

result = plot_function("x^2", x_min=-10, x_max=10)
print(f"图片保存路径：{result}")

print("\n" + "=" * 60)
print("测试：组合查询（文本 + 图像）")
print("=" * 60)

full_result = query_wolfram_with_plot("Plot[x^2, {x, -10, 10}]", need_plot=True)
print(f"文本结果：{full_result['text']}")
print(f"图片路径：{full_result['image']}")