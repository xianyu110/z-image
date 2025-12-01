// 全局变量
let currentTaskId = null;
let generationInterval = null;
let startTime = null;
let elapsedTimeInterval = null;
let isGenerating = false;

// API 配置
const API_CONFIG = {
    baseUrl: 'http://localhost:8000',
    endpoints: {
        health: '/api/health',
        completions: '/v1/chat/completions',
        task: '/v1/tasks/{taskId}',
        image: '/v1/images/{taskId}'
    }
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 从本地存储恢复设置
    loadSettings();

    // 设置事件监听器
    setupEventListeners();

    // 测试 API 连接
    testApiConnection();

    addLog('系统初始化完成', 'success');
}

// 加载设置
function loadSettings() {
    const savedApiUrl = localStorage.getItem('apiUrl');
    if (savedApiUrl) {
        document.getElementById('apiUrl').value = savedApiUrl;
        API_CONFIG.baseUrl = savedApiUrl;
    }

    const savedPrompt = localStorage.getItem('prompt');
    if (savedPrompt) {
        document.getElementById('prompt').value = savedPrompt;
    }

    const savedNegativePrompt = localStorage.getItem('negativePrompt');
    if (savedNegativePrompt) {
        document.getElementById('negativePrompt').value = savedNegativePrompt;
    }
}

// 保存设置
function saveSettings() {
    localStorage.setItem('apiUrl', document.getElementById('apiUrl').value);
    localStorage.setItem('prompt', document.getElementById('prompt').value);
    localStorage.setItem('negativePrompt', document.getElementById('negativePrompt').value);
}

// 设置事件监听器
function setupEventListeners() {
    // API 地址变化
    document.getElementById('apiUrl').addEventListener('change', function() {
        API_CONFIG.baseUrl = this.value;
        localStorage.setItem('apiUrl', this.value);
        testApiConnection();
    });

    // 提示词变化时自动保存
    document.getElementById('prompt').addEventListener('input', function() {
        localStorage.setItem('prompt', this.value);
    });

    document.getElementById('negativePrompt').addEventListener('input', function() {
        localStorage.setItem('negativePrompt', this.value);
    });

    // 键盘快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 生成图片
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!isGenerating) {
                generateImage();
            } else {
                stopGeneration();
            }
        }

        // Esc 停止生成
        if (e.key === 'Escape' && isGenerating) {
            stopGeneration();
        }
    });

    // 模态框点击外部关闭
    document.getElementById('imageModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

// 测试 API 连接
async function testApiConnection() {
    const statusElement = document.getElementById('connectionStatus');
    const apiUrl = document.getElementById('apiUrl').value;

    try {
        statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>连接中...</span>';
        statusElement.className = 'status-indicator';

        const response = await fetch(`${apiUrl}${API_CONFIG.endpoints.health}`, {
            method: 'GET',
            timeout: 5000
        });

        if (response.ok) {
            const data = await response.json();
            statusElement.innerHTML = '<i class="fas fa-circle"></i> <span>连接成功</span>';
            statusElement.className = 'status-indicator connected';
            addLog(`API 连接成功: ${data.message || '服务正常运行'}`, 'success');
            API_CONFIG.baseUrl = apiUrl;
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        statusElement.innerHTML = '<i class="fas fa-circle"></i> <span>连接失败</span>';
        statusElement.className = 'status-indicator disconnected';
        addLog(`API 连接失败: ${error.message}`, 'error');
    }
}

// 更新滑块显示
function updateStepsDisplay(value) {
    document.getElementById('stepsDisplay').textContent = value;
}

function updateCfgDisplay(value) {
    document.getElementById('cfgDisplay').textContent = value;
}

// 应用预设
function applyPreset(presetText) {
    const promptElement = document.getElementById('prompt');
    promptElement.value = presetText;
    promptElement.focus();

    // 添加动画效果
    promptElement.style.animation = 'fadeIn 0.3s ease';
    setTimeout(() => {
        promptElement.style.animation = '';
    }, 300);

    addLog('应用预设提示词', 'info');
}

// 生成图片
async function generateImage() {
    if (isGenerating) {
        addLog('正在生成中，请稍候...', 'warning');
        return;
    }

    // 验证输入
    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) {
        addLog('请输入图片描述', 'error');
        document.getElementById('prompt').focus();
        return;
    }

    const apiUrl = document.getElementById('apiUrl').value;
    if (!apiUrl) {
        addLog('请输入 API 地址', 'error');
        document.getElementById('apiUrl').focus();
        return;
    }

    // 获取参数
    const params = getGenerationParams();

    // 设置生成状态
    setGeneratingState(true);

    try {
        addLog('开始生成图片...', 'info');
        updateStatus('提交任务...');

        const requestBody = {
            model: params.model,
            messages: [{ role: 'user', content: prompt }],
            extra_body: {
                prompt: prompt,
                negative_prompt: params.negativePrompt,
                batch_size: params.batchSize,
                width: params.width,
                height: params.height,
                steps: params.steps,
                cfg_scale: params.cfgScale
            }
        };

        const response = await fetch(`${apiUrl}${API_CONFIG.endpoints.completions}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        currentTaskId = data.choices[0].message.task_uuid;

        document.getElementById('taskId').textContent = currentTaskId;
        updateStatus('任务已提交');

        addLog(`任务提交成功，ID: ${currentTaskId}`, 'success');

        // 开始轮询任务状态
        startTaskPolling();

    } catch (error) {
        addLog(`生成失败: ${error.message}`, 'error');
        updateStatus('生成失败');
        setGeneratingState(false);
    }
}

// 获取生成参数
function getGenerationParams() {
    return {
        model: document.getElementById('model').value,
        prompt: document.getElementById('prompt').value.trim(),
        negativePrompt: document.getElementById('negativePrompt').value.trim(),
        batchSize: parseInt(document.getElementById('batchSize').value),
        width: parseInt(document.getElementById('width').value),
        height: parseInt(document.getElementById('height').value),
        steps: parseInt(document.getElementById('steps').value),
        cfgScale: parseInt(document.getElementById('cfgScale').value)
    };
}

// 开始任务轮询
function startTaskPolling() {
    if (!currentTaskId) return;

    startTime = Date.now();
    startElapsedTimeCounter();

    generationInterval = setInterval(async () => {
        await checkTaskStatus();
    }, 2000); // 每2秒检查一次
}

// 检查任务状态
async function checkTaskStatus() {
    if (!currentTaskId) return;

    try {
        const apiUrl = document.getElementById('apiUrl').value;
        const response = await fetch(`${apiUrl}${API_CONFIG.endpoints.task.replace('{taskId}', currentTaskId)}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const taskData = data.data.task;

        updateStatus(taskData.taskStatus);
        updateProgress(taskData.progress || 0);

        if (taskData.taskStatus === 'completed') {
            // 任务完成，获取结果
            await getTaskResult();
        } else if (taskData.taskStatus === 'failed') {
            throw new Error(taskData.errorMessage || '任务失败');
        }

    } catch (error) {
        addLog(`检查任务状态失败: ${error.message}`, 'error');
        stopGeneration();
    }
}

// 获取任务结果
async function getTaskResult() {
    try {
        const apiUrl = document.getElementById('apiUrl').value;
        const response = await fetch(`${apiUrl}${API_CONFIG.endpoints.image.replace('{taskId}', currentTaskId)}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.data.images && data.data.images.length > 0) {
            displayResults(data.data.images);
            addLog(`图片生成成功，共 ${data.data.images.length} 张`, 'success');
            updateStatus('生成完成');
        } else {
            throw new Error('未获取到图片结果');
        }

    } catch (error) {
        addLog(`获取结果失败: ${error.message}`, 'error');
        updateStatus('获取结果失败');
    } finally {
        stopGeneration();
    }
}

// 显示结果
function displayResults(images) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';

    images.forEach((imageUrl, index) => {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.innerHTML = `
            <img src="${imageUrl}" alt="生成的图片 ${index + 1}" onclick="openModal('${imageUrl}')">
            <div class="image-overlay">
                <div class="btn-group">
                    <button class="overlay-btn" onclick="downloadImage('${imageUrl}', 'image_${index + 1}')" title="下载">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="overlay-btn" onclick="copyImageUrl('${imageUrl}')" title="复制链接">
                        <i class="fas fa-link"></i>
                    </button>
                    <button class="overlay-btn" onclick="openModal('${imageUrl}')" title="查看大图">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(imageItem);
    });

    // 显示操作按钮
    document.getElementById('resultActions').style.display = 'flex';

    // 滚动到结果区域
    document.querySelector('.results-card').scrollIntoView({ behavior: 'smooth' });
}

// 停止生成
function stopGeneration() {
    isGenerating = false;

    if (generationInterval) {
        clearInterval(generationInterval);
        generationInterval = null;
    }

    if (elapsedTimeInterval) {
        clearInterval(elapsedTimeInterval);
        elapsedTimeInterval = null;
    }

    currentTaskId = null;
    setGeneratingState(false);
    updateStatus('已停止');

    addLog('图片生成已停止', 'info');
}

// 设置生成状态
function setGeneratingState(generating) {
    isGenerating = generating;
    const generateBtn = document.getElementById('generateBtn');
    const stopBtn = document.getElementById('stopBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');

    if (generating) {
        generateBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        loadingOverlay.style.display = 'flex';
    } else {
        generateBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        loadingOverlay.style.display = 'none';
    }
}

// 更新状态
function updateStatus(status) {
    document.getElementById('currentStatus').textContent = status;
}

// 更新进度
function updateProgress(progress) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    const percentage = Math.round(progress);
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `${percentage}%`;
}

// 开始计时器
function startElapsedTimeCounter() {
    elapsedTimeInterval = setInterval(() => {
        if (startTime) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            document.getElementById('elapsedTime').textContent = `${elapsed}秒`;
        }
    }, 1000);
}

// 下载图片
function downloadImage(imageUrl, filename) {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `zimage_${filename}.png`;
    link.target = '_blank';
    link.click();

    addLog(`下载图片: ${filename}`, 'info');
}

// 下载所有图片
function downloadAllImages() {
    const images = document.querySelectorAll('#resultsContainer img');
    images.forEach((img, index) => {
        setTimeout(() => {
            downloadImage(img.src, `image_${index + 1}`);
        }, index * 200); // 间隔200ms下载，避免浏览器阻止
    });

    addLog('开始批量下载图片', 'info');
}

// 复制图片链接
function copyImageUrl(imageUrl) {
    navigator.clipboard.writeText(imageUrl).then(() => {
        addLog('图片链接已复制到剪贴板', 'success');
    }).catch(() => {
        addLog('复制失败，请手动复制链接', 'error');
    });
}

// 清空结果
function clearResults() {
    document.getElementById('resultsContainer').innerHTML = `
        <div class="placeholder">
            <i class="fas fa-image"></i>
            <p>点击"生成图片"开始创建</p>
        </div>
    `;
    document.getElementById('resultActions').style.display = 'none';

    addLog('结果已清空', 'info');
}

// 分享结果
async function shareResults() {
    const images = document.querySelectorAll('#resultsContainer img');
    if (images.length === 0) {
        addLog('没有可分享的图片', 'warning');
        return;
    }

    const shareData = {
        title: 'Z-Image 生成的图片',
        text: `使用 Z-Image 生成了 ${images.length} 张图片`,
        url: window.location.href
    };

    try {
        if (navigator.share) {
            await navigator.share(shareData);
            addLog('分享成功', 'success');
        } else {
            // 如果不支持分享 API，复制链接
            navigator.clipboard.writeText(window.location.href);
            addLog('链接已复制到剪贴板', 'success');
        }
    } catch (error) {
        addLog('分享失败', 'error');
    }
}

// 打开模态框
function openModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');

    modalImage.src = imageUrl;
    modal.style.display = 'flex';

    addLog('查看大图', 'info');
}

// 关闭模态框
function closeModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// 添加日志
function addLog(message, type = 'info') {
    const logsContainer = document.getElementById('logsContainer');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';

    const currentTime = new Date().toLocaleTimeString();
    logEntry.innerHTML = `
        <span class="log-time">[${currentTime}]</span>
        <span class="log-${type}">${message}</span>
    `;

    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;

    // 限制日志数量
    const logs = logsContainer.querySelectorAll('.log-entry');
    if (logs.length > 50) {
        logs[0].remove();
    }
}

// 错误处理
window.addEventListener('error', function(e) {
    addLog(`系统错误: ${e.message}`, 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    addLog(`未处理的 Promise 错误: ${e.reason}`, 'error');
});

// 网络状态监听
window.addEventListener('online', function() {
    addLog('网络连接已恢复', 'success');
    testApiConnection();
});

window.addEventListener('offline', function() {
    addLog('网络连接已断开', 'warning');
});

// 页面离开提醒
window.addEventListener('beforeunload', function(e) {
    if (isGenerating) {
        e.preventDefault();
        e.returnValue = '图片正在生成中，确定要离开吗？';
    }
});

// 工具函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 导出函数到全局作用域（用于 HTML 中的 onclick）
window.generateImage = generateImage;
window.stopGeneration = stopGeneration;
window.testApiConnection = testApiConnection;
window.applyPreset = applyPreset;
window.downloadImage = downloadImage;
window.copyImageUrl = copyImageUrl;
window.clearResults = clearResults;
window.shareResults = shareResults;
window.openModal = openModal;
window.closeModal = closeModal;
window.updateStepsDisplay = updateStepsDisplay;
window.updateCfgDisplay = updateCfgDisplay;
window.downloadAllImages = downloadAllImages;