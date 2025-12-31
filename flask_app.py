"""
Flask Web 应用
Z-Image-Turbo 图片生成器的 Web 界面
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
from pathlib import Path
import os
import time
import threading
import uuid

from model_manager import model_manager, load_model, get_pipe, is_model_loaded, unload_model
from image_processing import save_to_gallery
from prompt_optimizer import optimize_with_custom_input
from config_manager import config_manager
from utils import validate_file_extension

# 创建 Flask 应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON

# 加载环境变量
config_manager.load_from_env()

# 存储生成任务状态
generation_tasks = {}


def generate_image_task(task_id, prompt, width, height, steps, filename, optimize_prompt,
                       art_style, character_description, pose_description, background_description,
                       clothing_description, lighting_description, composition_description,
                       additional_details, optimization_mode):
    """
    后台图片生成任务
    """
    try:
        pipe = get_pipe()
        if not pipe:
            generation_tasks[task_id] = {
                'status': 'failed',
                'message': '请先加载模型',
                'progress': 0
            }
            return

        # 更新任务状态 - 开始优化提示词
        generation_tasks[task_id]['progress'] = 5
        generation_tasks[task_id]['stage'] = '优化提示词...'

        # 如果启用提示词优化
        if optimize_prompt:
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
        filename = validate_file_extension(filename)

        # 更新任务状态 - 开始生成
        generation_tasks[task_id]['progress'] = 10
        generation_tasks[task_id]['stage'] = '准备生成...'
        generation_tasks[task_id]['prompt'] = prompt

        print(f"🔄 [任务 {task_id}] 开始生成图片: {prompt}")
        start_time = time.time()

        # 更新进度 - 开始生成
        generation_tasks[task_id]['progress'] = 15
        generation_tasks[task_id]['stage'] = '初始化...'

        # 生成图片（带进度更新）
        def progress_callback(pipe, step, timestep, callback_kwargs):
            # 从15%到85%，共70%用于生成过程
            progress = 15 + int((step + 1) / steps * 70)
            generation_tasks[task_id]['progress'] = progress
            generation_tasks[task_id]['stage'] = f'生成中: {step + 1}/{steps} 步'
            return callback_kwargs  # 必须返回 callback_kwargs

        # 验证并准备生成参数
        generation_params = {
            "prompt": prompt,
            "height": height,
            "width": width,
            "num_inference_steps": steps,
            "guidance_scale": 0.0,
        }

        # 确保所有参数都不为 None
        for key, value in generation_params.items():
            if value is None:
                raise ValueError(f"参数 {key} 不能为 None")

        print(f"📝 生成参数: prompt={prompt[:50]}..., size={width}x{height}, steps={steps}")

        # 尝试使用回调（如果支持）
        try:
            print(f"🎨 [任务 {task_id}] 开始图片生成...")
            image = pipe(
                **generation_params,
                callback_on_step_end=progress_callback,
            ).images[0]
            print(f"✅ [任务 {task_id}] 图片生成完成")
        except TypeError as e:
            # 如果回调参数不支持，使用不带回调的方式
            print(f"⚠️ 回调函数不支持，使用基本生成模式: {e}")
            image = pipe(**generation_params).images[0]
            print(f"✅ [任务 {task_id}] 图片生成完成（基本模式）")

        gen_time = time.time() - start_time
        print(f"⏱️ [任务 {task_id}] 生成耗时: {gen_time:.2f}秒")

        # 更新进度 - 生成已完成，准备保存 (85%)
        generation_tasks[task_id]['progress'] = 88
        generation_tasks[task_id]['stage'] = '生成完成，准备保存...'
        print(f"💾 [任务 {task_id}] 准备保存图片...")

        # 保存图片到画廊
        try:
            save_start = time.time()
            print(f"💾 [任务 {task_id}] 调用 save_to_gallery...")
            gallery_folder = save_to_gallery(
                image, filename, prompt, width, height, steps,
                gen_time, optimization_mode
            )
            save_duration = time.time() - save_start
            print(f"💾 [任务 {task_id}] 图片保存完成，耗时: {save_duration:.2f}秒")

            # 保存完成 (92%)
            generation_tasks[task_id]['progress'] = 92
            generation_tasks[task_id]['stage'] = '保存完成...'
        except Exception as save_error:
            print(f"❌ [任务 {task_id}] 保存图片失败: {save_error}")
            import traceback
            traceback.print_exc()
            raise Exception(f"保存图片失败: {str(save_error)}")

        # 构建文件路径和URL
        print(f"🔗 [任务 {task_id}] 构建文件路径...")
        file_path = Path(gallery_folder) / filename
        gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
        relative_path = file_path.relative_to(gallery_dir)
        image_url = f"/gallery/{relative_path.as_posix()}"

        # 任务完成
        print(f"🎉 [任务 {task_id}] 全部完成！")
        generation_tasks[task_id] = {
            'status': 'completed',
            'progress': 100,
            'stage': '完成！',
            'image_url': image_url,
            'file_path': str(file_path),
            'prompt': prompt,
            'message': f"✅ 图片已保存到: {file_path}\\n⏱️ 生成时间: {gen_time:.2f}秒",
            'gen_time': gen_time
        }

        print(f"✅ [任务 {task_id}] 任务已完成")

    except Exception as e:
        import traceback
        error_msg = f"❌ 生成失败: {str(e)}"
        if "out of memory" in str(e).lower():
            error_msg += "\n💡 检测到显存不足,请尝试使用低显存优化模式"

        # 打印完整的错误堆栈以便调试
        print(f"❌ [任务 {task_id}] 生成失败: {e}")
        print("完整错误堆栈:")
        traceback.print_exc()

        generation_tasks[task_id] = {
            'status': 'failed',
            'message': error_msg,
            'progress': 0
        }


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/gallery')
def gallery():
    """画廊页面"""
    gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))

    images = []
    if gallery_dir.exists():
        # 遍历gallery文件夹
        for image_folder in sorted(gallery_dir.iterdir(), reverse=True):
            if image_folder.is_dir():
                # 查找图片文件
                image_files = list(image_folder.glob('*.png')) + list(image_folder.glob('*.jpg')) + list(image_folder.glob('*.jpeg'))

                if image_files:
                    image_file = image_files[0]
                    image_name = image_file.name

                    # 读取info文件
                    info_file = image_folder / f"{image_file.stem}_info.txt"
                    info = {}
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if ':' in line:
                                    key, value = line.strip().split(':', 1)
                                    info[key] = value

                    # 转换为URL路径
                    gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
                    relative_path = image_file.relative_to(gallery_dir)
                    image_url = f"/gallery/{relative_path.as_posix()}"

                    images.append({
                        'name': image_name,
                        'folder': image_folder.name,
                        'path': image_url,
                        'info': info
                    })

    return render_template('gallery.html', images=images)


# ==================== API 路由 ====================

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    return jsonify({
        'model_loaded': is_model_loaded()
    })


@app.route('/api/config')
def api_config():
    """获取配置"""
    return jsonify({
        'default_width': config_manager.get("default_width"),
        'default_height': config_manager.get("default_height"),
        'default_steps': config_manager.get("default_steps"),
        'default_filename': config_manager.get("default_filename")
    })


@app.route('/api/load-model', methods=['POST'])
def api_load_model():
    """加载模型"""
    data = request.get_json()
    optimization_mode = data.get('optimization_mode', 'basic')

    try:
        success, message = load_model(
            optimization_mode=optimization_mode,
            model_path=config_manager.get("model_path")
        )

        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"加载模型失败: {str(e)}"
        })


@app.route('/api/unload-model', methods=['POST'])
def api_unload_model():
    """卸载模型"""
    try:
        success, message = unload_model()

        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"卸载模型失败: {str(e)}"
        })


@app.route('/api/optimize-prompt', methods=['POST'])
def api_optimize_prompt():
    """
    优化提示词 API
    接收用户输入和优化参数,返回优化后的提示词
    """
    try:
        data = request.get_json()

        # 获取原始提示词
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({
                'success': False,
                'message': '提示词不能为空'
            })

        # 获取优化参数
        art_style = data.get('art_style', '')
        character_description = data.get('character_description', '')
        pose_description = data.get('pose_description', '')
        background_description = data.get('background_description', '')
        clothing_description = data.get('clothing_description', '')
        lighting_description = data.get('lighting_description', '')
        composition_description = data.get('composition_description', '')
        additional_details = data.get('additional_details', '')

        # 调用优化函数
        optimized_prompt = optimize_with_custom_input(
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

        return jsonify({
            'success': True,
            'optimized_prompt': optimized_prompt,
            'message': '提示词优化成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'优化失败: {str(e)}'
        })


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    生成图片 API - 启动后台任务
    """
    try:
        data = request.get_json()

        # 检查模型是否已加载
        pipe = get_pipe()
        if not pipe:
            return jsonify({
                'success': False,
                'message': '请先加载模型'
            })

        # 获取基本参数
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({
                'success': False,
                'message': '提示词不能为空'
            })

        width = data.get('width', 1024)
        height = data.get('height', 1024)
        steps = data.get('steps', 9)
        filename = data.get('filename', 'generated_image.png')
        optimize_prompt = data.get('optimize_prompt', False)
        optimization_mode = data.get('optimization_mode', 'basic')

        art_style = data.get('art_style', '')
        character_description = data.get('character_description', '')
        pose_description = data.get('pose_description', '')
        background_description = data.get('background_description', '')
        clothing_description = data.get('clothing_description', '')
        lighting_description = data.get('lighting_description', '')
        composition_description = data.get('composition_description', '')
        additional_details = data.get('additional_details', '')

        # 创建任务ID
        task_id = str(uuid.uuid4())

        # 初始化任务状态
        generation_tasks[task_id] = {
            'status': 'pending',
            'progress': 0,
            'stage': '准备中...'
        }

        # 启动后台线程生成图片
        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, width, height, steps, filename, optimize_prompt,
                  art_style, character_description, pose_description, background_description,
                  clothing_description, lighting_description, composition_description,
                  additional_details, optimization_mode)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '生成任务已启动'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动生成任务失败: {str(e)}'
        })


@app.route('/api/generate/progress/<task_id>')
def api_generate_progress(task_id):
    """
    查询生成任务进度
    """
    if task_id not in generation_tasks:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        })

    task = generation_tasks[task_id]
    return jsonify({
        'success': True,
        'status': task.get('status', 'pending'),
        'progress': task.get('progress', 0),
        'stage': task.get('stage', ''),
        'image_url': task.get('image_url'),
        'message': task.get('message'),
        'prompt': task.get('prompt')
    })


# ==================== 删除图片 API ====================

@app.route('/api/gallery/delete', methods=['POST'])
def api_delete_gallery_item():
    """
    删除画廊图片及其信息文档
    """
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')

        if not folder_name:
            return jsonify({
                'success': False,
                'message': '缺少文件夹名称'
            })

        gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
        folder_path = gallery_dir / folder_name

        if not folder_path.exists():
            return jsonify({
                'success': False,
                'message': '图片文件夹不存在'
            })

        # 安全检查:确保路径在gallery目录内
        folder_path_resolved = folder_path.resolve()
        gallery_dir_resolved = gallery_dir.resolve()

        if not folder_path_resolved.is_relative_to(gallery_dir_resolved):
            return jsonify({
                'success': False,
                'message': '无效的路径'
            })

        # 删除整个文件夹
        import shutil
        shutil.rmtree(folder_path)

        return jsonify({
            'success': True,
            'message': f'已删除: {folder_name}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        })


# ==================== 静态文件服务 ====================

@app.route('/gallery/<path:filename>')
def serve_gallery(filename):
    """
    提供画廊图片文件
    支持子目录路径,例如: gallery/folder_name/image.png
    """
    gallery_dir = Path(config_manager.get("gallery_dir", "gallery")).resolve()
    # 安全检查:确保请求的路径在gallery目录内
    requested_path = (gallery_dir / filename).resolve()

    if not requested_path.is_relative_to(gallery_dir):
        return jsonify({'error': 'Invalid path'}), 403

    if requested_path.exists() and requested_path.is_file():
        # 根据文件扩展名设置 MIME 类型
        mimetype = None
        if requested_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            mimetype = f'image/{requested_path.suffix[1:]}'

        return send_file(str(requested_path), mimetype=mimetype)
    else:
        return jsonify({'error': 'File not found'}), 404


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """500错误处理"""
    return jsonify({'error': 'Internal server error'}), 500


# ==================== 启动应用 ====================

def main():
    """主函数"""
    # 从配置获取Flask参数
    host = config_manager.get("flask_host", "0.0.0.0")
    port = config_manager.get("flask_port", 5000)
    debug = config_manager.get("flask_debug", False)

    print("=" * 50)
    print("   Z-Image-Turbo Flask Web UI")
    print("=" * 50)
    print(f"🚀 启动服务器...")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"🎨 画廊地址: http://localhost:{port}/gallery")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
