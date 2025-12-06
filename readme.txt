# Z-Image-Turbo 图片生成器 - 快速开始指南

## 快速安装

1. 下载模型:
```bash
cd models
git clone https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
cd ..
```

2. 安装依赖:
```bash
pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu130
pip install --upgrade git+https://github.com/huggingface/diffusers transformers accelerate
```

3. 运行程序:
```bash
python main.py
```

## 重要提示

- 必须从源码安装 diffusers 以支持 Z-Image-Turbo
- 首次运行需要加载模型，请耐心等待
- 推荐使用 NVIDIA GPU 以获得最佳性能

## 故障排除

如果遇到导入错误，请运行:
```bash
pip uninstall diffusers
pip install git+https://github.com/huggingface/diffusers
```

详细说明请查看 README.md 文件。