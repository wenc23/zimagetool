"""
主交互模块
处理图片生成的主交互流程
"""

import time
from user_input import get_user_input, get_integer_input
from image_processing import save_to_gallery
from optimization import apply_low_vram_optimizations, is_high_resolution

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
        steps = get_integer_input("推理步数", 9, 1, 50)  # 将默认值从15改为9
        
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