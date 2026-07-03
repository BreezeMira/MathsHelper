import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

#从.env读取wolfram.exe的文件路径
WOLFRAM_EXE_PATH = os.getenv("WOLFRAM_EXE_PATH")
def test_connection() -> str:
    """测试 wolfram.exe 是否可用"""
    if not WOLFRAM_EXE_PATH:
        return "错误：未配置 WOLFRAM_EXE_PATH, 请你在.env文件中写入 WOLFRAM_EXE_PATH=你的wolfram.exe的绝对路径"
    
    try:
        # 执行 Print[2+2]; 然后退出
        result = subprocess.run(
            [WOLFRAM_EXE_PATH, "-noprompt", "-run", "Print[2+2]; Exit[]"],
            #"-noprompt"用来让wolfram.exe不要有多余输出，Exit[]是必要的，否则不退出这个会导致整个程序卡在这里
            #wolfram对"-batch"不能正确处理，它不会退出命令行，甚至没有结果,所以用"-run"
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return f"wolfram.exe 连接成功! 2+2 = {result.stdout.strip()}"
        else:
            return f"连接失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "错误：执行超(30秒)"
    except Exception as e:
        return f"错误：{str(e)}"
    

def solve_math(code: str) -> str:
    """
    执行 Wolfram 语言代码并返回结果

    Args:
        code: Wolfram 语言代码，如 "Solve[x^2 - 4 == 0, x]"
    
    Returns:
        str: 计算结果
    """

    if not WOLFRAM_EXE_PATH:
        return "错误：未配置 WOLFRAM_EXE_PATH, 请你在.env文件中写入 WOLFRAM_EXE_PATH=你的wolfram.exe的绝对路径"
    
    try:
        # 用 Print 包裹代码，确保输出
        full_code = f"Print[{code}]; Exit[]"
        
        result = subprocess.run(
            [WOLFRAM_EXE_PATH, "-noprompt", "-run", full_code],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"计算失败：{result.stderr}"
    except subprocess.TimeoutExpired:
        return "错误: 计算超时60秒"
    except Exception as e:
        return f"错误：{str(e)}"