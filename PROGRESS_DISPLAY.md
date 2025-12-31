# 进度显示说明

## 进度阶段划分

### 后端进度更新（flask_app.py）

| 进度 | 阶段 | 说明 |
|------|------|------|
| 0% | 准备中... | 任务创建，等待开始 |
| 10% | 优化提示词... | 正在优化提示词 |
| 30% | 生成图片中... | 准备生成图片 |
| 40% | 生成中... | 开始生成 |
| 40-90% | 生成中: X/Y 步 | 实时显示推理步骤 |
| 95% | 保存图片... | 保存到画廊 |
| 100% | 完成！ | 任务完成 |

### 前端轮询机制
- **轮询间隔**: 500ms (每0.5秒查询一次)
- **实时更新**: 进度条宽度、百分比文字、阶段描述
- **显示位置**:
  - 进度条内：百分比
  - 进度条下方：阶段描述 + 百分比

## 进度回调函数

```python
def progress_callback(pipe, step, timestep, callback_kwargs):
    """
    步骤结束时的回调函数
    参数：
    - pipe: pipeline实例
    - step: 当前步骤 (0-based)
    - timestep: 时间步
    - callback_kwargs: 包含latents等信息的字典
    """
    progress = 40 + int((step + 1) / steps * 50)
    generation_tasks[task_id]['progress'] = progress
    generation_tasks[task_id]['stage'] = f'生成中: {step + 1}/{steps} 步'
```

## 前端更新方法

```javascript
updateProgress(progress, stage) {
    progressBar.style.width = `${progress}%`;
    progressTextOverlay.textContent = `${progress}%`;
    progressPercentage.textContent = `${progress}%`;
    progressStage.textContent = stage;
    loadingSubtext.textContent = stage;
}
```

## 示例进度流程（9步生成）

```
0%   → 准备中...
10%  → 优化提示词...
30%  → 生成图片中...
40%  → 生成中...
45%  → 生成中: 1/9 步
50%  → 生成中: 2/9 步
55%  → 生成中: 3/9 步
60%  → 生成中: 4/9 步
65%  → 生成中: 5/9 步
70%  → 生成中: 6/9 步
75%  → 生成中: 7/9 步
80%  → 生成中: 8/9 步
85%  → 生成中: 9/9 步
90%  → 生成中: 9/9 步
95%  → 保存图片...
100% → 完成！
```

## 修复记录

### 问题1: Callback 导入错误
**错误**: `cannot import name 'Callback' from 'diffusers'`

**原因**: diffusers 库中没有 Callback 类

**解决**: 直接定义回调函数，不使用类
```python
def progress_callback(pipe, step, timestep, callback_kwargs):
    # 回调逻辑
```

### 问题2: 回调参数错误
**错误**: `progress_callback() takes 3 positional arguments but 4 were given`

**原因**: 回调函数定义不正确

**解决**: 确保函数签名正确：`(step, timestep, latents)`

### 问题3: 进度显示不一致
**问题**: 加载遮罩显示"准备中..."，但后端实际阶段不同

**解决**:
1. 统一所有进度阶段文本
2. 前端初始化时使用传入的 subtext 参数
3. 确保后端阶段文本与前端显示一致

## 技术要点

1. **实时进度**: 使用 diffusers 的 `callback_on_step_end` 参数
2. **进度计算**: 40%起始 + 50%范围分配给各步骤
3. **线程安全**: generation_tasks 字典在多线程环境下的使用
4. **前端轮询**: 500ms 间隔查询 `/api/generate/progress/<task_id>`
5. **用户体验**: 进度条带流光动画，显示具体步骤数

## 调试建议

如果进度显示异常，检查：
1. 后端日志中的进度更新
2. 前端浏览器控制台的 API 响应
3. 回调函数是否正常执行
4. 轮询间隔是否合理（500ms）
5. 进度百分比计算是否正确

---

**最后更新**: 2026-01-01
**状态**: ✅ 所有问题已修复，进度显示精准一致
