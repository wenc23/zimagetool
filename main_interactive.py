"""
主交互模块
处理图片生成的主交互流程
"""

import time
from user_input import get_user_input, get_integer_input
from image_processing import save_to_gallery
from optimization import apply_low_vram_optimizations, is_high_resolution
from prompt_optimizer import optimize_prompt_interactive

def interactive_generate(pipe, optimization_mode):
    """交互式生成图片"""
    print("\n" + "="*50)
    print("🎨 交互式图片生成")
    print("="*50)
    
    # 根据初始选择的优化模式应用相应的优化
    if optimization_mode == "low_vram":
        print("🔧 应用低显存优化...")
        apply_low_vram_optimizations(pipe)
    else:
        print("🔧 应用基础优化...")
        # 基础优化模式已启用基本优化
    
    while True:
        print("\n请输入图片生成参数:")
        
        # 获取用户输入
        prompt = get_user_input("提示词")
        if not prompt:
            print("❌ 提示词不能为空")
            continue
            
        # 询问是否优化提示词
        optimize_choice = input("是否优化提示词? (y/n, 默认n): ").strip().lower()
        if optimize_choice == 'y':
            prompt = optimize_prompt_interactive(prompt)
            
        filename = get_user_input("文件名", "generated_image.png")
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
            
        width = get_integer_input("图片宽度", 1024, 256, 4096)
        height = get_integer_input("图片高度", 1024, 256, 4096)
        steps = get_integer_input("推理步数", 9, 1, 50)  # 将默认值从15改为9
        
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
            # 如果是显存不足错误，提示用户重新启动程序选择低显存模式
            if "out of memory" in str(e).lower():
                print("💡 检测到显存不足，请重新启动程序并选择低显存优化模式")
                break
        
        # 询问是否继续
        continue_choice = input("\n是否继续生成下一张图片? (y/n): ").strip().lower()
        if continue_choice != 'y':
            break
    
    print("\n👋 感谢使用，再见!")