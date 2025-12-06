"""
依赖检查脚本
检查并更新必要的依赖包
"""

import subprocess
import sys
import importlib

def check_requirements():
    """检查依赖包版本"""
    requirements = {
        "torch": "2.0.0",
        "diffusers": "0.21.0", 
        "gradio": "3.0.0",
        "pillow": "9.0.0"
    }
    
    print("🔍 检查依赖包版本...")
    
    for package, min_version in requirements.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {package}: {version}")
            
        except ImportError:
            print(f"❌ {package}: 未安装")
            print(f"   建议安装版本: {min_version}+")
            
    print("\n📦 如果需要更新依赖，请运行:")
    print("pip install --upgrade torch diffusers gradio pillow")

if __name__ == "__main__":
    check_requirements()