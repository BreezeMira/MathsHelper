import os
import subprocess
import uuid
from dotenv import load_dotenv

load_dotenv()

# 从 .env 读取 wolframscript.exe 的文件路径
WOLFRAMSCRIPT_PATH = os.getenv("WOLFRAMSCRIPT_PATH")


def test_connection() -> str:
    """测试 wolframscript.exe 是否可用"""
    if not WOLFRAMSCRIPT_PATH:
        return "错误: 未配置 WOLFRAMSCRIPT_PATH"
    
    try:
        result = subprocess.run(
            [WOLFRAMSCRIPT_PATH, "-code", "2+2"],  
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return f"wolframscript.exe 连接成功!2+2 = {result.stdout.strip()}"
        else:
            return f"连接失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "错误:执行超时(30秒)S"
    except Exception as e:
        return f"错误: {str(e)}"

def solve_math(code: str) -> str:
    """
    执行 Wolfram 语言代码并返回结果

    Args:
        code: Wolfram 语言代码, 如 "Solve[x^2 - 4 == 0, x]"
    
    Returns:
        str: 计算结果

    """
    if not WOLFRAMSCRIPT_PATH:
        return "错误: 未配置 WOLFRAMSCRIPT_PATH, 请你在 .env 文件中写入 WOLFRAMSCRIPT_PATH=你的 wolframscript.exe 的绝对路径"
    
    try:

        result = subprocess.run(
            [WOLFRAMSCRIPT_PATH, "-code", code],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"计算失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "错误: 计算超时(60秒)"
    except Exception as e:
        return f"错误: {str(e)}"


def plot_function(expr: str, x_min: float = -10, x_max: float = 10) -> str:
    """
    绘制函数图像, 保存为图片
    
    Args:
        expr: 函数表达式, 如 "x^2" 或 "Sin[x]"
        x_min: x轴最小值, 默认 -10
        x_max: x轴最大值, 默认 10
    
    Returns:
        str: 图片保存路径, 或错误信息
    """
    if not WOLFRAMSCRIPT_PATH:
        return "错误: 未配置 WOLFRAMSCRIPT_PATH"
    
    # 创建 images 文件夹
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 生成唯一文件名
    filename = f"plot_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(images_dir, filename)
    filepath_posix = filepath.replace("\\", "/")
    
    # 构建绘图命令
    wolfram_code = f'Export["{filepath_posix}", Plot[{expr}, {{x, {x_min}, {x_max}}}], "PNG"];'
    
    try:
        result = subprocess.run(
            [WOLFRAMSCRIPT_PATH, "-code", wolfram_code],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
        else:
            return f"绘图失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "错误: 绘图超时(120秒)"
    except Exception as e:
        return f"错误: {str(e)}"