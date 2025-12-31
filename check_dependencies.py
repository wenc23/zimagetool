"""
依赖检查脚本
检查并更新必要的依赖包，提供系统环境诊断
重构版本 - 使用公共模块
"""

import subprocess
import sys
import importlib
import platform
import os
from pathlib import Path

from utils import (
    print_section, print_success, print_error, print_warning, print_info,
    ensure_directory
)
from config_manager import config_manager


class EnvironmentStatus:
    """环境状态记录类"""
    def __init__(self):
        self.python_ok = False
        self.model_ok = False
        self.deps_ok = False
        self.missing_deps = []
        self.outdated_deps = []
        self.cuda_available = False
        self.os_type = platform.system().lower()


def get_system_info():
    """获取系统信息"""
    print_section("🖥️ 系统环境检查", width=60)
    print_info(f"操作系统: {platform.system()} {platform.release()}")
    print_info(f"Python版本: {platform.python_version()}")
    print_info(f"Python路径: {sys.executable}")

    return platform.system().lower()


def check_cuda_support():
    """检查CUDA支持"""
    try:
        import torch
        if torch.cuda.is_available():
            print_success(f"CUDA可用: {torch.version.cuda}")
            print_info(f"GPU设备: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print_warning("CUDA不可用 - 将使用CPU模式")
            return False
    except ImportError:
        print_error("PyTorch未安装 - 无法检查CUDA")
        return False


def check_python_version():
    """检查Python版本"""
    python_version = platform.python_version_tuple()
    major, minor = int(python_version[0]), int(python_version[1])

    if major >= 3 and minor >= 8:
        print_success(f"Python版本: {platform.python_version()} (符合要求)")
        return True
    else:
        print_error(f"Python版本: {platform.python_version()} (需要3.8+)")
        return False


def check_model_files():
    """检查模型文件是否存在"""
    model_path = Path(config_manager.get("model_path", "models/Z-Image-Turbo"))
    required_files = [
        "model_index.json",
        "scheduler/scheduler_config.json",
        "text_encoder/config.json",
        "transformer/config.json",
        "vae/config.json"
    ]

    print_section("📁 检查模型文件", width=60)
    if model_path.exists():
        print_success(f"模型目录存在: {model_path}")

        missing_files = []
        for file in required_files:
            file_path = model_path / file
            if not file_path.exists():
                missing_files.append(file)

        if missing_files:
            print_error(f"缺少关键模型文件: {', '.join(missing_files)}")
            return False
        else:
            print_success("所有关键模型文件都存在")
            return True
    else:
        print_error(f"模型目录不存在: {model_path}")
        return False


def check_pillow_specifically():
    """专门检查Pillow库的安装情况"""
    try:
        # 尝试多种导入方式
        import PIL
        # Pillow库的版本信息可能在多个属性中
        version = getattr(PIL, "__version__",
                         getattr(PIL, "PILLOW_VERSION",
                                getattr(PIL, "VERSION", "unknown")))

        if version != "unknown":
            # 检查版本是否满足要求
            min_version = "9.0.0"
            try:
                current_parts = [int(x) for x in version.split('.') if x.isdigit()]
                min_parts = [int(x) for x in min_version.split('.') if x.isdigit()]

                if current_parts >= min_parts:
                    return True, version
                else:
                    return False, version
            except ValueError:
                # 版本格式解析失败，但已安装
                return True, version
        else:
            # 版本未知但已安装
            return True, "unknown"

    except ImportError:
        return False, "未安装"


def check_requirements(status):
    """检查依赖包版本"""
    requirements = {
        "torch": "2.9.0+cu126",
        "diffusers": "0.36.0.dev0",
        "gradio": "6.0.2",
        "transformers": "4.57.3",
        "accelerate": "1.12.0",
        "requests": "2.32.5"
    }

    print_section("🔍 检查依赖包版本", width=60)

    all_passed = True

    # 先检查Pillow库（特殊处理）
    pillow_ok, pillow_version = check_pillow_specifically()
    if pillow_ok:
        if pillow_version != "unknown":
            print_success(f"PIL: {pillow_version}")
        else:
            print_success("PIL: 已安装 (版本未知)")
    else:
        print_error(f"PIL: {pillow_version}")
        status.missing_deps.append(("PIL", "9.0.0"))
        all_passed = False

    # 检查其他依赖包
    for package, min_version in requirements.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")

            # 简单的版本比较
            if version != "unknown":
                try:
                    current_parts = [int(x) for x in version.split('.') if x.isdigit()]
                    min_parts = [int(x) for x in min_version.split('.') if x.isdigit()]

                    if current_parts >= min_parts:
                        print_success(f"{package}: {version}")
                    else:
                        print_warning(f"{package}: {version} (需要{min_version}+)")
                        status.outdated_deps.append((package, min_version))
                        all_passed = False
                except ValueError:
                    # 版本格式解析失败，但已安装
                    print_success(f"{package}: {version}")
            else:
                print_success(f"{package}: 已安装 (版本未知)")

        except ImportError:
            print_error(f"{package}: 未安装")
            status.missing_deps.append((package, min_version))
            all_passed = False

    status.deps_ok = all_passed
    return all_passed


def check_optional_dependencies():
    """检查可选依赖包"""
    optional_deps = {
        "aiofiles": "Web UI文件处理",
        "colorama": "终端颜色输出",
        "huggingface_hub": "模型下载"
    }

    print_section("🔍 检查可选依赖包", width=60)

    missing_optional = []
    for package, description in optional_deps.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print_success(f"{package}: {version} ({description})")
        except ImportError:
            print_warning(f"{package}: 未安装 ({description})")
            missing_optional.append(package)

    return missing_optional


def check_deepseek_api():
    """检查DeepSeek API配置"""
    print_section("🔑 检查DeepSeek API配置", width=60)

    api_key = config_manager.get("deepseek_api_key") or os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        print_success("DeepSeek API密钥已配置")
        print_info(f"密钥长度: {len(api_key)} 字符")
        return True
    else:
        print_warning("DeepSeek API密钥未配置")
        print_info("提示词优化功能将使用本地优化器")
        return False


def suggest_installation_commands(status):
    """根据具体问题提供针对性的安装建议"""
    print_section("📦 针对性安装建议", width=60)

    # 根据操作系统提供不同的命令
    if status.os_type == "windows":
        pip_cmd = "pip"
        env_set_cmd = 'setx DEEPSEEK_API_KEY "your_api_key_here"'
    else:
        pip_cmd = "pip3" if "linux" in status.os_type or "darwin" in status.os_type else "pip"
        env_set_cmd = 'export DEEPSEEK_API_KEY="your_api_key_here"'

    suggestions = []

    # 1. Python版本问题
    if not status.python_ok:
        suggestions.append(("🔧 1. 解决Python版本问题:", [
            "请安装Python 3.8或更高版本",
            "下载地址: https://www.python.org/downloads/"
        ]))

    # 2. 模型文件问题
    if not status.model_ok:
        suggestions.append(("🔧 2. 解决模型文件问题:", [
            "下载模型文件:",
            "git clone https://huggingface.co/Tongyi-MAI/Z-Image-Turbo models/Z-Image-Turbo",
            "或者使用huggingface_hub下载:",
            f"{pip_cmd} install huggingface_hub",
            "python -c \"from huggingface_hub import snapshot_download; snapshot_download(repo_id='Tongyi-MAI/Z-Image-Turbo', local_dir='models/Z-Image-Turbo')\""
        ]))

    # 3. 依赖包问题
    if status.missing_deps or status.outdated_deps:
        deps_suggestions = []

        # 缺失的依赖包（处理PIL包名映射）
        if status.missing_deps:
            missing_packages = []
            for pkg, _ in status.missing_deps:
                if pkg == "PIL":
                    missing_packages.append("pillow")  # 安装时使用pillow包名
                else:
                    missing_packages.append(pkg)

            if missing_packages:
                deps_suggestions.append(f"缺失的包: {', '.join(missing_packages)}")
                deps_suggestions.append(f"安装命令: {pip_cmd} install {' '.join(missing_packages)}")

        # 版本过旧的依赖包（处理PIL包名映射）
        if status.outdated_deps:
            outdated_packages = []
            for pkg, _ in status.outdated_deps:
                if pkg == "PIL":
                    outdated_packages.append("pillow")  # 更新时使用pillow包名
                else:
                    outdated_packages.append(pkg)

            if outdated_packages:
                deps_suggestions.append(f"需要更新的包: {', '.join(outdated_packages)}")
                deps_suggestions.append(f"更新命令: {pip_cmd} install --upgrade {' '.join(outdated_packages)}")

        if deps_suggestions:
            suggestions.append(("🔧 3. 解决依赖包问题:", deps_suggestions))

    # 4. PyTorch特殊处理（仅在确实需要时显示）
    if any(pkg == "torch" for pkg, _ in status.missing_deps + status.outdated_deps):
        pytorch_suggestions = []
        if status.cuda_available:
            pytorch_suggestions.append("GPU版本 (推荐):")
            pytorch_suggestions.append(f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130")
        else:
            pytorch_suggestions.append("CPU版本:")
            pytorch_suggestions.append(f"{pip_cmd} install torch torchvision torchaudio")

        suggestions.append(("🔧 4. PyTorch安装建议:", pytorch_suggestions))

    # 5. diffusers特殊处理（仅在确实需要时显示）
    if any(pkg == "diffusers" for pkg, _ in status.missing_deps + status.outdated_deps):
        suggestions.append(("🔧 5. diffusers安装建议:", [
            "必须从源码安装以支持Z-Image:",
            f"{pip_cmd} uninstall diffusers",
            f"{pip_cmd} install git+https://github.com/huggingface/diffusers"
        ]))

    # 6. 可选依赖（始终显示，但标记为可选）
    suggestions.append(("🔧 6. 可选依赖 (提升体验):", [
        f"{pip_cmd} install aiofiles colorama huggingface_hub"
    ]))

    # 7. API配置（始终显示）
    suggestions.append(("🔧 7. DeepSeek API配置:", [
        "设置环境变量:",
        f"{env_set_cmd}",
        "或者直接在代码中设置:",
        "import os",
        'os.environ["DEEPSEEK_API_KEY"] = "your_api_key_here"'
    ]))

    # 8. 一键安装命令（仅在需要时显示）
    if status.missing_deps or status.outdated_deps or not status.model_ok:
        suggestions.append(("🔧 8. 一键安装所有依赖:", [
            f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130" if status.os_type == "windows" else f"{pip_cmd} install torch torchvision torchaudio",
            f"{pip_cmd} install --upgrade git+https://github.com/huggingface/diffusers transformers accelerate",
            f"{pip_cmd} install gradio pillow requests aiofiles colorama huggingface_hub"
        ]))

    # 按优先级显示建议
    for i, (title, items) in enumerate(suggestions, 1):
        print_info(title)
        for item in items:
            print(f"   {item}")
        if i < len(suggestions):  # 不在最后一个建议后添加空行
            print()


def check_environment():
    """综合环境检查"""
    status = EnvironmentStatus()

    print_section("🎯 Z-Image-Turbo 环境检查", width=60)

    # 检查系统信息
    status.os_type = get_system_info()

    # 检查CUDA支持
    status.cuda_available = check_cuda_support()

    # 检查Python版本
    status.python_ok = check_python_version()

    # 检查模型文件
    status.model_ok = check_model_files()

    # 检查依赖包
    check_requirements(status)

    # 检查可选依赖
    missing_optional = check_optional_dependencies()

    # 检查API配置
    api_configured = check_deepseek_api()

    # 总体评估
    print_section("📊 环境检查总结", width=60)
    if status.python_ok and status.model_ok and status.deps_ok:
        print_success("环境配置完整，可以正常运行!")
        if missing_optional:
            print_info("可选依赖未安装，但不影响基本功能")
        if not api_configured:
            print_info("DeepSeek API未配置，提示词优化使用本地模式")
    else:
        print_error("环境配置不完整，请根据以下提示进行修复")
        suggest_installation_commands(status)


def auto_fix_dependencies():
    """自动修复依赖问题"""
    print_section("🛠️ 尝试自动修复依赖", width=60)

    status = EnvironmentStatus()
    status.os_type = platform.system().lower()

    try:
        # 检查当前状态
        check_requirements(status)

        # 根据操作系统选择命令
        pip_cmd = "pip" if status.os_type == "windows" else "pip3"

        # 安装基础依赖
        commands = [
            f"{pip_cmd} install --upgrade pip",
        ]

        # 根据缺失的包添加特定命令（处理PIL包名映射）
        missing_packages = []
        for pkg, _ in status.missing_deps:
            if pkg == "PIL":
                missing_packages.append("pillow")
            else:
                missing_packages.append(pkg)

        if missing_packages:
            commands.append(f"{pip_cmd} install {' '.join(missing_packages)}")

        # 特殊处理PyTorch
        if "torch" in [pkg for pkg, _ in status.missing_deps]:
            if status.os_type == "windows":
                commands.append(f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130")
            else:
                commands.append(f"{pip_cmd} install torch torchvision torchaudio")

        # 特殊处理diffusers
        if "diffusers" in [pkg for pkg, _ in status.missing_deps]:
            commands.append(f"{pip_cmd} uninstall diffusers")
            commands.append(f"{pip_cmd} install git+https://github.com/huggingface/diffusers")

        # 安装可选依赖
        commands.append(f"{pip_cmd} install aiofiles colorama huggingface_hub")

        for cmd in commands:
            print_info(f"执行: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print_success("执行成功")
            else:
                print_error(f"执行失败: {result.stderr}")

    except Exception as e:
        print_error(f"自动修复失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        auto_fix_dependencies()
    else:
        check_environment()