"""
增强版提示词优化器模块
支持用户自由输入画风、人物、姿势、背景、服饰等详细描述
"""

import requests
import json
import os
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class PromptConfig:
    """提示词配置类 - 支持用户自由输入"""
    # 画风描述
    art_style: str = ""
    # 人物描述
    character_description: str = ""
    # 姿势描述
    pose_description: str = ""
    # 背景描述
    background_description: str = ""
    # 服饰描述
    clothing_description: str = ""
    # 其他描述
    lighting_description: str = ""
    composition_description: str = ""
    additional_details: str = ""

class AdvancedPromptOptimizer:
    """增强版提示词优化器类 - 支持用户自定义输入"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化优化器
        
        Args:
            api_key: DeepSeek API密钥，如果为None则从环境变量读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def optimize_with_config(self, original_prompt: str, config: PromptConfig) -> str:
        """
        根据用户自定义配置优化提示词
        
        Args:
            original_prompt: 原始提示词
            config: 用户自定义的提示词配置对象
            
        Returns:
            优化后的提示词
        """
        if not self.api_key:
            print("⚠️ 未设置DeepSeek API密钥，将返回原始提示词")
            return original_prompt
        
        # 构建详细的优化指令
        system_prompt = self._build_system_prompt(config)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": f"请根据以上要求优化以下提示词：\n\n{original_prompt}"
            }
        ]
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1500,
                "stream": False
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            optimized_prompt = result["choices"][0]["message"]["content"].strip()
            
            print(f"✅ 提示词优化完成")
            print(f"📝 原始提示词: {original_prompt}")
            print(f"✨ 优化后提示词: {optimized_prompt}")
            
            return optimized_prompt
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {e}")
            return original_prompt
        except (KeyError, IndexError) as e:
            print(f"❌ API响应解析失败: {e}")
            return original_prompt
        except Exception as e:
            print(f"❌ 优化过程中出错: {e}")
            return original_prompt
    
    def _build_system_prompt(self, config: PromptConfig) -> str:
        """构建系统提示词"""
        prompt_parts = []
        
        prompt_parts.append("你是一个专业的AI绘画提示词优化专家。请根据以下用户自定义要求优化提示词：")
        
        # 添加用户自定义的描述
        if config.art_style:
            prompt_parts.append(f"- 画风要求：{config.art_style}")
        
        if config.character_description:
            prompt_parts.append(f"- 人物要求：{config.character_description}")
        
        if config.pose_description:
            prompt_parts.append(f"- 姿势要求：{config.pose_description}")
        
        if config.background_description:
            prompt_parts.append(f"- 背景要求：{config.background_description}")
        
        if config.clothing_description:
            prompt_parts.append(f"- 服饰要求：{config.clothing_description}")
        
        if config.lighting_description:
            prompt_parts.append(f"- 光照要求：{config.lighting_description}")
        
        if config.composition_description:
            prompt_parts.append(f"- 构图要求：{config.composition_description}")
        
        if config.additional_details:
            prompt_parts.append(f"- 其他要求：{config.additional_details}")
        
        prompt_parts.append("\n优化要求：")
        prompt_parts.append("1. 保持原始提示词的核心意思不变")
        prompt_parts.append("2. 将用户的所有要求整合到优化后的提示词中")
        prompt_parts.append("3. 确保优化后的提示词清晰、具体、易于AI理解")
        prompt_parts.append("4. 使用专业的美术术语和描述性语言")
        prompt_parts.append("5. 确保提示词长度适中，既详细又不过于冗长")
        prompt_parts.append("6. 优先使用英文专业术语（如需要可适当添加中文说明）")
        
        return "\n".join(prompt_parts)
    
    def quick_optimize_with_style(self, prompt: str, art_style: str) -> str:
        """快速优化（指定画风）"""
        config = PromptConfig(art_style=art_style)
        return self.optimize_with_config(prompt, config)

# 保留原有简单优化器类
class PromptOptimizer:
    """简单提示词优化器类（向后兼容）"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.advanced_optimizer = AdvancedPromptOptimizer(api_key)
    
    def optimize_prompt(self, original_prompt: str, target_style: str = "简洁") -> str:
        """简单优化方法"""
        config = PromptConfig()
        if target_style == "简洁":
            config.art_style = "简约风格"
        elif target_style == "详细":
            config.art_style = "写实风格"
        elif target_style == "专业":
            config.art_style = "数字艺术风格"
        elif target_style == "创意":
            config.art_style = "抽象艺术风格"
        
        return self.advanced_optimizer.optimize_with_config(original_prompt, config)

def optimize_prompt_interactive(original_prompt: str) -> str:
    """
    增强版交互式提示词优化 - 支持用户自由输入
    
    Args:
        original_prompt: 原始提示词
        
    Returns:
        优化后的提示词或用户选择的结果
    """
    print(f"\n📝 当前提示词: {original_prompt}")
    
    # 选择优化模式
    print("\n请选择优化模式:")
    print("1. 快速优化（简单风格选择）")
    print("2. 详细配置优化（自定义输入画风、人物、背景等）")
    print("3. 跳过优化")
    
    from user_input import get_integer_input
    mode_choice = get_integer_input("请选择模式", default_value=3, min_value=1, max_value=3)
    
    if mode_choice == 3:
        return original_prompt
    elif mode_choice == 1:
        return _simple_optimize_interactive(original_prompt)
    else:
        return _detailed_optimize_interactive(original_prompt)

def _simple_optimize_interactive(original_prompt: str) -> str:
    """简单交互式优化"""
    print("\n请选择优化风格:")
    print("1. 简洁优化（简约风格）")
    print("2. 详细优化（写实风格）") 
    print("3. 专业优化（数字艺术风格）")
    print("4. 创意优化（抽象艺术风格）")
    
    from user_input import get_integer_input
    choice = get_integer_input("请选择", default_value=1, min_value=1, max_value=4)
    
    style_map = {
        1: "简洁",
        2: "详细", 
        3: "专业",
        4: "创意"
    }
    
    target_style = style_map[choice]
    optimizer = PromptOptimizer()
    
    return optimizer.optimize_prompt(original_prompt, target_style)

def _detailed_optimize_interactive(original_prompt: str) -> str:
    """详细交互式优化 - 支持用户自由输入"""
    from user_input import get_user_input
    
    config = PromptConfig()
    optimizer = AdvancedPromptOptimizer()
    
    print("\n🎨 详细配置优化（请输入具体描述）")
    print("=" * 50)
    print("💡 提示：可以输入具体描述，如'日系动漫风格'、'年轻女性'、'坐在樱花树下'等")
    print("直接按回车跳过该选项")
    print("=" * 50)
    
    # 画风描述
    config.art_style = get_user_input("请输入画风描述（如：日系动漫、写实油画、赛博朋克）", "")
    
    # 人物描述
    config.character_description = get_user_input("请输入人物描述（如：年轻女性、中年男性、可爱小孩）", "")
    
    # 姿势描述
    config.pose_description = get_user_input("请输入姿势描述（如：坐着、行走、跳舞、思考）", "")
    
    # 背景描述
    config.background_description = get_user_input("请输入背景描述（如：樱花树下、城市街道、室内书房）", "")
    
    # 服饰描述
    config.clothing_description = get_user_input("请输入服饰描述（如：和服、西装、运动装、奇幻服装）", "")
    
    # 询问是否继续其他配置
    more_config = input("\n是否配置更多选项（光照、构图、其他细节）? (y/n, 默认n): ").strip().lower()
    
    if more_config == 'y':
        # 光照描述
        config.lighting_description = get_user_input("请输入光照描述（如：黄昏光线、室内灯光、戏剧性背光）", "")
        
        # 构图描述
        config.composition_description = get_user_input("请输入构图描述（如：全景、特写、俯视角度）", "")
        
        # 其他细节
        config.additional_details = get_user_input("请输入其他细节描述", "")
    
    # 显示配置摘要
    print("\n📋 配置摘要:")
    if config.art_style:
        print(f"   🎨 画风: {config.art_style}")
    if config.character_description:
        print(f"   👤 人物: {config.character_description}")
    if config.pose_description:
        print(f"   💃 姿势: {config.pose_description}")
    if config.background_description:
        print(f"   🏞️ 背景: {config.background_description}")
    if config.clothing_description:
        print(f"   👕 服饰: {config.clothing_description}")
    if config.lighting_description:
        print(f"   💡 光照: {config.lighting_description}")
    if config.composition_description:
        print(f"   📐 构图: {config.composition_description}")
    if config.additional_details:
        print(f"   📝 其他: {config.additional_details}")
    
    confirm = input("\n确认开始优化? (y/n, 默认y): ").strip().lower()
    if confirm == 'n':
        return original_prompt
    
    return optimizer.optimize_with_config(original_prompt, config)

# 便捷函数（保持向后兼容）
def quick_optimize(prompt: str) -> str:
    """快速优化提示词（简约风格）"""
    optimizer = AdvancedPromptOptimizer()
    return optimizer.quick_optimize_with_style(prompt, "简约")

def quick_optimize_with_style(prompt: str, art_style: str) -> str:
    """快速优化（指定画风）"""
    optimizer = AdvancedPromptOptimizer()
    return optimizer.quick_optimize_with_style(prompt, art_style)

def optimize_with_custom_input(prompt: str, **kwargs) -> str:
    """
    使用自定义输入优化提示词
    
    Args:
        prompt: 原始提示词
        **kwargs: 自定义配置参数，支持：
            - art_style: 画风描述
            - character: 人物描述
            - pose: 姿势描述
            - background: 背景描述
            - clothing: 服饰描述
            - lighting: 光照描述
            - composition: 构图描述
            - details: 其他细节
            
    Returns:
        优化后的提示词
    """
    config = PromptConfig()
    
    # 映射参数到配置对象
    param_mapping = {
        'art_style': 'art_style',
        'character': 'character_description', 
        'pose': 'pose_description',
        'background': 'background_description',
        'clothing': 'clothing_description',
        'lighting': 'lighting_description',
        'composition': 'composition_description',
        'details': 'additional_details'
    }
    
    for key, value in kwargs.items():
        if key in param_mapping and value:
            setattr(config, param_mapping[key], value)
    
    optimizer = AdvancedPromptOptimizer()
    return optimizer.optimize_with_config(prompt, config)