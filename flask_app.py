"""
Flask Web 应用
Z-Image-Turbo 图片生成器的 Web 界面
"""

from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
import time
import threading
import shutil
import math
from urllib.parse import quote

from model_manager import model_manager, load_model, is_model_loaded, unload_model
from image_processing import create_gallery_thumbnail, get_thumbnail_path, save_to_gallery
from prompt_optimizer import optimize_with_custom_input
from config_manager import config_manager
from task_manager import GenerationCancelled, TaskManager
from utils import validate_file_extension, validate_integer

# 创建 Flask 应用
app = Flask(__name__)
app.json.ensure_ascii = False  # Flask 3.x 中文 JSON

# 加载环境变量
config_manager.load_from_env()

# 仅允许一个真实工作线程使用本地 GPU；终态任务保留一小时，最多保留 100 条。
task_manager = TaskManager(retention_seconds=3600, max_completed_tasks=100)
gallery_index_lock = threading.RLock()
thumbnail_lock = threading.Lock()
gallery_index_cache = {'signature': None, 'folders': []}


def invalidate_gallery_cache():
    with gallery_index_lock:
        gallery_index_cache['signature'] = None
        gallery_index_cache['folders'] = []


def get_gallery_folders(gallery_dir):
    """按目录修改时间缓存作品目录；新增或删除作品时自动失效。"""
    gallery_dir = Path(gallery_dir)
    if not gallery_dir.exists():
        return []
    signature = gallery_dir.stat().st_mtime_ns
    with gallery_index_lock:
        if gallery_index_cache['signature'] == signature:
            return list(gallery_index_cache['folders'])
        folders = sorted(
            (path for path in gallery_dir.iterdir() if path.is_dir()),
            key=lambda path: path.name,
            reverse=True,
        )
        gallery_index_cache['signature'] = signature
        gallery_index_cache['folders'] = folders
        return list(folders)


def get_json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("请求体必须是JSON对象")
    return data


def get_text_field(data, key, label, max_length, required=False):
    value = data.get(key, '')
    if not isinstance(value, str):
        raise ValueError(f"{label}必须是字符串")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label}不能为空")
    if len(value) > max_length:
        raise ValueError(f"{label}不能超过{max_length}个字符")
    return value


def normalize_optimization_mode(value):
    if value == 'lowvram':
        value = 'low_vram'
    if value not in {'basic', 'low_vram'}:
        raise ValueError("优化模式必须是 basic 或 low_vram")
    return value


def get_prompt_fields(data):
    return {
        'art_style': get_text_field(data, 'art_style', '画风', 1000),
        'character_description': get_text_field(data, 'character_description', '人物描述', 1000),
        'pose_description': get_text_field(data, 'pose_description', '姿势描述', 1000),
        'background_description': get_text_field(data, 'background_description', '背景描述', 1000),
        'clothing_description': get_text_field(data, 'clothing_description', '服饰描述', 1000),
        'lighting_description': get_text_field(data, 'lighting_description', '光照描述', 1000),
        'composition_description': get_text_field(data, 'composition_description', '构图描述', 1000),
        'additional_details': get_text_field(data, 'additional_details', '其他细节', 1000),
    }


def generate_image_task(task_id, prompt, width, height, steps, filename, optimize_prompt,
                       art_style, character_description, pose_description, background_description,
                       clothing_description, lighting_description, composition_description,
                       additional_details, optimization_mode):
    """
    后台图片生成任务
    """
    pipe_acquired = False
    saved_image_path = None

    def update_task(**changes):
        if not task_manager.update(task_id, **changes):
            raise GenerationCancelled()

    def cleanup_cancelled_output():
        if not saved_image_path:
            return
        gallery_dir = Path(config_manager.get("gallery_dir", "gallery")).resolve()
        folder = Path(saved_image_path).resolve().parent
        if folder != gallery_dir and folder.is_relative_to(gallery_dir) and folder.exists():
            shutil.rmtree(folder)

    try:
        task_manager.raise_if_cancelled(task_id)
        pipe = model_manager.acquire_pipe_for_inference()
        if not pipe:
            task_manager.fail(task_id, '模型已卸载，请重新加载模型')
            return
        pipe_acquired = True

        task_manager.raise_if_cancelled(task_id)

        # 如果启用提示词优化
        if optimize_prompt:
            update_task(status='optimizing', progress=5, stage='正在优化提示词...')

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
            task_manager.raise_if_cancelled(task_id)
            update_task(status='pending', progress=10, stage='提示词优化完成，准备生成...')

        filename = validate_file_extension(filename)

        print(f"🔄 [任务 {task_id}] 开始生成图片: {prompt}")
        start_time = time.time()

        # 生成图片
        def progress_callback(pipe, step, timestep, callback_kwargs):
            task_manager.raise_if_cancelled(task_id)
            progress_percent = 20 + int((step + 1) / steps * 70)
            update_task(
                status='generating',
                progress=min(progress_percent, 90),
                stage=f'生成中: {step + 1}/{steps} 步',
            )

            print(f"  生成进度: {step + 1}/{steps} 步 ({progress_percent}%)")
            return callback_kwargs

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
        print(f"🎨 [任务 {task_id}] 开始图片生成...")

        update_task(status='preparing', progress=15, stage='准备生成...')
        task_manager.raise_if_cancelled(task_id)

        image = pipe(
            **generation_params,
            callback_on_step_end=progress_callback,
        ).images[0]
        task_manager.raise_if_cancelled(task_id)
        print(f"✅ [任务 {task_id}] 图片生成完成")

        # 推理结束后立即释放模型锁，保存图片无需继续占用 GPU 管线。
        model_manager.release_pipe_after_inference()
        pipe_acquired = False

        gen_time = time.time() - start_time
        print(f"⏱️ [任务 {task_id}] 生成耗时: {gen_time:.2f}秒")

        # 保存图片到画廊
        try:
            save_start = time.time()
            print(f"💾 [任务 {task_id}] 调用 save_to_gallery...")

            update_task(status='saving', progress=95, stage='正在保存图片...')

            saved_image_path = save_to_gallery(
                image, filename, prompt, width, height, steps,
                gen_time, optimization_mode,
                cancellation_check=lambda: task_manager.raise_if_cancelled(task_id),
            )
            invalidate_gallery_cache()
            task_manager.raise_if_cancelled(task_id)
            save_duration = time.time() - save_start
            print(f"💾 [任务 {task_id}] 图片保存完成，耗时: {save_duration:.2f}秒")
        except GenerationCancelled:
            raise
        except Exception as save_error:
            print(f"❌ [任务 {task_id}] 保存图片失败: {save_error}")
            import traceback
            traceback.print_exc()
            raise Exception(f"保存图片失败: {str(save_error)}")

        # 构建文件路径和URL
        print(f"🔗 [任务 {task_id}] 构建文件路径...")
        file_path = Path(saved_image_path)
        gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
        relative_path = file_path.resolve().relative_to(gallery_dir.resolve())
        image_url = f"/gallery/{quote(relative_path.as_posix(), safe='/')}"

        # 任务完成
        print(f"🎉 [任务 {task_id}] 全部完成！")
        update_task(
            status='completed',
            progress=100,
            stage='生成完成',
            image_url=image_url,
            file_path=str(file_path),
            prompt=prompt,
            message=f"✅ 图片已保存到: {file_path}\n⏱️ 生成时间: {gen_time:.2f}秒",
            gen_time=gen_time,
        )

        print(f"✅ [任务 {task_id}] 任务已完成")

    except GenerationCancelled:
        cleanup_cancelled_output()
        print(f"🚫 [任务 {task_id}] 任务已取消，工作线程已退出")
    except Exception as e:
        if task_manager.is_cancelled(task_id):
            cleanup_cancelled_output()
            return

        import traceback
        error_msg = f"❌ 生成失败: {str(e)}"
        if "out of memory" in str(e).lower():
            error_msg += "\n💡 检测到显存不足,请尝试使用低显存优化模式"

        # 打印完整的错误堆栈以便调试
        print(f"❌ [任务 {task_id}] 生成失败: {e}")
        print("完整错误堆栈:")
        traceback.print_exc()

        task_manager.fail(task_id, error_msg)
    finally:
        if pipe_acquired:
            model_manager.release_pipe_after_inference()
        task_manager.finish_worker(task_id)


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/gallery')
def gallery():
    """画廊页面"""
    gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
    try:
        requested_page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        requested_page = 1
    page = max(1, requested_page)
    page_size = validate_integer(
        '画廊分页大小', config_manager.get('gallery_page_size', 24), 6, 60
    )

    folders = get_gallery_folders(gallery_dir)
    total_images = len(folders)
    total_pages = max(1, math.ceil(total_images / page_size))
    page = min(page, total_pages)
    start = (page - 1) * page_size
    visible_folders = folders[start:start + page_size]
    images = []
    for image_folder in visible_folders:
        image_files = (
            list(image_folder.glob('*.png'))
            + list(image_folder.glob('*.jpg'))
            + list(image_folder.glob('*.jpeg'))
        )
        if not image_files:
            continue
        image_file = image_files[0]
        info_file = image_folder / f"{image_file.stem}_info.txt"
        info = {}
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        info[key] = value

        relative_path = image_file.relative_to(gallery_dir)
        images.append({
            'name': image_file.name,
            'folder': image_folder.name,
            'path': f"/gallery/{quote(relative_path.as_posix(), safe='/')}",
            'info': info,
        })

    return render_template(
        'gallery.html',
        images=images,
        total_images=total_images,
        page=page,
        total_pages=total_pages,
    )


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
        'default_filename': config_manager.get("default_filename"),
        'default_optimization_mode': config_manager.get("default_optimization_mode", "basic")
    })


@app.route('/api/load-model', methods=['POST'])
def api_load_model():
    """加载模型"""
    try:
        data = get_json_object()
        optimization_mode = normalize_optimization_mode(data.get('optimization_mode', 'basic'))
        success, message = load_model(
            optimization_mode=optimization_mode,
            model_path=config_manager.get("model_path")
        )

        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 409
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"加载模型失败: {str(e)}"
        }), 500


@app.route('/api/unload-model', methods=['POST'])
def api_unload_model():
    """卸载模型"""
    try:
        success, message = unload_model()

        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 409
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"卸载模型失败: {str(e)}"
        }), 500


@app.route('/api/optimize-prompt', methods=['POST'])
def api_optimize_prompt():
    """
    优化提示词 API
    接收用户输入和优化参数,返回优化后的提示词
    """
    try:
        data = get_json_object()

        prompt = get_text_field(data, 'prompt', '提示词', 4000, required=True)
        fields = get_prompt_fields(data)

        # 调用优化函数
        optimized_prompt = optimize_with_custom_input(
            prompt,
            art_style=fields['art_style'],
            character=fields['character_description'],
            pose=fields['pose_description'],
            background=fields['background_description'],
            clothing=fields['clothing_description'],
            lighting=fields['lighting_description'],
            composition=fields['composition_description'],
            details=fields['additional_details']
        )

        return jsonify({
            'success': True,
            'optimized_prompt': optimized_prompt,
            'message': '提示词优化成功'
        })

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'优化失败: {str(e)}'
        }), 500


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    生成图片 API - 启动后台任务
    """
    try:
        data = get_json_object()

        # 检查模型是否已加载
        if not is_model_loaded():
            return jsonify({
                'success': False,
                'message': '请先加载模型'
            }), 409

        prompt = get_text_field(data, 'prompt', '提示词', 4000, required=True)
        width = validate_integer('宽度', data.get('width', 1024), 256, 4096, multiple_of=64)
        height = validate_integer('高度', data.get('height', 1024), 256, 4096, multiple_of=64)
        steps = validate_integer('生成步数', data.get('steps', 9), 4, 20)
        filename = validate_file_extension(data.get('filename', 'generated_image.png'))
        optimize_prompt = data.get('optimize_prompt', False)
        if not isinstance(optimize_prompt, bool):
            raise ValueError('是否优化提示词必须是布尔值')
        requested_mode = normalize_optimization_mode(data.get('optimization_mode', 'basic'))
        optimization_mode = model_manager.get_optimization_mode()
        if optimization_mode != requested_mode:
            return jsonify({
                'success': False,
                'message': '优化模式已更改，请按当前模式重新加载模型',
            }), 409
        fields = get_prompt_fields(data)

        task_id, active_task_id = task_manager.create_task()
        if task_id is None:
            return jsonify({
                'success': False,
                'message': '已有生成任务正在运行，请等待完成或先取消该任务',
                'task_id': active_task_id,
            }), 409

        # 启动后台线程生成图片
        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, width, height, steps, filename, optimize_prompt,
                  fields['art_style'], fields['character_description'], fields['pose_description'],
                  fields['background_description'], fields['clothing_description'],
                  fields['lighting_description'], fields['composition_description'],
                  fields['additional_details'], optimization_mode)
        )
        thread.daemon = True
        try:
            thread.start()
        except Exception:
            task_manager.fail(task_id, '无法启动生成工作线程')
            task_manager.finish_worker(task_id)
            raise

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '生成任务已启动'
        }), 202

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动生成任务失败: {str(e)}'
        }), 500


@app.route('/api/generate/progress/<task_id>')
def api_generate_progress(task_id):
    """
    查询生成任务进度
    """
    task = task_manager.get(task_id)
    if task is None:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        }), 404

    return jsonify({
        'success': True,
        'status': task.get('status', 'pending'),
        'progress': task.get('progress', 0),
        'stage': task.get('stage', ''),
        'image_url': task.get('image_url'),
        'message': task.get('message'),
        'file_path': task.get('file_path'),
        'prompt': task.get('prompt')
    })


@app.route('/api/generate/cancel', methods=['POST'])
def api_generate_cancel():
    """
    取消生成任务
    """
    try:
        data = get_json_object()
        task_id = get_text_field(data, 'task_id', '任务ID', 64, required=True)

        success, message = task_manager.cancel(task_id)
        if not success:
            status_code = 404 if message == '任务不存在' else 409
            return jsonify({'success': False, 'message': message}), status_code

        return jsonify({
            'success': True,
            'message': message
        })

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'取消任务失败: {str(e)}'
        }), 500


# ==================== 删除图片 API ====================

@app.route('/api/gallery/delete', methods=['POST'])
def api_delete_gallery_item():
    """
    删除画廊图片及其信息文档
    """
    try:
        data = get_json_object()
        folder_name = get_text_field(data, 'folder_name', '文件夹名称', 255, required=True)
        if folder_name in {'.', '..'} or '/' in folder_name or '\\' in folder_name:
            raise ValueError('文件夹名称无效')

        gallery_dir = Path(config_manager.get("gallery_dir", "gallery"))
        folder_path = gallery_dir / folder_name

        if not folder_path.exists():
            return jsonify({
                'success': False,
                'message': '图片文件夹不存在'
            }), 404

        # 安全检查:确保路径在gallery目录内
        folder_path_resolved = folder_path.resolve()
        gallery_dir_resolved = gallery_dir.resolve()

        if not folder_path_resolved.is_relative_to(gallery_dir_resolved):
            return jsonify({
                'success': False,
                'message': '无效的路径'
            }), 400

        # 删除整个文件夹
        import shutil
        shutil.rmtree(folder_path)
        invalidate_gallery_cache()

        return jsonify({
            'success': True,
            'message': f'已删除: {folder_name}'
        })

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 静态文件服务 ====================

@app.route('/gallery/thumbnail/<path:folder_name>')
def serve_gallery_thumbnail(folder_name):
    """按需生成并长期缓存画廊缩略图，兼容已有作品。"""
    gallery_dir = Path(config_manager.get("gallery_dir", "gallery")).resolve()
    folder = (gallery_dir / folder_name).resolve()
    if folder.parent != gallery_dir or not folder.is_dir():
        return jsonify({'error': 'Invalid gallery item'}), 404

    image_files = list(folder.glob('*.png')) + list(folder.glob('*.jpg')) + list(folder.glob('*.jpeg'))
    if not image_files:
        return jsonify({'error': 'Image not found'}), 404
    image_path = image_files[0]
    thumbnail_path = get_thumbnail_path(image_path)
    if not thumbnail_path.exists():
        with thumbnail_lock:
            if not thumbnail_path.exists():
                try:
                    create_gallery_thumbnail(image_path, image_path)
                except Exception as error:
                    print(f"⚠️ 无法生成缩略图 {image_path}: {error}")
                    return send_file(str(image_path), conditional=True, max_age=3600)

    return send_file(
        str(thumbnail_path),
        mimetype='image/webp',
        conditional=True,
        max_age=31536000,
    )

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
        if requested_path.suffix.lower() == '.png':
            mimetype = 'image/png'
        elif requested_path.suffix.lower() in ['.jpg', '.jpeg']:
            mimetype = 'image/jpeg'

        return send_file(
            str(requested_path),
            mimetype=mimetype,
            conditional=True,
            max_age=31536000,
        )
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
    host = config_manager.get("flask_host", "127.0.0.1")
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
