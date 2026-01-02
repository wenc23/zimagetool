"""
提示词优化模块
使用 DeepSeek API 优化用户输入的提示词
"""

import requests
import json
from config_manager import config_manager


def optimize_with_custom_input(
    prompt,
    art_style="",
    character="",
    pose="",
    background="",
    clothing="",
    lighting="",
    composition="",
    details=""
):
    """
    使用 DeepSeek API 优化提示词

    Args:
        prompt: 原始提示词
        art_style: 画风描述
        character: 人物描述
        pose: 姿势描述
        background: 背景描述
        clothing: 服饰描述
        lighting: 光照描述
        composition: 构图描述
        details: 其他细节

    Returns:
        优化后的提示词
    """
    # 获取API密钥
    api_key = config_manager.get("deepseek_api_key", "")
    api_url = config_manager.get("deepseek_base_url", "https://api.deepseek.com/v1/chat/completions")

    # 如果没有API密钥,返回简单的组合提示词
    if not api_key:
        print("⚠️ 未设置DeepSeek API密钥,使用简单组合方式")
        return _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details)

    # 构建优化请求的提示词
    optimization_prompt = _build_optimization_prompt(
        prompt, art_style, character, pose, background, clothing, lighting, composition, details
    )

    try:
        # 调用 DeepSeek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的AI绘画提示词优化助手。你的任务是根据用户的描述,生成高质量的中文提示词。提示词应该简洁、准确、富有表现力。只返回优化后的提示词,不要包含任何解释或额外文字。"
                },
                {
                    "role": "user",
                    "content": optimization_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            # 安全检查:确保响应结构正确
            if (
                result
                and "choices" in result
                and len(result["choices"]) > 0
                and "message" in result["choices"][0]
                and "content" in result["choices"][0]["message"]
            ):
                optimized_prompt = result["choices"][0]["message"]["content"].strip()
                if optimized_prompt:  # 确保内容不为空
                    print(f"✅ 提示词优化成功")
                    return optimized_prompt
                else:
                    print(f"⚠️ API返回空内容,使用简单组合方式")
                    return _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details)
            else:
                print(f"⚠️ API响应格式异常,使用简单组合方式")
                return _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details)
        else:
            print(f"⚠️ API请求失败: {response.status_code}")
            return _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details)

    except Exception as e:
        print(f"❌ 优化提示词时出错: {e}")
        return _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details)


def _build_optimization_prompt(prompt, art_style, character, pose, background, clothing, lighting, composition, details):
    """构建发送给API的优化请求"""
    parts = []

    parts.append(f"原始描述: {prompt}")

    if art_style:
        parts.append(f"画风: {art_style}")
    if character:
        parts.append(f"人物: {character}")
    if pose:
        parts.append(f"姿势: {pose}")
    if background:
        parts.append(f"背景: {background}")
    if clothing:
        parts.append(f"服饰: {clothing}")
    if lighting:
        parts.append(f"光照: {lighting}")
    if composition:
        parts.append(f"构图: {composition}")
    if details:
        parts.append(f"其他细节: {details}")

    optimization_request = "\n".join(parts)
    optimization_request += "\n\n请根据以上信息,生成一个优化的AI绘画提示词。"

    return optimization_request


def _simple_combine(prompt, art_style, character, pose, background, clothing, lighting, composition, details):
    """简单的提示词组合方法(不使用API)"""
    parts = []

    if prompt:
        parts.append(prompt)

    # 按优先级组合各个要素
    if art_style:
        parts.append(f"{art_style} style")
    if character:
        parts.append(f"{character}")
    if clothing:
        parts.append(f"wearing {clothing}")
    if pose:
        parts.append(f"{pose}")
    if background:
        parts.append(f"in {background}")
    if lighting:
        parts.append(f"{lighting} lighting")
    if composition:
        parts.append(f"{composition} composition")
    if details:
        parts.append(details)

    # 用逗号连接
    combined = ", ".join(parts)

    print("ℹ️ 使用简单组合方式生成提示词")
    return combined


def optimize_prompt_simple(prompt, art_style=""):
    """
    简化的提示词优化方法

    Args:
        prompt: 原始提示词
        art_style: 画风描述

    Returns:
        优化后的提示词
    """
    return optimize_with_custom_input(prompt, art_style=art_style)
