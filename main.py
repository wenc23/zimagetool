"""
主程序模块
Z-Image-Turbo 图片生成器主入口
"""

import torch
import time
from pathlib import Path
from diffusers import ZImagePipeline
from optimization import select_optimization_mode
from main_interactive import interactive_generate

def main():
    """主函数"""
    print("="*60)
    print("🎨 Z-Image-Turbo 图片生成器")
    print("="*60)
    print("💡 新功能: 集成提示词优化器，提升图片生成质量!")
    print("🔧 支持多种在线API和本地优化")
    print("="*60)
    
    # 让用户选择优化模式
    optimization_mode = select_optimization_mode()
    
    local_model_path = Path("models/Z-Image-Turbo")
    
    if not local_model_path.exists():
        print(f"❌ 错误: 模型路径不存在: {local_model_path}")
        return
    
    print(f"📁 从本地路径加载模型: {local_model_path}")
    
    start_time = time.time()
    try:
        # 根据优化模式选择加载参数
        if optimization_mode == "low_vram":
            # 低显存优化模式使用不同的加载参数
            pipe = ZImagePipeline.from_pretrained(
                str(local_model_path),
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                local_files_only=True,
                offload_folder="offload",
            )
            
            # 应用低显存优化
            from optimization import apply_low_vram_optimizations
            apply_low_vram_optimizations(pipe)
        else:
            # 基础优化模式使用平衡模式分配设备
            pipe = ZImagePipeline.from_pretrained(
                str(local_model_path),
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                local_files_only=True,
                device_map="balanced",  # 使用平衡模式分配设备
            )
            
            # 启用基本显存优化
            pipe.enable_attention_slicing("max")
        
        load_time = time.time() - start_time
        print(f"✅ 模型加载成功! 耗时: {load_time:.2f}秒")
        
        # 进入交互式生成模式
        interactive_generate(pipe, optimization_mode)
        
    except Exception as e:
        print(f"❌ 加载模型时出错: {e}")
        return
    

if __name__ == "__main__":
    main()