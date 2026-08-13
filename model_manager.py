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
            self._state_lock = threading.RLock()
            self._inference_lock = threading.Lock()
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
        if optimization_mode == "lowvram":
            optimization_mode = "low_vram"
        if optimization_mode not in {"basic", "low_vram"}:
            return False, f"❌ 不支持的优化模式: {optimization_mode}"

        local_model_path = Path(model_path or "models/Z-Image-Turbo")
        if not local_model_path.exists():
            return False, f"❌ 错误: 模型路径不存在: {local_model_path}"

        # 加载、推理和卸载必须互斥，避免修改正在使用的管线。
        if not self._inference_lock.acquire(blocking=False):
            return False, "🔄 模型正在生成图片或执行其他模型操作，请稍候..."

        with self._state_lock:
            if self.model_loaded and self.pipe is not None:
                self._inference_lock.release()
                return True, "✅ 模型已加载，无需重复加载"
            if self.loading_in_progress:
                self._inference_lock.release()
                return False, "🔄 模型正在加载中，请稍候..."
            self.loading_in_progress = True

        try:
            start_time = time.time()
            self._configure_torch_runtime()

            if optimization_mode == "low_vram":
                # 低显存优化模式
                loaded_pipe = ZImagePipeline.from_pretrained(
                    str(local_model_path),
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True,
                    local_files_only=True,
                    offload_folder="offload",
                )

                # 应用低显存优化
                self._apply_low_vram_optimizations(loaded_pipe)
            else:
                # 基础优化模式
                loaded_pipe = ZImagePipeline.from_pretrained(
                    str(local_model_path),
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True,
                    local_files_only=True,
                    device_map="balanced",
                )

                # 标准模式优先吞吐量。最大注意力切片会把注意力拆成大量小操作，
                # 在显存充足时反而明显降低速度，因此只在 low_vram 模式启用。

            load_time = time.time() - start_time
            with self._state_lock:
                self.pipe = loaded_pipe
                self.model_loaded = True
                self.optimization_mode = optimization_mode
                self.loading_in_progress = False

            return True, f"✅ 模型加载成功! 耗时: {load_time:.2f}秒"

        except Exception as e:
            with self._state_lock:
                self.loading_in_progress = False
            return False, f"❌ 加载模型时出错: {e}"
        finally:
            self._inference_lock.release()

    @staticmethod
    def _configure_torch_runtime():
        """在支持的 NVIDIA GPU 上启用安全的高吞吐矩阵运算设置。"""
        if hasattr(torch, "set_float32_matmul_precision"):
            torch.set_float32_matmul_precision("high")
        if not getattr(torch, "cuda", None) or not torch.cuda.is_available():
            return
        backends = getattr(torch, "backends", None)
        cuda_backend = getattr(backends, "cuda", None)
        cudnn_backend = getattr(backends, "cudnn", None)
        if cuda_backend and hasattr(cuda_backend, "matmul"):
            cuda_backend.matmul.allow_tf32 = True
        if cudnn_backend and hasattr(cudnn_backend, "allow_tf32"):
            cudnn_backend.allow_tf32 = True

    def _apply_low_vram_optimizations(self, pipe=None):
        """应用低显存优化方法"""
        pipe = pipe or self.pipe
        if not pipe:
            return

        print("🔧 启用低显存优化模式...")

        try:
            # 先重置设备映射，以便启用CPU卸载
            if hasattr(pipe, 'reset_device_map'):
                print("🔄 重置设备映射...")
                pipe.reset_device_map()

            # 启用所有可用的内存优化技术
            pipe.enable_attention_slicing("max")  # 最大切片
            pipe.enable_sequential_cpu_offload()  # 顺序CPU卸载

            print("✅ 低显存优化已启用")
        except Exception as e:
            print(f"⚠️ 启用低显存优化时出错: {e}")
            print("💡 尝试使用基本优化...")
            # 如果出错，至少启用注意力切片
            pipe.enable_attention_slicing("max")
            print("✅ 已启用基本优化")

    def get_pipe(self):
        """获取模型管道实例"""
        with self._state_lock:
            return self.pipe if self.model_loaded else None

    def acquire_pipe_for_inference(self):
        """独占获取推理管线；调用方必须在 finally 中释放。"""
        self._inference_lock.acquire()
        with self._state_lock:
            if not self.model_loaded or self.pipe is None:
                self._inference_lock.release()
                return None
            return self.pipe

    def release_pipe_after_inference(self):
        """释放由 acquire_pipe_for_inference 获取的推理锁。"""
        self._inference_lock.release()

    def is_model_loaded(self):
        """检查模型是否已加载"""
        with self._state_lock:
            return self.model_loaded and self.pipe is not None

    def get_optimization_mode(self):
        """获取当前优化模式"""
        with self._state_lock:
            return self.optimization_mode

    def reset(self):
        """重置模型管理器状态"""
        with self._state_lock:
            self.pipe = None
            self.model_loaded = False
            self.loading_in_progress = False
            self.optimization_mode = None

    def unload_model(self) -> Tuple[bool, str]:
        """
        卸载模型并释放显存

        Returns:
            (成功标志, 消息)
        """
        if not self._inference_lock.acquire(blocking=False):
            return False, "⚠️ 图片正在生成，无法卸载模型"

        with self._state_lock:
            if not self.model_loaded:
                self._inference_lock.release()
                return False, "⚠️ 模型未加载，无需卸载"

        try:
            import gc

            # 删除模型引用
            with self._state_lock:
                pipe = self.pipe
                self.pipe = None

            if pipe is not None:
                # 如果模型有to()方法，先移到CPU（避免GPU显存碎片）
                if hasattr(pipe, 'to'):
                    try:
                        pipe.to('cpu')
                        print("🔄 模型已移至CPU")
                    except Exception:
                        pass

                # 删除各个组件
                if hasattr(pipe, 'components'):
                    for component_name in pipe.components:
                        if hasattr(pipe, component_name):
                            setattr(pipe, component_name, None)

                del pipe

            # 多轮垃圾回收
            gc.collect()
            if torch.cuda.is_available():
                gc.collect()  # 再次GC
                torch.cuda.empty_cache()  # 清空缓存
                torch.cuda.synchronize()  # 同步
                # 再次清理，确保彻底
                torch.cuda.empty_cache()

            # 重置状态
            with self._state_lock:
                self.model_loaded = False
                self.loading_in_progress = False
                self.optimization_mode = None

            # 获取显存信息
            if torch.cuda.is_available():
                # 等待一下让显存释放
                import time
                time.sleep(0.5)

                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                free = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3

                return True, f"✅ 模型已卸载\n💾 显存状态: {free:.2f}GB 可用 / {total:.2f}GB 总计\n   (已分配: {allocated:.2f}GB, 已保留: {reserved:.2f}GB)"
            else:
                return True, "✅ 模型已卸载"

        except Exception as e:
            with self._state_lock:
                self.pipe = None
                self.model_loaded = False
                self.loading_in_progress = False
                self.optimization_mode = None
            return False, f"❌ 卸载模型时出错: {e}"
        finally:
            self._inference_lock.release()


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


def unload_model() -> Tuple[bool, str]:
    """便捷函数：卸载模型"""
    return model_manager.unload_model()
