"""
模型管理器模块
统一管理模型加载、优化模式应用和状态管理
"""

import torch
import time
import threading
from pathlib import Path
from typing import Optional, Tuple
from diffusers import ZImagePipeline


class ModelManager:
    """模型管理器类 - 单例模式管理模型实例"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化模型管理器"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self.pipe = None
            self.model_loaded = False
            self.loading_in_progress = False
            self.optimization_mode = None
            self._initialized = True

    def load_model(self, optimization_mode: str = "basic", model_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        加载模型

        Args:
            optimization_mode: 优化模式 ("basic" 或 "low_vram")
            model_path: 模型路径，默认为 "models/Z-Image-Turbo"

        Returns:
            (成功标志, 消息)
        """
        # 如果模型已经加载，直接返回
        if self.model_loaded and self.pipe is not None:
            return True, "✅ 模型已加载，无需重复加载"

        # 如果正在加载中，等待
        if self.loading_in_progress:
            return False, "🔄 模型正在加载中，请稍候..."

        # 设置模型路径
        local_model_path = Path(model_path or "models/Z-Image-Turbo")

        if not local_model_path.exists():
            return False, f"❌ 错误: 模型路径不存在: {local_model_path}"

        try:
            self.loading_in_progress = True
            start_time = time.time()

            if optimization_mode == "low_vram":
                # 低显存优化模式
                self.pipe = ZImagePipeline.from_pretrained(
                    str(local_model_path),
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True,
                    local_files_only=True,
                    offload_folder="offload",
                )

                # 应用低显存优化
                self._apply_low_vram_optimizations()
            else:
                # 基础优化模式
                self.pipe = ZImagePipeline.from_pretrained(
                    str(local_model_path),
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True,
                    local_files_only=True,
                    device_map="balanced",
                )

                # 启用基本显存优化
                self.pipe.enable_attention_slicing("max")

            load_time = time.time() - start_time
            self.model_loaded = True
            self.optimization_mode = optimization_mode
            self.loading_in_progress = False

            return True, f"✅ 模型加载成功! 耗时: {load_time:.2f}秒"

        except Exception as e:
            self.loading_in_progress = False
            return False, f"❌ 加载模型时出错: {e}"

    def _apply_low_vram_optimizations(self):
        """应用低显存优化方法"""
        if not self.pipe:
            return

        print("🔧 启用低显存优化模式...")

        try:
            # 先重置设备映射，以便启用CPU卸载
            if hasattr(self.pipe, 'reset_device_map'):
                print("🔄 重置设备映射...")
                self.pipe.reset_device_map()

            # 启用所有可用的内存优化技术
            self.pipe.enable_attention_slicing("max")  # 最大切片
            self.pipe.enable_sequential_cpu_offload()  # 顺序CPU卸载

            print("✅ 低显存优化已启用")
        except Exception as e:
            print(f"⚠️ 启用低显存优化时出错: {e}")
            print("💡 尝试使用基本优化...")
            # 如果出错，至少启用注意力切片
            self.pipe.enable_attention_slicing("max")
            print("✅ 已启用基本优化")

    def get_pipe(self):
        """获取模型管道实例"""
        return self.pipe

    def is_model_loaded(self):
        """检查模型是否已加载"""
        return self.model_loaded and self.pipe is not None

    def get_optimization_mode(self):
        """获取当前优化模式"""
        return self.optimization_mode

    def reset(self):
        """重置模型管理器状态"""
        self.pipe = None
        self.model_loaded = False
        self.loading_in_progress = False
        self.optimization_mode = None


# 创建全局实例
model_manager = ModelManager()


def load_model(optimization_mode: str = "basic", model_path: Optional[str] = None) -> Tuple[bool, str]:
    """便捷函数：加载模型"""
    return model_manager.load_model(optimization_mode, model_path)


def get_pipe():
    """便捷函数：获取模型管道"""
    return model_manager.get_pipe()


def is_model_loaded():
    """便捷函数：检查模型是否已加载"""
    return model_manager.is_model_loaded()


def get_optimization_mode():
    """便捷函数：获取优化模式"""
    return model_manager.get_optimization_mode()