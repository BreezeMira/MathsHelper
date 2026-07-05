import os
import json
import sys
from typing import Optional, Dict, List, Any
from openai import OpenAI
from openai import BadRequestError
from tools import ToolExecutor
from dotenv import load_dotenv

load_dotenv()

def load_system_prompt(prompt_file: str = "config/system_prompt.txt") -> str:
    """加载系统提示词, 如果文件不存在则报错"""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"系统提示词文件{prompt_file}不存在, 你可能删除了默认提示词文件\n")


class ReActAgent:
    def __init__(
            self,
            model: Optional[str] = None,
            reasoning_mode: Optional[bool]=None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            llm_time_out: Optional[int] = None,
            max_steps:Optional[int] = None,
    ):
        '''初始化'''
        self.model = model or os.getenv("OPENAI_MODEL")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        #不写也可以运行的环境变量

        #是否开启思考模式(默认为否)
        if(reasoning_mode==True):
            self.reasoning_mode=True
            print(f"思考模式开启")
        elif(reasoning_mode==False):
            self.reasoning_mode=False
            print(f"思考模式关闭")
        elif os.getenv("REASONING_MODE") is None:
            self.reasoning_mode=False
            print(f".env中缺少REASONING_MODE的值, 目前默认为0, 思考模式关闭")
        elif (os.getenv("REASONING_MODE")=="1"):
            self.reasoning_mode=True
            print(f"思考模式已开启")
        else:
            self.reasoning_mode=False
            print(f"思考模式已关闭")

        #LLM超时时限
        if(llm_time_out is not None):
            self.llm_time_out=llm_time_out
            print(f"目前LLM超时时限为{self.llm_time_out}秒")
        elif os.getenv("LLM_TIME_OUT") is None:
            self.llm_time_out=60
            print(f".env中缺少LLM_TIME_OUT的值, 目前使用默认值60")
        else:
            try:
                self.llm_time_out=int(os.getenv("LLM_TIME_OUT"))
                print(f"目前LLM超时时限为{self.llm_time_out}秒")
            except ValueError:
                self.llm_time_out=60
                print(f".env中LLM_TIME_OUT的值不是整数, 目前使用默认值60")

        #最大步长(默认为5)
        if(max_steps is not None):
            self.max_steps=max_steps
            print(f"目前最大步长为{self.max_steps}步")
        elif os.getenv("MAX_STEPS") is None:
            self.max_steps=5
            print(f".env中缺少MAX_STEPS的值, 目前使用默认值5")
        else:
            try:
                self.max_steps=int(os.getenv("MAX_STEPS"))
                print(f"目前最大步长为{self.max_steps}步")
            except ValueError:
                self.max_steps=5
                print(f".env中MAX_STEPS的值不是整数, 目前使用默认值5")

        #收集所有漏填的重要环境变量, 统一报错
        missing_vars = []
    
        if not self.model:
            missing_vars.append("OPENAI_MODEL")
        if not self.api_key:
            missing_vars.append("OPENAI_API_KEY")
        if not self.base_url:
            missing_vars.append("OPENAI_BASE_URL")
        
        if missing_vars:
            raise EnvironmentError(
                f"缺少必要的环境变量配置, 请在 .env 文件中设置以下变量: \n"
                f"  {', '.join(missing_vars)}\n"
            )
    
        self.client = OpenAI(
        api_key=self.api_key,
        base_url=self.base_url,
        timeout=self.llm_time_out
        )

        #工具执行器
        self.tool_executor = ToolExecutor()
        self.tools = self.tool_executor.get_openai_tools()
        #读取系统提示词为初始提示词
        self.system_prompt = load_system_prompt()
        # 对话历史
        self.messages: List[Dict[str, Any]] = []
        self.messages = [{"role": "system", "content": self.system_prompt}]
        


    def call_llm(self) ->Any:
        params = {
            "model": self.model,
            "messages": self.messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "temperature": 0.7,
        }
        # 思考模式
        if self.reasoning_mode:
            try:
                params["extra_body"] = {"reasoning": "enabled"}
                params["temperature"] = 0.0
                return self.client.chat.completions.create(**params)
            except BadRequestError as e:
                print(f"尝试思考模式出错, 降级到普通模式: {e}")
                params.pop("extra_body", None)
                params["temperature"] = 0.7
                return self.client.chat.completions.create(**params)
        else:
            return self.client.chat.completions.create(**params)
            



    def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, str]]:
        """执行工具调用并返回结果"""
        results = []
        for tool_call in tool_calls:
            # 打印工具调用信息, 方便调试
            func_name = tool_call.function.name
            func_args = tool_call.function.arguments
            print(f"\n[工具调用] {func_name}")
            print(f"[参数] {func_args}")

            result = self.tool_executor.execute_tool(tool_call)
            # 打印返回结果(截取前200字符)
            result_preview = result[:200] + "..." if len(result) > 200 else result
            print(f"[结果] {result_preview}")
            results.append({
                "tool_call_id": tool_call.id,
                "result": result
            })
        return results


    def run(self, user_input: str) -> Optional[str]:
        """执行 ReAct 循环(使用 Tool Calling), 步数用完后额外给 3 步, 
        且强制 LLM 在提交最终答案前审查长表达式并生成图片"""
        self.messages.append({"role": "user", "content": user_input})
        step = 0
        self._force_review_long = True         
        # ── 第一阶段: 正常 max_steps 步 ──
        while step < self.max_steps:
            step += 1
            try:
                response = self.call_llm()
            except Exception as e:
                print(f"LLM 调用失败: {e}")
                return None

            message = response.choices[0].message
            print(f"话: {message.content}")

            if not message.tool_calls:
                # LLM 认为可以结束了, 但我们要检查是否还需要审查长表达式
                if self._force_review_long:
                    # 第一次认为完成, 插入审查提示, 不返回最终答案
                    self._force_review_long = False
                    review_prompt = (
                        "系统提示: 在给出最终答案之前, 请你先回顾之前工具返回的所有结果, "
                        "尤其关注那些很长的数学表达式。请用简洁的语言解释这些表达式的含义, "
                        "并把其中重要的、还未可视化过的表达式绘制成图片。尤其是长的表达式, 它们一定很重要。现在给你额外最多3步来完成这些。wolfram_expression_image 模式不会先执行再渲染, 而是直接把输入的代码当作符号表达式画出来。所以传入 Reduce[...] 时, 它画的是求解命令本身, 而非解的公式。而传入纯数学表达式时, 就能正确渲染。所以应该把之前得到的长表达式结果原封不动地传进去"
                    )
                    self.messages.append({"role": "user", "content": review_prompt})
                    # 进入额外步循环(与超步数后相同的逻辑)
                    extra_step = 0
                    extra_max = 3
                    while extra_step < extra_max:
                        extra_step += 1
                        try:
                            response = self.call_llm()
                        except Exception as e:
                            print(f"LLM 调用失败(审查步): {e}")
                            return None

                        message = response.choices[0].message
                        print(f"话: {message.content}")

                        if not message.tool_calls:
                            final_answer = message.content or "我没有得到答案。"
                            self.messages.append({"role": "assistant", "content": final_answer})
                            return final_answer

                        self.messages.append({
                            "role": "assistant",
                            "content": message.content or "",
                            "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                        })
                        tool_results = self._process_tool_calls(message.tool_calls)
                        for tr in tool_results:
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tr["tool_call_id"],
                                "content": tr["result"]
                            })
                    # 额外步用完仍未结束, 强制总结
                    self.messages.append({
                        "role": "user",
                        "content": "审查步骤已用完, 请直接给出你已经解释和绘制的所有内容, 不要调用工具。"
                    })
                    original_tools = self.tools
                    self.tools = None
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=self.messages,
                            temperature=0.7,
                        )
                        final_summary = response.choices[0].message.content or "无法生成总结。"
                    except Exception as e:
                        print(f"[审查总结失败] {e}")
                        final_summary = f"审查步骤耗尽, 总结失败: {e}"
                    finally:
                        self.tools = original_tools
                    self.messages.append({"role": "assistant", "content": final_summary})
                    return final_summary
                else:
                    # 已经审查过, 直接返回最终答案
                    final_answer = message.content or "我没有得到答案。"
                    self.messages.append({"role": "assistant", "content": final_answer})
                    return final_answer

            # 正常工具调用处理
            self.messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [tc.model_dump() for tc in message.tool_calls]
            })

            tool_results = self._process_tool_calls(message.tool_calls)
            for tr in tool_results:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": tr["result"]
                })

        # ── 达到初始最大步数, 额外给 3 步机会 ──
        self.messages.append({
            "role": "user",
            "content": (
                "系统提示: 你已经用完了初始的步骤。现在额外给你 3 步机会, "
                "请先输出之前你对每次工具返回结果的内容的理解, 尤其是那些很长的表达式, "
                "再把重要且还没变成图片的表达式图片!尤其是那些很长的表达式!wolfram_expression_image 模式不会先执行再渲染, 而是直接把输入的代码当作符号表达式画出来。所以传入 Reduce[...] 时, 它画的是求解命令本身, 而非解的公式。而传入纯数学表达式时, 就能正确渲染。所以应该把之前得到的长表达式结果原封不动地传进去"
            )
        })

        extra_step = 0
        extra_max = 3
        while extra_step < extra_max:
            extra_step += 1
            try:
                response = self.call_llm()
            except Exception as e:
                print(f"LLM 调用失败(额外步): {e}")
                return None

            message = response.choices[0].message
            print(f"话: {message.content}")

            if not message.tool_calls:
                final_answer = message.content or "我没有得到答案。"
                self.messages.append({"role": "assistant", "content": final_answer})
                return final_answer

            self.messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [tc.model_dump() for tc in message.tool_calls]
            })

            tool_results = self._process_tool_calls(message.tool_calls)
            for tr in tool_results:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": tr["result"]
                })

        # ── 如果额外 3 步用完仍然没给出最终答案, 移除工具强制总结 ──
        self.messages.append({
            "role": "user",
            "content": (
                "额外步骤也已用完。请直接输出你已经获得的所有图片路径或数学结果, "
                "不要调用工具, 就基于现有信息回答。"
            )
        })

        original_tools = self.tools
        self.tools = None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
            )
            final_summary = response.choices[0].message.content or "无法生成总结。"
        except Exception as e:
            print(f"[总结失败] {e}")
            final_summary = f"步骤耗尽, 总结失败: {e}"
        finally:
            self.tools = original_tools

        self.messages.append({"role": "assistant", "content": final_summary})
        return final_summary
if __name__ == "__main__":
    agent = ReActAgent()
    print("ReAct Agent 已启动, 输入 'exit' 退出。")
    while True:
        try:
            user_input = input("\n用户: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break
        if user_input.lower() in ("exit", "quit"):
            print("再见!")
            break
        if not user_input:
            continue
        result = agent.run(user_input)
        if result:
            print(f"助手: {result}")
        else:
            print("助手: 处理请求时遇到错误, 请重试。")

                