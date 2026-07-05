import os
import subprocess
import uuid
import json
from typing import Dict, Any, Callable, List, Optional
from dotenv import load_dotenv

load_dotenv()

# 从 .env 读取 wolframscript.exe 的文件路径
WOLFRAMSCRIPT_PATH = os.getenv("WOLFRAMSCRIPT_PATH")
wolfram_timeout = 30


class ToolExecutor:
    """
    一个工具执行器, 负责管理和执行工具
    支持注册, 执行和生成 OpenAI 格式的工具定义
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        # 自动注册默认工具
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认的数学及系统工具"""
        self.register_tool(
            name="run_wolfram",
            description=("执行 Wolfram 语言代码, 支持三种输出模式"
                         "'math_text': 返回纯文本计算结果"
                         "'plot_image': 绘制数学图像(如函数曲线, 3D曲面等), 保存至 plots/ 文件夹"
                         "'wolfram_expression_image': 将 Wolfram 表达式渲染为图片, 保存至 expressions/ 文件夹。wolfram_expression_image 模式不会先执行再渲染, 而是直接把输入的代码当作符号表达式画出来。所以传入 Reduce[]或Solve[]等 时, 它画的是求解命令本身, 而非解的公式。而传入纯数学表达式时, 就能正确渲染。所以应该把之前得到的长表达式结果原封不动地传进去"),
            func=self._run_wolfram,
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": ("待执行的代码. math_text 模式: 任意 Wolfram 代码"
                                        "plot_image 模式: 绘图代码(如 Plot, Plot3D)"
                                        "wolfram_expression_image 模式: Wolfram 表达式(如 Integrate[...], Sum[...])")
                    },
                    "output_type": {
                        "type": "string",
                        "enum": ["math_text", "plot_image", "wolfram_expression_image"],
                        "description": ("输出模式: 'math_text' 返回文本结果"
                                        "'plot_image' 生成数学图片"
                                        "'wolfram_expression_image' 将 Wolfram 表达式渲染为图片")
                    }
                },
                "required": ["code", "output_type"]
            }
        )
        
        self.register_tool(
            name="test_connection",
            description="测试wolframscript连接是否正常",
            func=self._test_connection,
            parameters={
                "type": "object",
                "properties": {}
            }
        )
        
        self.register_tool(
            name="set_timeout",
            description="设置wolframscript执行的超时时限(秒)",
            func=self._set_timeout,
            parameters={
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "integer",
                        "description": "超时时限(秒), 必须大于0"
                    }
                },
                "required": ["seconds"]
            }
        )
        
        self.register_tool(
            name="get_timeout",
            description="获取当前wolframscript执行的超时时限(秒)",
            func=self._get_timeout,
            parameters={
                "type": "object",
                "properties": {}
            }
        )
    
    def register_tool(self, name: str, description: str, func: Callable, 
                     parameters: Optional[Dict] = None):
        """
        向工具箱中注册一个新工具
        
        Args:
            name: 工具名称
            description: 工具描述
            func: 工具执行函数
            parameters: 工具参数的JSON Schema(用于OpenAI API)
        """
        self.tools[name] = {
            "description": description,
            "func": func,
            "parameters": parameters or {"type": "object", "properties": {}}
        }

    
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        根据名称获取一个工具的执行函数
        """
        tool = self.tools.get(name)
        return tool.get("func") if tool else None
    
    def get_available_tools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
    
    def get_openai_tools(self) -> List[Dict]:
        """
        生成OpenAI API兼容的工具定义列表.
        可以直接用于 chat.completions.create(tools=...)
        """
        openai_tools = []
        for name, info in self.tools.items():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": info["parameters"]
                }
            })
        return openai_tools
    
    def execute_tool(self, tool_call) -> str:
        """
        执行工具调用(兼容OpenAI的tool_call格式).
        
        Args:
            tool_call: OpenAI API返回的tool_call对象, 包含function.name和function.arguments
        
        Returns:
            str: 工具执行结果
        """
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        func = self.get_tool(tool_name)
        if not func:
            return f"错误: 未找到工具 '{tool_name}'"
        
        try:
            result = func(**arguments)
            return str(result)
        except Exception as e:
            return f"工具执行失败: {str(e)}"
    
    #内部工具实现
    def _set_timeout(self, seconds: int) -> str:
        """设置超时时限"""
        global wolfram_timeout
        if seconds <= 0:
            return "错误: 超时时限必须大于0"
        wolfram_timeout = seconds
        return f"超时时限已设置为 {seconds} 秒"
    
    def _get_timeout(self) -> int:
        """获取超时时限"""
        return wolfram_timeout
    
    def _test_connection(self) -> str:
        """测试 wolframscript.exe 是否可用"""
        if not WOLFRAMSCRIPT_PATH:
            return "错误: 未配置 WOLFRAMSCRIPT_PATH, 请在 .env 文件中设置 WOLFRAMSCRIPT_PATH 为 wolframscript.exe 的绝对路径"
        
        try:
            result = subprocess.run(
                [WOLFRAMSCRIPT_PATH, "-code", "2+2"],  
                capture_output=True,
                text=True,
                timeout=wolfram_timeout
            )
            if result.returncode == 0:
                return f"wolframscript.exe 连接成功! 2+2 = {result.stdout.strip()}"
            else:
                return f"连接失败: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"错误: 执行超时 (当前超时时限: {wolfram_timeout} 秒)"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def _run_wolfram(self, code: str, output_type: str = "math_text") -> str:
        """
        执行 Wolfram 代码并返回结果
        
        Args:
            code: Wolfram 代码或绘图代码
            output_type: 输出模式
                - "math_text": 返回纯文本
                - "plot_image": 渲染数学图像, 保存至 plots/
                - "wolfram_expression_image": 渲染 Wolfram 表达式, 保存至 expressions/
        
        Returns:
            str: 计算结果或图片路径
        """
        if not WOLFRAMSCRIPT_PATH:
            return "错误: 未配置 WOLFRAMSCRIPT_PATH, 请在 .env 文件中设置 WOLFRAMSCRIPT_PATH 为 wolframscript.exe 的绝对路径"
        
        # 文本模式直接执行
        if output_type == "math_text":
            try:
                result = subprocess.run(
                    [WOLFRAMSCRIPT_PATH, "-code", code],
                    capture_output=True,
                    text=True,
                    timeout=wolfram_timeout
                )
                if result.returncode != 0:
                    return f"执行失败: {result.stderr}"
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                return f"错误: 执行超时 (当前超时时限: {wolfram_timeout} 秒), 你的选择的表达式很可能计算量太大了"
            except Exception as e:
                return f"错误: {str(e)}"
        
        # 图片模式: 确定保存目录和文件名前缀
        if output_type == "plot_image":
            # 数学图像放在 plots/
            save_dir = os.path.join(os.path.dirname(__file__), "plots")
            prefix = "plot"
        elif output_type == "wolfram_expression_image":
            # 表达式图片放在 expressions/
            save_dir = os.path.join(os.path.dirname(__file__), "expressions")
            prefix = "expression"
        else:
            return f"错误: 未知的输出模式 '{output_type}'"
        
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(save_dir, filename)
        filepath_posix = filepath.replace("\\", "/")
        

        if output_type == "plot_image":
            wolfram_code = f'Export["{filepath_posix}", {code}, "PNG"];'
        elif output_type == "wolfram_expression_image":
            wolfram_code = (
                f'Export["{filepath_posix}", '
                f'Rasterize[TraditionalForm[HoldForm[{code}]], "Image", '
                f'ImageResolution -> 300, Background -> White], "PNG"];'
            )
        else:
            return f"错误: 未知的输出模式 '{output_type}'"
        
        try:
            result = subprocess.run(
                [WOLFRAMSCRIPT_PATH, "-code", wolfram_code],
                capture_output=True,
                text=True,
                timeout=wolfram_timeout
            )
            
            if result.returncode != 0:
                return f"执行失败: {result.stderr}"
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
            else:
                return f"错误: 图片生成失败, 请检查输入代码. 提示: plot_image 模式需确保是合法的绘图代码; wolfram_expression_image 模式需确保是合法的 Wolfram 表达式"
        except subprocess.TimeoutExpired:
            return f"错误: 执行超时 (当前超时时限: {wolfram_timeout} 秒)"
        except Exception as e:
            return f"错误: {str(e)}"