// 全局变量
let currentTaskId = null;
let generationInterval = null;
let startTime = null;
let elapsedTimeInterval = null;
let isGenerating = false;
let currentPreset = 'fast';
let generationHistory = [];
let performanceStats = {
    totalGenerations: 0,
    totalTime: 0,
    avgTime: 0
};

// API 配置
const API_CONFIG = {
    baseUrl: 'http://localhost:8000',
    endpoints: {
        health: '/health',
        completions: '/v1/chat/completions',
        task: '/v1/tasks/{taskId}',
        image: '/v1/images/{taskId}'
    }
};

// 预设配置
const PRESETS = {
    fast: {
        name: '极速模式',
        batch_size: 1,
        width: 512,
        height: 512,
        steps: 4,
        cfg_scale: 5,
        negative_prompt: '',
        estimatedTime: '2-3秒'
    },
    balanced: {
        name: '平衡模式',
        batch_size: 2,
        width: 768,
        height: 768,
        steps: 6,
        cfg_scale: 7,
        negative_prompt: 'low quality, blurry',
        estimatedTime: '4-6秒'
    },
    quality: {
        name: '质量模式',
        batch_size: 4,
        width: 1024,
        height: 1024,
        steps: 8,
        cfg_scale: 8,
        negative_prompt: 'low quality, blurry, deformed',
        estimatedTime: '8-12秒'
    }
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    loadSettings();
    setupEventListeners();
    selectPreset('fast');
    testApiConnection();
    loadHistory();
    addLog('🚀 系统初始化完成', 'success');
}

function setupEventListeners() {
    // API地址变化监听
    document.getElementById('apiUrl').addEventListener('change', function() {
        API_CONFIG.baseUrl = this.value;
        saveSettings();
        testApiConnection();
    });

    // 提示文本变化监听
    document.getElementById('prompt').addEventListener('input', function() {
        saveSettings();
    });

    document.getElementById('negativePrompt').addEventListener('input', function() {
        saveSettings();
    });

    // 参数变化监听
    ['batchSize', 'width', 'height', 'steps', 'cfgScale'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', function() {
                updateCustomPreset();
                saveSettings();
            });
        }
    });
}

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

    // 加载历史记录
    const savedHistory = localStorage.getItem('generationHistory');
    if (savedHistory) {
        generationHistory = JSON.parse(savedHistory);
        displayHistory();
    }

    // 加载性能统计
    const savedStats = localStorage.getItem('performanceStats');
    if (savedStats) {
        performanceStats = JSON.parse(savedStats);
        updatePerformanceDisplay();
    }
}

function saveSettings() {
    localStorage.setItem('apiUrl', API_CONFIG.baseUrl);
    localStorage.setItem('prompt', document.getElementById('prompt').value);
    localStorage.setItem('negativePrompt', document.getElementById('negativePrompt').value);
}

function saveHistory() {
    localStorage.setItem('generationHistory', JSON.stringify(generationHistory));
}

function savePerformanceStats() {
    localStorage.setItem('performanceStats', JSON.stringify(performanceStats));
}

function selectPreset(preset) {
    currentPreset = preset;

    // 更新按钮状态
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-preset="${preset}"]`).classList.add('active');

    // 应用预设参数
    const config = PRESETS[preset];

    document.getElementById('batchSize').value = config.batch_size;
    document.getElementById('width').value = config.width;
    document.getElementById('height').value = config.height;
    document.getElementById('steps').value = config.steps;
    document.getElementById('cfgScale').value = config.cfg_scale;
    document.getElementById('negativePrompt').value = config.negative_prompt;

    updateStepsDisplay();
    updateCfgDisplay();

    addLog(`🎯 已选择${config.name}，预计时间：${config.estimatedTime}`, 'info');
}

function updateCustomPreset() {
    // 当参数被手动修改时，取消预设选择
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('active');
    });
}

function updateStepsDisplay() {
    const steps = document.getElementById('steps').value;
    document.getElementById('stepsDisplay').textContent = `${steps}步`;
}

function updateCfgDisplay() {
    const cfg = document.getElementById('cfgScale').value;
    document.getElementById('cfgDisplay').textContent = cfg;
}

function setPrompt(prompt) {
    document.getElementById('prompt').value = prompt;
    saveSettings();
    addLog(`✏️ 已设置快速提示：${prompt}`, 'info');
}

async function testApiConnection() {
    const statusElement = document.getElementById('connectionStatus');
    const statusIndicator = statusElement.querySelector('i');
    const statusText = statusElement.querySelector('span');
    const serverStatus = document.getElementById('serverStatus');

    try {
        statusElement.className = 'status-indicator connecting';
        statusIndicator.className = 'fas fa-circle';
        statusText.textContent = '连接中...';
        serverStatus.textContent = '检查中...';

        const response = await fetch(`${API_CONFIG.baseUrl}/health`);

        if (response.ok) {
            const data = await response.json();
            statusElement.className = 'status-indicator connected';
            statusIndicator.className = 'fas fa-circle';
            statusText.textContent = '已连接';
            serverStatus.textContent = '✅ 服务器正常';
            addLog('🔗 API连接成功', 'success');
        } else {
            throw new Error('服务器响应异常');
        }
    } catch (error) {
        statusElement.className = 'status-indicator disconnected';
        statusIndicator.className = 'fas fa-circle';
        statusText.textContent = '连接失败';
        serverStatus.textContent = '❌ 连接失败';
        addLog(`❌ API连接失败：${error.message}`, 'error');
    }
}

async function generateImage() {
    if (isGenerating) {
        addLog('⚠️ 正在生成中，请等待', 'warning');
        return;
    }

    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) {
        addLog('⚠️ 请输入图片描述', 'warning');
        return;
    }

    try {
        isGenerating = true;
        startTime = Date.now();

        // 更新UI状态
        updateGeneratingUI(true);
        addLog('🎨 开始生成图片...', 'info');

        // 构建请求参数
        const requestParams = {
            model: 'zimage-turbo',
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            extra_body: {
                batch_size: parseInt(document.getElementById('batchSize').value),
                width: parseInt(document.getElementById('width').value),
                height: parseInt(document.getElementById('height').value),
                steps: parseInt(document.getElementById('steps').value),
                cfg_scale: parseFloat(document.getElementById('cfgScale').value),
                negative_prompt: document.getElementById('negativePrompt').value
            }
        };

        addLog(`📤 发送生成请求：${JSON.stringify(requestParams, null, 2)}`, 'info');

        // 发送生成请求
        const response = await fetch(`${API_CONFIG.baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestParams)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        currentTaskId = result.choices[0].message.task_uuid;

        addLog(`✅ 任务已创建，ID：${currentTaskId}`, 'success');
        addLog(`⏱️ 预计完成时间：${result.choices[0].message.estimated_time || '计算中...'}`, 'info');

        // 开始轮询任务状态
        startTaskPolling();

    } catch (error) {
        isGenerating = false;
        updateGeneratingUI(false);
        addLog(`❌ 生成失败：${error.message}`, 'error');
    }
}

function startTaskPolling() {
    let attempt = 0;
    const maxAttempts = 60; // 最多轮询60次（5分钟）

    generationInterval = setInterval(async () => {
        attempt++;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);

        try {
            const response = await fetch(`${API_CONFIG.baseUrl}/v1/tasks/${currentTaskId}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            const taskData = result.data?.task;

            if (taskData) {
                const status = taskData.taskStatus;
                const progress = taskData.progress || 0;

                // 更新进度
                updateProgress(progress, elapsed);

                if (status === 'completed') {
                    // 任务完成
                    clearInterval(generationInterval);
                    await handleTaskCompleted(taskData);
                    return;
                } else if (status === 'failed') {
                    // 任务失败
                    clearInterval(generationInterval);
                    handleTaskFailed();
                    return;
                }
            }

            // 检查超时
            if (attempt >= maxAttempts) {
                clearInterval(generationInterval);
                handleTaskTimeout();
                return;
            }

        } catch (error) {
            addLog(`⚠️ 状态检查失败：${error.message}`, 'warning');
        }
    }, 2000); // 每2秒检查一次

    // 更新时间显示
    elapsedTimeInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('progressTime').textContent = `${elapsed}s`;
    }, 1000);
}

function updateProgress(progress, elapsed) {
    const progressPercent = Math.min(progress, 100);
    document.getElementById('progressFill').style.width = `${progressPercent}%`;
    document.getElementById('progressPercent').textContent = `${progressPercent}%`;
    document.getElementById('progressTime').textContent = `${elapsed}s`;
    document.getElementById('statusText').textContent = `生成进度：${progressPercent}%`;
}

async function handleTaskCompleted(taskData) {
    isGenerating = false;
    const totalTime = Math.floor((Date.now() - startTime) / 1000);

    updateGeneratingUI(false);
    updateProgress(100, totalTime);

    addLog(`🎉 生成完成！用时：${totalTime}秒`, 'success');
    document.getElementById('statusText').textContent = '生成完成！';

    // 更新性能统计
    performanceStats.totalGenerations++;
    performanceStats.totalTime += totalTime;
    performanceStats.avgTime = Math.round(performanceStats.totalTime / performanceStats.totalGenerations);
    savePerformanceStats();
    updatePerformanceDisplay();

    // 获取图片URL
    const resultUrl = taskData.resultUrl;
    const imageUrls = resultUrl ? [resultUrl] : (taskData.resultUrls || []);

    if (imageUrls.length > 0) {
        // 显示生成的图片
        displayImages(imageUrls, taskData);

        // 添加到历史记录
        addToHistory(imageUrls, {
            prompt: document.getElementById('prompt').value,
            preset: currentPreset,
            time: totalTime,
            timestamp: new Date().toISOString()
        });

        addLog(`📸 成功生成${imageUrls.length}张图片`, 'success');
    } else {
        addLog('⚠️ 未找到生成的图片', 'warning');
    }

    // 清理定时器
    if (elapsedTimeInterval) {
        clearInterval(elapsedTimeInterval);
    }
}

function handleTaskFailed() {
    isGenerating = false;
    updateGeneratingUI(false);
    addLog('❌ 生成任务失败', 'error');
    document.getElementById('statusText').textContent = '生成失败';
}

function handleTaskTimeout() {
    isGenerating = false;
    updateGeneratingUI(false);
    addLog('⏰ 生成任务超时', 'error');
    document.getElementById('statusText').textContent = '生成超时';
}

function updateGeneratingUI(generating) {
    const generateBtn = document.getElementById('generateBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    if (generating) {
        generateBtn.style.display = 'none';
        cancelBtn.style.display = 'block';
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressPercent').textContent = '0%';
        document.getElementById('progressTime').textContent = '0s';
        document.getElementById('statusText').textContent = '正在生成...';

        // 禁用输入
        document.getElementById('prompt').disabled = true;
        document.getElementById('batchSize').disabled = true;
        document.getElementById('width').disabled = true;
        document.getElementById('height').disabled = true;
        document.getElementById('steps').disabled = true;
        document.getElementById('cfgScale').disabled = true;
        document.querySelectorAll('.preset-btn').forEach(btn => btn.disabled = true);
    } else {
        generateBtn.style.display = 'block';
        cancelBtn.style.display = 'none';

        // 启用输入
        document.getElementById('prompt').disabled = false;
        document.getElementById('batchSize').disabled = false;
        document.getElementById('width').disabled = false;
        document.getElementById('height').disabled = false;
        document.getElementById('steps').disabled = false;
        document.getElementById('cfgScale').disabled = false;
        document.querySelectorAll('.preset-btn').forEach(btn => btn.disabled = false);
    }
}

function cancelGeneration() {
    if (generationInterval) {
        clearInterval(generationInterval);
    }
    if (elapsedTimeInterval) {
        clearInterval(elapsedTimeInterval);
    }

    isGenerating = false;
    currentTaskId = null;
    updateGeneratingUI(false);

    addLog('🛑 已取消生成', 'warning');
    document.getElementById('statusText').textContent = '已取消';
}

function displayImages(imageUrls, taskData) {
    const gallery = document.getElementById('imageGallery');
    gallery.innerHTML = '';

    imageUrls.forEach((url, index) => {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.innerHTML = `
            <img src="${url}" alt="生成的图片${index + 1}" onclick="showImageModal('${url}')" loading="lazy">
            <div class="image-info">
                <div>图片 ${index + 1}</div>
                <div>${taskData.width || '?'}x${taskData.height || '?'}</div>
            </div>
        `;
        gallery.appendChild(imageItem);
    });
}

function showImageModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalDownload = document.getElementById('modalDownload');

    modalImage.src = imageUrl;
    modalDownload.href = imageUrl;
    modalDownload.download = imageUrl.split('/').pop() || 'generated_image.png';

    modal.style.display = 'block';
}

function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
}

function copyImageUrl() {
    const imageUrl = document.getElementById('modalImage').src;
    navigator.clipboard.writeText(imageUrl).then(() => {
        addLog('📋 图片链接已复制到剪贴板', 'success');
    }).catch(() => {
        addLog('❌ 复制失败', 'error');
    });
}

function addToHistory(imageUrls, metadata) {
    const historyItem = {
        id: Date.now(),
        images: imageUrls,
        prompt: metadata.prompt,
        preset: metadata.preset,
        time: metadata.time,
        timestamp: metadata.timestamp
    };

    generationHistory.unshift(historyItem);

    // 只保留最近20条记录
    if (generationHistory.length > 20) {
        generationHistory = generationHistory.slice(0, 20);
    }

    saveHistory();
    displayHistory();
}

function displayHistory() {
    const historyGallery = document.getElementById('historyGallery');

    if (generationHistory.length === 0) {
        historyGallery.innerHTML = `
            <div class="placeholder">
                <i class="fas fa-clock"></i>
                <p>暂无历史记录</p>
            </div>
        `;
        return;
    }

    historyGallery.innerHTML = '';

    generationHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'image-item history-item';

        const firstImage = item.images[0];
        const date = new Date(item.timestamp).toLocaleString();

        historyItem.innerHTML = `
            <img src="${firstImage}" alt="历史图片" onclick="showImageModal('${firstImage}')" loading="lazy">
            <div class="image-info">
                <div>${item.prompt.substring(0, 20)}${item.prompt.length > 20 ? '...' : ''}</div>
                <div>${item.time}s • ${item.preset}</div>
            </div>
        `;

        historyGallery.appendChild(historyItem);
    });
}

function loadHistory() {
    displayHistory();
}

function updatePerformanceDisplay() {
    const avgTimeElement = document.getElementById('avgTime');

    if (performanceStats.totalGenerations > 0) {
        avgTimeElement.textContent = `平均：${performanceStats.avgTime}秒`;
    } else {
        avgTimeElement.textContent = '-';
    }
}

function addLog(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;

    const timestamp = new Date().toLocaleTimeString();
    logEntry.innerHTML = `<span style="opacity: 0.7">[${timestamp}]</span> ${message}`;

    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // 限制日志条数
    const logs = logContainer.querySelectorAll('.log-entry');
    if (logs.length > 100) {
        logs[0].remove();
    }
}

function clearLogs() {
    document.getElementById('logContainer').innerHTML = '';
    addLog('🧹 日志已清空', 'info');
}

function exportLogs() {
    const logContainer = document.getElementById('logContainer');
    const logs = Array.from(logContainer.querySelectorAll('.log-entry')).map(log =>
        log.textContent
    ).join('\n');

    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `z-image-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();

    URL.revokeObjectURL(url);
    addLog('📥 日志已导出', 'success');
}

// 键盘快捷键
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter 生成图片
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        if (!isGenerating) {
            generateImage();
        }
    }

    // Escape 取消生成
    if (event.key === 'Escape' && isGenerating) {
        cancelGeneration();
    }

    // Ctrl/Cmd + L 清空日志
    if ((event.ctrlKey || event.metaKey) && event.key === 'l') {
        event.preventDefault();
        clearLogs();
    }
});

// 页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (document.hidden && isGenerating) {
        addLog('⚠️ 页面已隐藏，生成过程继续在后台运行', 'warning');
    } else if (!document.hidden && isGenerating) {
        addLog('👁️ 页面已恢复，正在监控生成进度', 'info');
    }
});

// 错误处理
window.addEventListener('error', function(event) {
    addLog(`❌ JavaScript错误：${event.error.message}`, 'error');
});

window.addEventListener('unhandledrejection', function(event) {
    addLog(`❌ 未处理的Promise拒绝：${event.reason}`, 'error');
});