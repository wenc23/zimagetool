# Z-Image-Turbo 图片生成器

一个基于 Z-Image-Turbo 模型的本地图片生成工具，支持中英文双语提示词和多种优化模式。

## 🚀 特性

- **高效生成**: 基于 Z-Image-Turbo 模型，仅需 8 步推理即可生成高质量图片
- **双语支持**: 完美支持中英文提示词，准确渲染双语文字
- **显存优化**: 提供多种优化模式，支持低显存设备运行
- **交互式界面**: 友好的命令行交互界面，易于使用
- **图片管理**: 自动保存生成图片到画廊，包含元数据记录

## 📋 系统要求

### 硬件要求
- **GPU**: NVIDIA GPU (推荐 RTX 3060 或更高)
- **显存**: 最低 8GB，推荐 16GB 或更高
- **内存**: 最低 16GB，推荐 32GB

### 软件要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8 或更高版本
- **CUDA**: 11.8 或更高版本 (如使用 NVIDIA GPU)

## 🔧 安装步骤

### 1. 克隆项目
```bash
git clone <你的项目地址>
cd image
```

### 2. 下载模型
```bash
cd models
git clone https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
cd ..
```

### 3. 安装依赖
```bash
# 安装 PyTorch (CUDA 版本)
pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu130

# 安装最新版 diffusers (必须从源码安装以支持 Z-Image)
pip install --upgrade git+https://github.com/huggingface/diffusers transformers accelerate
```

### 4. 验证安装
```bash
python -c "import diffusers; print(f'diffusers版本: {diffusers.__version__}')"
```

## 🎮 使用方法

### 基本使用
```bash
python main.py
```

### 程序流程
1. **选择优化模式**: 程序启动后会让你选择优化模式
   - 基础模式: 平衡性能和显存使用
   - 低显存模式: 适合显存较小的设备

2. **输入生成参数**:
   - 提示词 (支持中英文)
   - 图片尺寸 (默认 1024x1024)
   - 推理步数 (默认 9 步)
   - 文件名

3. **生成图片**: 程序会自动生成并保存图片

### 示例提示词
- **中文**: "一位穿着红色汉服的年轻中国女子，精致的刺绣，完美的妆容"
- **英文**: "A beautiful landscape with mountains, lakes, and sunset, photorealistic"


## ⚡ 优化模式说明

### 基础模式
- 使用平衡设备映射
- 启用注意力切片
- 适合显存充足的设备

### 低显存模式
- 启用 CPU 卸载
- 更激进的显存优化
- 适合显存有限的设备

## 🛠️ 故障排除

### 常见问题

**1. 导入错误: `cannot import name 'ZImagePipeline'`**
```bash
# 解决方案: 重新安装最新版 diffusers
pip uninstall diffusers
pip install git+https://github.com/huggingface/diffusers
```

**2. 显存不足错误**
- 选择"低显存模式"
- 减小图片尺寸 (如 768x768)
- 关闭其他占用显存的程序

**3. 模型加载失败**
- 检查模型路径: `models/Z-Image-Turbo` 是否存在
- 重新下载模型文件

## 📊 性能指标

| 配置 | 生成时间 | 显存占用 | 图片质量 |
|------|----------|----------|----------|
| 1024x1024, 9步 | ~15-30秒 | 12-16GB | 优秀 |
| 768x768, 9步 | ~8-15秒 | 8-12GB | 良好 |
| 低显存模式 | ~20-40秒 | 6-10GB | 良好 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目基于 Apache 2.0 许可证开源。

## 🙏 致谢

- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) - 强大的图片生成模型
- [Hugging Face](https://huggingface.co) - 提供的模型和工具
- [Diffusers](https://github.com/huggingface/diffusers) - 优秀的扩散模型库

## 📞 支持

如果遇到问题，请：
1. 查看本 README 的故障排除部分
2. 检查模型文件是否完整下载
3. 确认依赖包版本正确

---

**享受创作的乐趣！** 🎨