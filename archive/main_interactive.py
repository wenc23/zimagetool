"""
主交互模块
处理图片生成的主交互流程
重构版本 - 使用公共模块
"""

import time
from utils import (
    print_section, print_success, print_error, print_progress,
    get_user_input, get_integer_input, get_yes_no_input,
    validate_file_extension
)
from image_processing import save_to_gallery
from config_manager import config_manager
from prompt_optimizer import optimize_prompt_interactive


def interactive_generate(pipe, optimization_mode):
    """交互式生成图片"""
    print_section("🎨 交互式图片生成", width=50)

    while True:
        print("\n请输入图片生成参数:")

        # 获取用户输入
        prompt = get_user_input("提示词")
        if not prompt:
            print_error("提示词不能为空")
            continue

        # 询问是否优化提示词
        if get_yes_no_input("是否优化提示词?", default_value=False):
            prompt = optimize_prompt_interactive(prompt)

        filename = get_user_input("文件名", config_manager.get("default_filename"))
        filename = validate_file_extension(filename)

        width = get_integer_input(
            "图片宽度",
            default_value=config_manager.get("default_width"),
            min_value=256,
            max_value=4096
        )
        height = get_integer_input(
            "图片高度",
            default_value=config_manager.get("default_height"),
            min_value=256,
            max_value=4096
        )
        steps = get_integer_input(
            "推理步数",
            default_value=config_manager.get("default_steps"),
            min_value=1,
            max_value=50
        )

        # 生成图片
        print_progress(f"开始生成图片: {prompt}")
        start_time = time.time()

        try:
            image = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=0.0,
            ).images[0]

            gen_time = time.time() - start_time
            print_success(f"图片生成完成! 耗时: {gen_time:.2f}秒")

            # 保存图片
            gallery_folder = save_to_gallery(
                image, filename, prompt, width, height, steps,
                gen_time, optimization_mode
            )

            print_success(f"图片已保存到: {gallery_folder}")

        except Exception as e:
            print_error(f"生成失败: {e}")
            if "out of memory" in str(e).lower():
                print("💡 检测到显存不足，请尝试使用低显存优化模式")

        # 询问是否继续
        if not get_yes_no_input("是否继续生成图片?", default_value=True):
            print_success("感谢使用 Z-Image-Turbo 图片生成器!")
            break
