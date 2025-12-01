# Web 前端测试工具部署指南

Z-Image 图片生成 API 的 Web 前端测试工具，提供直观的用户界面来测试和调用图片生成功能。

## 📋 功能特性

### 🎨 核心功能
- **可视化图片生成** - 通过 Web 界面生成图片
- **参数配置** - 实时调整生成参数
- **任务监控** - 实时查看生成进度和状态
- **结果管理** - 图片预览、下载和管理
- **预设提示词** - 快速应用常用提示词

### 🔧 高级功能
- **API 连接测试** - 自动检测 API 服务状态
- **多图片生成** - 支持批量生成（1-4张）
- **实时日志** - 详细的操作日志记录
- **响应式设计** - 支持桌面和移动设备
- **本地存储** - 保存用户设置和提示词

### ⌨️ 快捷操作
- **Ctrl+Enter** - 生成/停止图片
- **Esc** - 停止生成
- **自动保存** - 提示词和设置自动保存

## 🚀 快速开始

### 方法一：使用内置服务器（推荐）

1. **进入 web 目录**
   ```bash
   cd z-image/web
   ```

2. **启动服务器**
   ```bash
   python server.py
   ```

3. **访问应用**
   - 浏览器自动打开 http://localhost:3000
   - 或手动访问该地址

4. **配置 API 地址**
   - 默认: http://localhost:8000
   - 修改为你的实际 API 地址

### 方法二：使用 Python 内置服务器

```bash
# 进入 web 目录
cd z-image/web

# 启动 HTTP 服务器
python -m http.server 3000

# 或者使用 Python 2
python -m SimpleHTTPServer 3000
```

### 方法三：使用 Node.js

```bash
# 安装 http-server
npm install -g http-server

# 进入 web 目录并启动
cd z-image/web
http-server -p 3000
```

### 方法四：直接打开 HTML 文件

```bash
# 直接用浏览器打开
open z-image/web/index.html
```

## 📁 项目结构

```
web/
├── index.html          # 主页面文件
├── styles.css          # 样式文件
├── script.js           # JavaScript 逻辑
├── server.py           # Python HTTP 服务器
└── README.md           # 说明文档
```

## ⚙️ 配置说明

### API 配置
- **API 地址**: http://localhost:8000（默认）
- **健康检查**: /api/health
- **生成端点**: /v1/chat/completions
- **任务查询**: /v1/tasks/{taskId}
- **图片获取**: /v1/images/{taskId}

### 生成参数
| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| 模型 | zimage-turbo/base | turbo | 选择生成模型 |
| 数量 | 1-4 | 1 | 生成图片数量 |
| 宽度 | 512/768/1024/1360 | 1024 | 图片宽度 |
| 高度 | 512/768/1024/1360 | 1024 | 图片高度 |
| 步数 | 1-20 | 8 | 采样步数 |
| 引导强度 | 1-20 | 7 | CFG Scale |

## 🎯 使用指南

### 1. 首次使用
1. 启动前端服务器
2. 测试 API 连接
3. 输入图片描述
4. 点击"生成图片"

### 2. 生成图片
1. **输入描述** - 在"图片描述"框中输入详细描述
2. **设置负面描述** - 输入要避免的内容（可选）
3. **调整参数** - 根据需要调整生成参数
4. **开始生成** - 点击"生成图片"按钮

### 3. 监控进度
- 查看生成状态
- 监控进度条
- 查看已用时间
- 查看操作日志

### 4. 管理结果
- **预览图片** - 点击图片查看大图
- **下载图片** - 单独或批量下载
- **复制链接** - 复制图片 URL
- **清空结果** - 清理当前结果

### 5. 快速操作
- **预设提示词** - 使用预设的提示词模板
- **键盘快捷键** - 使用快捷键提高效率
- **自动保存** - 设置和提示词自动保存

## 🔧 高级配置

### 自定义 API 地址
```javascript
// 在 script.js 中修改 API_CONFIG
const API_CONFIG = {
    baseUrl: 'https://your-api-server.com',
    // ...
};
```

### 自定义端口
```python
# 在 server.py 中修改端口
PORT = 8080  # 修改为你想要的端口
```

### 自定义样式
```css
/* 修改 CSS 变量 */
:root {
    --primary-color: #your-color;
    --bg-primary: #your-bg-color;
    /* ... */
}
```

## 🛠️ 开发指南

### 本地开发
1. **修改文件** - 编辑 HTML/CSS/JS 文件
2. **刷新浏览器** - Ctrl+R 或 Cmd+R 刷新页面
3. **查看控制台** - F12 打开开发者工具

### 调试技巧
- **查看日志** - 在"操作日志"区域查看详细日志
- **浏览器控制台** - F12 查看控制台输出
- **网络面板** - 检查 API 请求和响应

### 扩展功能
- **添加新的预设** - 在 HTML 中添加新的 preset-btn
- **自定义样式** - 修改 CSS 变量和样式
- **添加新功能** - 在 JavaScript 中添加新函数

## 🌐 部署到生产环境

### 1. 使用 Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/z-image/web;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理（如果需要）
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 使用 Apache
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /path/to/z-image/web

    <Directory /path/to/z-image/web>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

### 3. 使用 Docker
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. 使用 Vercel/Netlify
1. 将 web 文件夹推送到 GitHub
2. 在 Vercel/Netlify 中导入项目
3. 配置构建设置和部署

## 🔒 安全注意事项

### 跨域问题
- 前端和后端需要配置 CORS
- 或使用代理服务器转发请求

### API 认证
- 如果 API 需要认证，在请求头中添加认证信息
- 考虑使用 HTTPS 加密传输

### 输入验证
- 前端已包含基本输入验证
- 后端也应进行参数验证

## 🐛 故障排除

### 常见问题

#### 1. 无法连接到 API
- 检查 API 服务是否运行
- 确认 API 地址正确
- 检查防火墙设置

#### 2. 图片生成失败
- 检查提示词是否有效
- 确认参数设置合理
- 查看详细错误日志

#### 3. 页面无法加载
- 确认服务器已启动
- 检查端口是否被占用
- 查看浏览器控制台错误

#### 4. 样式显示异常
- 清除浏览器缓存
- 确认 CSS 文件加载成功
- 检查浏览器兼容性

### 调试步骤
1. **检查网络连接** - 使用浏览器开发者工具
2. **查看 API 响应** - 检查 HTTP 状态码和响应体
3. **查看控制台错误** - 检查 JavaScript 错误
4. **测试 API 独立性** - 使用 curl 测试 API

## 📊 性能优化

### 前端优化
- **图片懒加载** - 延迟加载图片
- **缓存策略** - 设置适当的缓存头
- **资源压缩** - 压缩 CSS/JS 文件
- **CDN 加速** - 使用 CDN 分发资源

### API 优化
- **请求去重** - 避免重复请求
- **结果缓存** - 缓存生成结果
- **并发控制** - 限制并发请求数量

## 📱 移动端适配

### 响应式设计
- 自动适配不同屏幕尺寸
- 触摸友好的界面设计
- 优化的移动端交互

### 性能考虑
- 减少资源大小
- 优化图片加载
- 使用现代浏览器特性

## 🔄 版本更新

### 更新步骤
1. 备份当前版本
2. 下载新版本文件
3. 替换 web 文件夹内容
4. 测试功能是否正常
5. 清除浏览器缓存

### 版本兼容性
- 检查 API 版本兼容性
- 确认浏览器支持情况
- 测试现有功能

## 📞 技术支持

### 获取帮助
- 查看 [GitHub Issues](https://github.com/xianyu110/z-image/issues)
- 阅读 [Z-Image 官方文档](https://zimage.run)
- 参考本部署指南

### 报告问题
提交问题时请包含：
- 操作系统信息
- 浏览器版本
- 错误描述和截图
- 复现步骤

## 🌟 功能建议

欢迎提交功能建议和改进意见：
- 新的预设提示词
- 界面优化建议
- 功能增强需求
- 性能优化方案

---

通过这个 Web 前端测试工具，你可以更方便地测试和使用 Z-Image 图片生成 API！