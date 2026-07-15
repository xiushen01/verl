"""
自定义 FunctionTool 。

在 YAML 配置中引用：
    actor_rollout_ref:
      rollout:
        multi_turn:
          format: hermes
          function_tool_path: examples/my_tools.py
"""

from verl.tools.function_tool import function_tool


@function_tool
def get_weather(location: str) -> str:
    """获取指定地点的天气信息。

    Args:
        location: 城市名称，例如"北京"、"上海"

    Returns:
        天气信息的字符串描述
    """
    # 这里写实际逻辑，可以是 API 调用等
    return f"{location}的天气：晴天，25°C"


@function_tool
def calculator(expr: str) -> str:
    """计算数学表达式。

    Args:
        expr: 数学表达式，如 "1+2*3"

    Returns:
        计算结果
    """
    try:
        result = eval(expr)  # 注意：仅作示例，生产环境慎用 eval
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"


@function_tool
def search_database(query: str) -> tuple[str, float]:
    """搜索数据库中的记录。

    Args:
        query: 搜索关键词

    Returns:
        (查询结果文本, 奖励分数)
    """
    results = [
        {"id": 1, "name": "Alice", "role": "engineer"},
        {"id": 2, "name": "Bob", "role": "designer"},
    ]
    matched = [r for r in results if query.lower() in r["name"].lower()]
    if matched:
        import json
        return f"找到 {len(matched)} 条记录:\n{json.dumps(matched, indent=2, ensure_ascii=False)}", 1.0
    else:
        return f"未找到匹配 '{query}' 的记录", 0.0


@function_tool
async def fetch_url(url: str, timeout: int = 10) -> str:
    """异步获取 URL 内容。

    Args:
        url: 要访问的网址
        timeout: 超时时间（秒），默认 10

    Returns:
        页面内容的文本摘要
    """
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                text = await resp.text()
                return f"状态码: {resp.status}, 内容长度: {len(text)} 字符"
    except Exception as e:
        return f"请求失败: {e}"
