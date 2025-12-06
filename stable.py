import torch
from diffusers import ZImagePipeline
from pathlib import Path
import time
import os
import datetime

def get_user_input(prompt_text, default_value=None):
    """获取用户输入，支持默认值"""
    if default_value:
        user_input = input(f"{prompt_text} (默认: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt_text}: ").strip()

def get_integer_input(prompt_text, default_value=None, min_value=None, max_value=None):
    """获取整数输入，支持范围验证"""
    while True:
        try:
            if default_value:
                input_str = input(f"{prompt_text} (默认: {default_value}): ").strip()
                value = int(input_str) if input_str else default_value
            else:
                value = int(input(f"{prompt_text}: ").strip())
            
            if min_value is not None and value < min_value:
                print(f"❌ 值不能小于 {min_value}，请重新输入")
                continue
            if max_value is not None and value > max_value:
                print(f"❌ 值不能大于 {max_value}，请重新输入")
                continue
                
            return value
        except ValueError:
            print("❌ 请输入有效的整数")

def select_optimization_mode():
    """让用户选择优化模式"""
    print("\n" + "="*50)
    print("🔧 请选择显存优化模式")
    print("="*50)
    print("1. 基础优化 - 平衡性能和显存使用")
    print("2. 低显存优化 - 最小化显存占用，适合低显存设备")
    
    while True:
        choice = get_integer_input("请选择优化模式", 1, 1, 2)
        
        if choice == 1:
            print("✅ 已选择: 基础优化模式")
            return "basic"
        elif choice == 2:
            print("✅ 已选择: 低显存优化模式")
            return "low_vram"

def apply_low_vram_optimizations(pipe):
    """应用最低显存优化方法"""
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

def is_high_resolution(width, height):
    """检查是否为高分辨率（大于2K）"""
    # 2K分辨率通常指2048×1080或更高
    # 这里我们检查任一边长大于2048或总像素数大于2K
    return width > 2048 or height > 2048 or (width * height > 2048 * 1080)

def save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode):
    """将图片保存到gallery文件夹中的子文件夹"""
    # 确保gallery文件夹存在
    gallery_dir = Path("gallery")
    gallery_dir.mkdir(exist_ok=True)
    
    # 获取文件名（不含扩展名）作为子文件夹名
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    
    # 创建以文件名命名的子文件夹
    image_folder = gallery_dir / base_name
    
    # 如果文件夹已存在，添加时间戳
    if image_folder.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_folder = gallery_dir / f"{base_name}_{timestamp}"
    
    image_folder.mkdir(exist_ok=True)
    
    # 保存图片到子文件夹
    image_path = image_folder / f"{base_name}{extension}"
    image.save(image_path)
    
    # 创建参数信息文件
    info_file = image_folder / f"{base_name}_info.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"图片名称: {base_name}{extension}\n")
        f.write(f"提示词: {prompt}\n")
        f.write(f"图片尺寸: {width}x{height}\n")
        f.write(f"推理步数: {steps}\n")
        f.write(f"优化模式: {optimization_mode}\n")
        f.write(f"生成时间: {gen_time:.2f}秒\n")
        f.write(f"创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return image_folder

def interactive_generate(pipe, optimization_mode):
    """交互式生成图片"""
    print("\n" + "="*50)
    print("🎨 交互式图片生成")
    print("="*50)
    
    # 标记是否已应用低显存优化
    low_vram_applied = False
    
    while True:
        print("\n请输入图片生成参数:")
        
        # 获取用户输入
        prompt = get_user_input("提示词")
        if not prompt:
            print("❌ 提示词不能为空")
            continue
            
        filename = get_user_input("文件名", "generated_image.png")
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
            
        width = get_integer_input("图片宽度", 1024, 256, 4096)
        height = get_integer_input("图片高度", 1024, 256, 4096)
        steps = get_integer_input("推理步数", 15, 1, 50)
        
        # 检查是否为高分辨率，如果是且未应用低显存优化，则应用
        if is_high_resolution(width, height) and not low_vram_applied and optimization_mode != "low_vram":
            print(f"\n⚠️ 检测到高分辨率图片 ({width}x{height})，启用低显存优化模式...")
            apply_low_vram_optimizations(pipe)
            low_vram_applied = True
        
        # 生成图片
        print(f"\n🔄 开始生成图片: {prompt}")
        start_time = time.time()
        
        try:
            image = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=0.0,  # 固定引导强度为0.0
            ).images[0]
            
            gen_time = time.time() - start_time
            
            # 保存图片到gallery文件夹中的子文件夹
            gallery_folder = save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode)
            print(f"✅ 图片已保存到gallery: {gallery_folder}")
            
            print(f"⏱️ 生成时间: {gen_time:.2f}秒")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            # 如果是显存不足错误，尝试应用低显存优化
            if "out of memory" in str(e).lower() and not low_vram_applied:
                print("💡 检测到显存不足，尝试启用低显存优化模式...")
                apply_low_vram_optimizations(pipe)
                low_vram_applied = True
                print("请重试生成...")
                continue
        
        # 询问是否继续
        continue_choice = input("\n是否继续生成下一张图片? (y/n): ").strip().lower()
        if continue_choice != 'y':
            break
    
    print("\n👋 感谢使用，再见!")

def main():
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
    
    # 不清理显存，保持模型加载状态
    print("\n📝 模型保持加载状态")

if __name__ == "__main__":
    main()