"""
配置管理器模块
统一管理应用程序配置
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """应用程序配置类"""
    # 模型配置
    model_path: str = "models/Z-Image-Turbo"
    default_optimization_mode: str = "basic"  # "basic" 或 "low_vram"

    # 图片生成配置
    default_width: int = 1024
    default_height: int = 1024
    default_steps: int = 9
    default_filename: str = "generated_image.png"

    # API配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1/chat/completions"

    # 文件路径配置
    gallery_dir: str = "gallery"
    offload_folder: str = "offload"

    # 性能配置
    enable_attention_slicing: bool = True
    attention_slicing_size: str = "max"

    # Web UI配置
    webui_port: int = 7860
    webui_share: bool = False

    # Flask配置
    flask_host: str = "0.0.0.0"
    flask_port: int = 5000
    flask_debug: bool = False


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = AppConfig()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 更新配置
                for key, value in data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

                print(f"✅ 配置文件加载成功: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}, 使用默认配置")
        else:
            print(f"⚠️ 配置文件不存在: {self.config_file}, 使用默认配置")

    def save_config(self):
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典并保存
            config_dict = asdict(self.config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            print(f"✅ 配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值
        """
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键名
            value: 配置值

        Returns:
            是否成功
        """
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            return True
        return False

    def update(self, updates: Dict[str, Any]) -> bool:
        """
        批量更新配置

        Args:
            updates: 配置更新字典

        Returns:
            是否成功
        """
        success = True
        for key, value in updates.items():
            if not self.set(key, value):
                success = False
                print(f"⚠️ 未知配置项: {key}")

        return success

    def load_from_env(self):
        """从环境变量加载配置"""
        # 加载DeepSeek API密钥
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if api_key:
            self.config.deepseek_api_key = api_key
            print("✅ 从环境变量加载DeepSeek API密钥")

        # 可以添加更多环境变量配置
        model_path = os.environ.get('MODEL_PATH')
        if model_path:
            self.config.model_path = model_path
            print(f"✅ 从环境变量加载模型路径: {model_path}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return asdict(self.config)

    def create_default_config(self):
        """创建默认配置文件"""
        return self.save_config()


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return config_manager.get(key, default)


def set_config(key: str, value: Any) -> bool:
    """便捷函数：设置配置值"""
    return config_manager.set(key, value)


def save_config() -> bool:
    """便捷函数：保存配置"""
    return config_manager.save_config()


def load_from_env():
    """便捷函数：从环境变量加载配置"""
    config_manager.load_from_env()