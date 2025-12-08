# Render 快速部署指南

## 方法一：使用 Blueprint（推荐）✅

### 步骤
1. 访问 [Render](https://render.com) 并登录
2. 点击 "New+" → "Blueprint"
3. 连接你的 GitHub 账户
4. 选择 `xianyu110/z-image` 仓库
5. 点击 "Apply" 开始部署

### 部署结果
- 单个服务同时提供前端和后端
- 访问地址：`https://z-image-unified.onrender.com`
- 内置 keep-alive 防止休眠

## 方法二：手动创建 Web Service

### 1. 创建新服务
- 登录 Render 控制台
- 点击 "New+" → "Web Service"
- 连接 GitHub 仓库 `xianyu110/z-image`

### 2. 配置服务
- **Name**: `z-image-api`（或其他名称）
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python zimage_proxy_unified.py`

### 3. 设置环境变量
```
PORT = 8000
PYTHONUNBUFFERED = true
ZIMAGE_API_HOST = https://zimage.run
ENABLE_KEEP_ALIVE = true
DEBUG = false
```

### 4. 高级设置
- **Health Check Path**: `/health`
- **Auto-Deploy**: 启用（推荐）

## 部署文件说明

### render.yaml（默认）
- 使用 `zimage_proxy_unified.py`
- 单服务部署（前端+后端）
- 适合免费计划

### render_simple.yaml
- 仅部署后端 API
- 需要单独部署前端

### render_single.yaml
- 与 render.yaml 相同
- 另一个命名版本

## 部署后配置

### 1. 更新前端 API 地址（如果需要）
如果前端默认 API 地址不正确，编辑 `web/script.js`：
```javascript
const API_CONFIG = {
    baseUrl: 'https://你的服务名.onrender.com',
    // ...
};
```

### 2. 验证部署
```bash
# 检查健康状态
curl https://你的服务名.onrender.com/health

# 测试 API
curl -X POST https://你的服务名.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"a cat"}]}'
```

## Keep-Alive 配置

服务已内置 keep-alive 功能：
- 每10分钟自动 ping 健康端点
- 通过 `ENABLE_KEEP_ALIVE=true` 控制
- 日志显示：`"Keep-alive ping sent"`

额外的保障方案：
- **GitHub Actions**: `.github/workflows/keep-alive.yml`
- **外部监控**: Uptime Robot（免费）

## 故障排除

### 1. 部署失败
- 检查构建日志
- 确认 `requirements.txt` 包含所有依赖
- 查看是否有语法错误

### 2. 前端无法访问
- 确认使用了 `zimage_proxy_unified.py`
- 检查 `web/` 目录是���包含前端文件

### 3. API 不工作
- 检查环境变量设置
- 查看 Render 日志
- 测试健康检查端点

### 4. 服务休眠
- 确认 `ENABLE_KEEP_ALIVE=true`
- 检查 keep-alive 日志
- 考虑使用 GitHub Actions

## 访问地址示例

部署成功后，你的服务地址格式：
- `https://z-image-unified.onrender.com`
- `https://你的服务名.onrender.com`

## 成本说明

### 免费计划限制
- 750 小时/月（约25天/月）
- 15分钟无活动休眠
- 512MB RAM
- 共享 CPU

### 优化建议
- 使用统一服务减少资源使用
- 启用 keep-alive 避免冷启动
- 监控使用时间避免超限

## 下一步

1. 部署服务
2. 测试图片生成功能
3. 设置域名（可选）
4. 配置监控（推荐）