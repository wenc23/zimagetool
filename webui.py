"""
Web UI模块
基于Gradio的Web界面 - 兼容版本
"""

import gradio as gr
import torch
import time
from pathlib import Path
from diffusers import ZImagePipeline
from image_processing import save_to_gallery
from prompt_optimizer import optimize_with_custom_input, AdvancedPromptOptimizer, PromptConfig

# 全局变量存储管道实例
pipe = None

def load_model(optimization_mode):
    """加载模型"""
    global pipe
    
    local_model_path = Path("models/Z-Image-Turbo")
    
    if not local_model_path.exists():
        return f"❌ 错误: 模型路径不存在: {local_model_path}"
    
    try:
        start_time = time.time()
        
        if optimization_mode == "low_vram":
            # 低显存优化模式
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
            # 基础优化模式
            pipe = ZImagePipeline.from_pretrained(
                str(local_model_path),
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                local_files_only=True,
                device_map="balanced",
            )
            
            # 启用基本显存优化
            pipe.enable_attention_slicing("max")
        
        load_time = time.time() - start_time
        return f"✅ 模型加载成功! 耗时: {load_time:.2f}秒"
        
    except Exception as e:
        return f"❌ 加载模型时出错: {e}"

def generate_image(prompt, width, height, steps, filename, optimize_prompt, art_style, 
                  character_description, pose_description, background_description, 
                  clothing_description, lighting_description, composition_description, 
                  additional_details, optimization_mode):
    """生成图片"""
    global pipe
    
    if not pipe:
        return None, "❌ 请先加载模型"
    
    if not prompt:
        return None, "❌ 提示词不能为空"
    
    try:
        # 优化提示词
        if optimize_prompt:
            # 使用用户自定义配置进行优化
            prompt = optimize_with_custom_input(
                prompt,
                art_style=art_style,
                character=character_description,
                pose=pose_description,
                background=background_description,
                clothing=clothing_description,
                lighting=lighting_description,
                composition=composition_description,
                details=additional_details
            )
        
        # 确保文件名格式正确
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
        
        print(f"🔄 开始生成图片: {prompt}")
        start_time = time.time()
        
        # 生成图片
        image = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=steps,
            guidance_scale=0.0,
        ).images[0]
        
        gen_time = time.time() - start_time
        
        # 保存图片
        gallery_folder = save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode)
        
        message = f"✅ 图片已保存到gallery: {gallery_folder}\n⏱️ 生成时间: {gen_time:.2f}秒"
        return image, message
        
    except Exception as e:
        error_msg = f"❌ 生成失败: {e}"
        if "out of memory" in str(e).lower():
            error_msg += "\n💡 检测到显存不足，请尝试使用低显存优化模式"
        return None, error_msg

def create_webui():
    """创建Web UI界面 - 兼容版本"""
    try:
        # 尝试使用新版本的Gradio API
        with gr.Blocks(title="Z-Image-Turbo Web UI") as demo:
            gr.Markdown("# 🎨 Z-Image-Turbo 图片生成器")
            gr.Markdown("基于Gradio的Web界面，提供更友好的用户体验")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## ⚙️ 设置")
                    
                    optimization_dropdown = gr.Dropdown(
                        choices=["基础优化", "低显存优化"],
                        label="优化模式",
                        value="基础优化",
                        info="选择适合您硬件的优化模式"
                    )
                    
                    load_btn = gr.Button("🚀 加载模型", variant="primary")
                    load_status = gr.Textbox(label="加载状态", interactive=False)
                    
                    gr.Markdown("## 📝 生成参数")
                    
                    prompt_input = gr.Textbox(
                        label="提示词",
                        placeholder="请输入图片描述...",
                        lines=3
                    )
                    
                    with gr.Accordion("🎨 提示词优化配置", open=False):
                        optimize_checkbox = gr.Checkbox(
                            label="启用提示词优化",
                            value=True,
                            info="使用AI优化提示词以获得更好的效果"
                        )
                        
                        art_style_input = gr.Textbox(
                            label="画风描述",
                            placeholder="如：日系动漫、写实油画、赛博朋克...",
                            info="描述想要的画风风格"
                        )
                        
                        character_input = gr.Textbox(
                            label="人物描述", 
                            placeholder="如：年轻女性、中年男性、可爱小孩...",
                            info="描述人物特征"
                        )
                        
                        pose_input = gr.Textbox(
                            label="姿势描述",
                            placeholder="如：坐着、行走、跳舞、思考...",
                            info="描述人物姿势"
                        )
                        
                        background_input = gr.Textbox(
                            label="背景描述",
                            placeholder="如：樱花树下、城市街道、室内书房...",
                            info="描述背景环境"
                        )
                        
                        clothing_input = gr.Textbox(
                            label="服饰描述",
                            placeholder="如：和服、西装、运动装、奇幻服装...",
                            info="描述服饰特征"
                        )
                        
                        lighting_input = gr.Textbox(
                            label="光照描述",
                            placeholder="如：黄昏光线、室内灯光、戏剧性背光...",
                            info="描述光照效果"
                        )
                        
                        composition_input = gr.Textbox(
                            label="构图描述",
                            placeholder="如：全景、特写、俯视角度...",
                            info="描述构图方式"
                        )
                        
                        details_input = gr.Textbox(
                            label="其他细节",
                            placeholder="如：表情、道具、氛围等额外描述...",
                            info="其他需要强调的细节"
                        )
                    
                    filename_input = gr.Textbox(
                        label="文件名",
                        value="generated_image.png",
                        placeholder="输入保存的文件名"
                    )
                    
                    with gr.Row():
                        width_slider = gr.Slider(
                            minimum=256, maximum=4096, value=1024, step=64,
                            label="图片宽度"
                        )
                        height_slider = gr.Slider(
                            minimum=256, maximum=4096, value=1024, step=64,
                            label="图片高度"
                        )
                    
                    steps_slider = gr.Slider(
                        minimum=1, maximum=50, value=9, step=1,
                        label="推理步数"
                    )
                    
                    generate_btn = gr.Button("🎨 生成图片", variant="primary")
                    
                with gr.Column(scale=1):
                    gr.Markdown("## 🖼️ 预览")
                    image_output = gr.Image(label="生成的图片", height=512)
                    output_status = gr.Textbox(label="生成状态", interactive=False, lines=3)
            
            # 事件处理
            def on_load_model(optimization_mode):
                mode_map = {"基础优化": "base", "低显存优化": "low_vram"}
                return load_model(mode_map[optimization_mode])
            
            def on_generate_image(prompt, width, height, steps, filename, optimize_prompt, 
                                 art_style, character, pose, background, clothing, 
                                 lighting, composition, details, optimization_mode):
                mode_map = {"基础优化": "base", "低显存优化": "low_vram"}
                return generate_image(prompt, width, height, steps, filename, optimize_prompt,
                                    art_style, character, pose, background, clothing,
                                    lighting, composition, details, mode_map[optimization_mode])
            
            load_btn.click(
                fn=on_load_model,
                inputs=[optimization_dropdown],
                outputs=[load_status]
            )
            
            generate_btn.click(
                fn=on_generate_image,
                inputs=[
                    prompt_input, width_slider, height_slider, steps_slider, filename_input,
                    optimize_checkbox, art_style_input, character_input, pose_input, 
                    background_input, clothing_input, lighting_input, composition_input, 
                    details_input, optimization_dropdown
                ],
                outputs=[image_output, output_status]
            )
        
        return demo
        
    except TypeError as e:
        # 如果新版本API失败，回退到旧版本API
        print("⚠️ 检测到旧版Gradio，使用兼容模式...")
        
        # 使用旧版Gradio API
        with gr.Blocks() as demo:
            gr.Markdown("# 🎨 Z-Image-Turbo 图片生成器")
            gr.Markdown("基于Gradio的Web界面，提供更友好的用户体验")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## ⚙️ 设置")
                    
                    optimization_dropdown = gr.Dropdown(
                        choices=["基础优化", "低显存优化"],
                        label="优化模式",
                        value="基础优化"
                    )
                    
                    load_btn = gr.Button("加载模型")
                    load_status = gr.Textbox(label="加载状态", interactive=False)
                    
                    gr.Markdown("## 📝 生成参数")
                    
                    prompt_input = gr.Textbox(
                        label="提示词",
                        placeholder="请输入图片描述...",
                        lines=3
                    )
                    
                    with gr.Accordion("提示词优化配置", open=False):
                        optimize_checkbox = gr.Checkbox(
                            label="启用提示词优化",
                            value=True
                        )
                        
                        art_style_input = gr.Textbox(
                            label="画风描述",
                            placeholder="如：日系动漫、写实油画、赛博朋克..."
                        )
                        
                        character_input = gr.Textbox(
                            label="人物描述", 
                            placeholder="如：年轻女性、中年男性、可爱小孩..."
                        )
                        
                        pose_input = gr.Textbox(
                            label="姿势描述",
                            placeholder="如：坐着、行走、跳舞、思考..."
                        )
                        
                        background_input = gr.Textbox(
                            label="背景描述",
                            placeholder="如：樱花树下、城市街道、室内书房..."
                        )
                        
                        clothing_input = gr.Textbox(
                            label="服饰描述",
                            placeholder="如：和服、西装、运动装、奇幻服装..."
                        )
                        
                        lighting_input = gr.Textbox(
                            label="光照描述",
                            placeholder="如：黄昏光线、室内灯光、戏剧性背光..."
                        )
                        
                        composition_input = gr.Textbox(
                            label="构图描述",
                            placeholder="如：全景、特写、俯视角度..."
                        )
                        
                        details_input = gr.Textbox(
                            label="其他细节",
                            placeholder="如：表情、道具、氛围等额外描述..."
                        )
                    
                    filename_input = gr.Textbox(
                        label="文件名",
                        value="generated_image.png"
                    )
                    
                    with gr.Row():
                        width_slider = gr.Slider(
                            minimum=256, maximum=4096, value=1024, step=64,
                            label="图片宽度"
                        )
                        height_slider = gr.Slider(
                            minimum=256, maximum=4096, value=1024, step=64,
                            label="图片高度"
                        )
                    
                    steps_slider = gr.Slider(
                        minimum=1, maximum=50, value=9, step=1,
                        label="推理步数"
                    )
                    
                    generate_btn = gr.Button("生成图片")
                    
                with gr.Column():
                    gr.Markdown("## 🖼️ 预览")
                    image_output = gr.Image(label="生成的图片", height=512)
                    output_status = gr.Textbox(label="生成状态", interactive=False, lines=3)
            
            # 事件处理
            def on_load_model(optimization_mode):
                mode_map = {"基础优化": "base", "低显存优化": "low_vram"}
                return load_model(mode_map[optimization_mode])
            
            def on_generate_image(prompt, width, height, steps, filename, optimize_prompt, 
                                 art_style, character, pose, background, clothing, 
                                 lighting, composition, details, optimization_mode):
                mode_map = {"基础优化": "base", "低显存优化": "low_vram"}
                return generate_image(prompt, width, height, steps, filename, optimize_prompt,
                                    art_style, character, pose, background, clothing,
                                    lighting, composition, details, mode_map[optimization_mode])
            
            load_btn.click(
                fn=on_load_model,
                inputs=[optimization_dropdown],
                outputs=[load_status]
            )
            
            generate_btn.click(
                fn=on_generate_image,
                inputs=[
                    prompt_input, width_slider, height_slider, steps_slider, filename_input,
                    optimize_checkbox, art_style_input, character_input, pose_input, 
                    background_input, clothing_input, lighting_input, composition_input, 
                    details_input, optimization_dropdown
                ],
                outputs=[image_output, output_status]
            )
        
        return demo

def main():
    """启动Web UI"""
    print("🚀 启动 Z-Image-Turbo Web UI...")
    print("📱 访问地址: http://localhost:7860")
    print("⏹️ 按 Ctrl+C 停止服务")
    
    demo = create_webui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()