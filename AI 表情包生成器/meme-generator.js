/**
 * AI 表情包生成器主要逻辑
 */
const { createApp } = Vue;

createApp({
    data() {
        return {
            // 基础数据
            description: '',
            selectedStyle: 'cute',
            selectedModels: ['dalle3'],
            
            // 高级参数
            parameters: {
                size: '512x512',
                steps: 30,
                guidance: 7,
                negativePrompt: ''
            },
            
            // 风格模板
            styleTemplates: [
                {
                    id: 'cute',
                    name: '可爱风格',
                    emoji: '🥰',
                    description: '萌萌哒的卡通风格',
                    prompt: 'cute, kawaii, adorable, chibi style, soft colors, rounded features'
                },
                {
                    id: 'funny',
                    name: '搞笑风格',
                    emoji: '😂',
                    description: '幽默搞怪的表现',
                    prompt: 'funny, humorous, comedic, exaggerated expressions, cartoon style'
                },
                {
                    id: 'cool',
                    name: '酷炫风格',
                    emoji: '😎',
                    description: '炫酷的视觉效果',
                    prompt: 'cool, stylish, modern, sleek design, vibrant colors, dynamic'
                },
                {
                    id: 'warm',
                    name: '温馨风格',
                    emoji: '🤗',
                    description: '温暖治愈的画面',
                    prompt: 'warm, cozy, heartwarming, soft lighting, gentle colors, peaceful'
                },
                {
                    id: 'artistic',
                    name: '艺术风格',
                    emoji: '🎨',
                    description: '具有艺术感的创作',
                    prompt: 'artistic, creative, abstract, expressive, unique style, masterpiece'
                },
                {
                    id: 'retro',
                    name: '复古风格',
                    emoji: '📼',
                    description: '怀旧复古的视觉',
                    prompt: 'retro, vintage, nostalgic, classic style, muted colors, old-fashioned'
                }
            ],
            
            // AI模型列表
            aiModels: [
                {
                    id: 'dalle3',
                    name: 'DALL-E 3',
                    description: '最新最强的图像生成模型'
                },
                {
                    id: 'dalle2',
                    name: 'DALL-E 2',
                    description: '经典稳定的图像生成'
                },
                {
                    id: 'stable-diffusion',
                    name: 'Stable Diffusion XL',
                    description: '开源高质量模型'
                },
                {
                    id: 'midjourney',
                    name: 'Midjourney',
                    description: '艺术风格专业模型'
                }
            ],
            
            // 生成状态
            isGenerating: false,
            generatedImage: null,
            finalImage: null,
            imageQuality: null,
            
            // 并行生成
            showParallelResults: false,
            parallelResults: [],
            
            // 文字设置
            textSettings: {
                topText: '',
                bottomText: '',
                fontSize: 40,
                color: '#FFFFFF',
                shadowBlur: 3
            },
            
            // 通知系统
            notification: {
                show: false,
                message: '',
                type: 'info' // success, error, info
            },
            
            // 生成历史记录
            showHistory: false,
            generationHistory: [],
            
            // API配置
            showAPIConfig: false,
            apiKeys: {
                openai: '',
                stability: '',
                midjourney: ''
            },
            
            // 自定义API配置
            showCustomAPIForm: false,
            isTestingCustomAPI: false,
            customAPIs: [],
            customAPIForm: {
                name: '',
                method: '',
                endpoint: '',
                authType: 'none',
                authValue: '',
                parameters: '',
                responsePath: 'data.image_url',
                errors: {}
            },
            editingAPIIndex: -1
        };
    },
    
    mounted() {
        // 加载历史记录
        this.loadHistory();
        // 加载API配置
        this.loadAPIKeys();
        // 加载自定义API配置
        this.loadCustomAPIs();
    },
    
    methods: {
        /**
         * 显示通知
         * @param {string} message - 通知消息
         * @param {string} type - 通知类型
         */
        showNotification(message, type = 'info') {
            this.notification = {
                show: true,
                message,
                type
            };
            
            // 3秒后自动隐藏
            setTimeout(() => {
                this.hideNotification();
            }, 3000);
        },
        
        /**
         * 隐藏通知
         */
        hideNotification() {
            this.notification.show = false;
        },
        
        /**
         * 增强提示词
         * @param {string} description - 原始描述
         * @param {string} styleId - 风格ID
         * @returns {string} 增强后的提示词
         */
        enhancePrompt(description, styleId) {
            const style = this.styleTemplates.find(s => s.id === styleId);
            const stylePrompt = style ? style.prompt : '';
            
            // 组合提示词
            let enhancedPrompt = description;
            if (stylePrompt) {
                enhancedPrompt += `, ${stylePrompt}`;
            }
            
            // 添加质量提升词
            enhancedPrompt += ', high quality, detailed, professional';
            
            return enhancedPrompt;
        },
        
        /**
         * 评估图片质量
         * @param {string} imageUrl - 图片URL
         * @param {Object} params - 生成参数
         * @returns {number} 质量评分 (0-100)
         */
        assessImageQuality(imageUrl, params) {
            // 基础质量评分
            let score = 60;
            
            // 根据参数调整评分
            if (params.size === '1024x1024') score += 15;
            else if (params.size === '768x768') score += 10;
            
            if (params.steps >= 30) score += 10;
            else if (params.steps >= 20) score += 5;
            
            if (params.guidance >= 7 && params.guidance <= 12) score += 10;
            
            // 添加随机因素模拟真实评估
            score += Math.floor(Math.random() * 15) - 7;
            
            return Math.max(0, Math.min(100, score));
        },
        
        /**
         * 生成单张图片
         */
        async generateSingleImage() {
            if (!this.description.trim()) {
                this.showNotification('请输入图片描述', 'error');
                return;
            }
            
            if (this.selectedModels.length === 0) {
                this.showNotification('请选择至少一个AI模型', 'error');
                return;
            }
            
            this.isGenerating = true;
            this.showParallelResults = false;
            
            try {
                const modelId = this.selectedModels[0];
                const enhancedPrompt = this.enhancePrompt(this.description, this.selectedStyle);
                
                // 准备API调用参数
                const params = {
                    prompt: enhancedPrompt,
                    size: this.parameters.size,
                    steps: this.parameters.steps,
                    guidance: this.parameters.guidance,
                    negativePrompt: this.parameters.negativePrompt
                };
                
                // 调用API
                const result = await window.apiConfigManager.callAPI(modelId, params);
                
                if (result.success && result.imageUrl) {
                    this.generatedImage = result.imageUrl;
                    this.finalImage = result.imageUrl;
                    this.imageQuality = this.assessImageQuality(result.imageUrl, params);
                    
                    // 保存到历史记录
                    const model = this.aiModels.find(m => m.id === modelId);
                    const style = this.styleTemplates.find(s => s.id === this.selectedStyle);
                    this.saveToHistory({
                        description: this.description,
                        image: result.imageUrl,
                        modelId: modelId,
                        modelName: model?.name || modelId,
                        styleId: this.selectedStyle,
                        styleName: style?.name || this.selectedStyle,
                        quality: this.imageQuality,
                        parameters: { ...params },
                        timestamp: Date.now()
                    });
                    
                    this.showNotification('图片生成成功！', 'success');
                } else {
                    throw new Error(result.error || '生成失败');
                }
            } catch (error) {
                console.error('生成图片失败:', error);
                this.showNotification('生成失败，请检查网络连接或API配置', 'error');
            } finally {
                this.isGenerating = false;
            }
        },
        
        /**
         * 并行生成多张图片
         */
        async generateParallelImages() {
            if (!this.description.trim()) {
                this.showNotification('请输入图片描述', 'error');
                return;
            }
            
            if (this.selectedModels.length < 2) {
                this.showNotification('并行生成需要选择至少2个模型', 'error');
                return;
            }
            
            this.isGenerating = true;
            this.showParallelResults = true;
            this.parallelResults = [];
            
            try {
                const enhancedPrompt = this.enhancePrompt(this.description, this.selectedStyle);
                
                // 准备API调用参数
                const params = {
                    prompt: enhancedPrompt,
                    size: this.parameters.size,
                    steps: this.parameters.steps,
                    guidance: this.parameters.guidance,
                    negativePrompt: this.parameters.negativePrompt
                };
                
                // 并行调用多个模型
                const promises = this.selectedModels.map(async (modelId) => {
                    try {
                        const result = await window.apiConfigManager.callAPI(modelId, params);
                        const model = this.aiModels.find(m => m.id === modelId);
                        
                        if (result.success && result.imageUrl) {
                            const quality = this.assessImageQuality(result.imageUrl, params);
                            return {
                                modelId,
                                modelName: model?.name || modelId,
                                image: result.imageUrl,
                                quality,
                                success: true
                            };
                        }
                        return { modelId, success: false, error: result.error };
                    } catch (error) {
                        return { modelId, success: false, error: error.message };
                    }
                });
                
                const results = await Promise.all(promises);
                this.parallelResults = results.filter(r => r.success);
                
                if (this.parallelResults.length > 0) {
                    this.showNotification(`成功生成 ${this.parallelResults.length} 张图片`, 'success');
                } else {
                    this.showNotification('所有模型生成失败', 'error');
                }
            } catch (error) {
                console.error('并行生成失败:', error);
                this.showNotification('并行生成失败', 'error');
            } finally {
                this.isGenerating = false;
            }
        },
        
        /**
         * 选择并行生成结果
         * @param {number} index - 结果索引
         */
        selectParallelResult(index) {
            const result = this.parallelResults[index];
            if (result) {
                this.generatedImage = result.image;
                this.finalImage = result.image;
                this.imageQuality = result.quality;
                this.showParallelResults = false;
                
                // 保存到历史记录
                const style = this.styleTemplates.find(s => s.id === this.selectedStyle);
                this.saveToHistory({
                    description: this.description,
                    image: result.image,
                    modelId: result.modelId,
                    modelName: result.modelName,
                    styleId: this.selectedStyle,
                    styleName: style?.name || this.selectedStyle,
                    quality: result.quality,
                    parameters: { ...this.parameters },
                    timestamp: Date.now()
                });
                
                this.showNotification(`已选择 ${result.modelName} 的生成结果`, 'success');
            }
        },
        
        /**
         * 应用文字到图片
         */
        applyText() {
            if (!this.generatedImage) {
                this.showNotification('请先生成图片', 'error');
                return;
            }
            
            const canvas = this.$refs.canvas;
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.crossOrigin = 'anonymous';
            img.onload = () => {
                // 设置画布尺寸
                canvas.width = img.width;
                canvas.height = img.height;
                
                // 绘制原图
                ctx.drawImage(img, 0, 0);
                
                // 设置文字样式
                ctx.font = `bold ${this.textSettings.fontSize}px Arial`;
                ctx.fillStyle = this.textSettings.color;
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                ctx.textAlign = 'center';
                ctx.shadowColor = '#000000';
                ctx.shadowBlur = this.textSettings.shadowBlur;
                
                // 绘制上方文字
                if (this.textSettings.topText) {
                    const y = this.textSettings.fontSize + 20;
                    ctx.strokeText(this.textSettings.topText, canvas.width / 2, y);
                    ctx.fillText(this.textSettings.topText, canvas.width / 2, y);
                }
                
                // 绘制下方文字
                if (this.textSettings.bottomText) {
                    const y = canvas.height - 20;
                    ctx.strokeText(this.textSettings.bottomText, canvas.width / 2, y);
                    ctx.fillText(this.textSettings.bottomText, canvas.width / 2, y);
                }
                
                // 更新最终图片
                this.finalImage = canvas.toDataURL('image/png');
                this.showNotification('文字添加成功！', 'success');
            };
            
            img.src = this.generatedImage;
        },
        
        /**
         * 下载图片
         */
        downloadImage() {
            if (!this.finalImage) {
                this.showNotification('没有可下载的图片', 'error');
                return;
            }
            
            const link = document.createElement('a');
            link.download = `meme-${Date.now()}.png`;
            link.href = this.finalImage;
            link.click();
            
            this.showNotification('图片下载成功！', 'success');
        },
        
        /**
         * 复制图片到剪贴板
         */
        async copyToClipboard() {
            if (!this.finalImage) {
                this.showNotification('没有可复制的图片', 'error');
                return;
            }
            
            try {
                const response = await fetch(this.finalImage);
                const blob = await response.blob();
                await navigator.clipboard.write([
                    new ClipboardItem({ 'image/png': blob })
                ]);
                this.showNotification('图片已复制到剪贴板！', 'success');
            } catch (error) {
                console.error('复制失败:', error);
                this.showNotification('复制失败，请手动保存图片', 'error');
            }
        },
        
        /**
         * 保存生成历史
         * @param {Object} item - 历史记录项
         */
        saveToHistory(item) {
            this.generationHistory.unshift(item);
            // 限制历史记录数量
            if (this.generationHistory.length > 50) {
                this.generationHistory = this.generationHistory.slice(0, 50);
            }
            this.saveHistoryToStorage();
        },
        
        /**
         * 加载历史图片
         * @param {Object} item - 历史记录项
         */
        loadHistoryImage(item) {
            this.description = item.description;
            this.selectedStyle = item.styleId;
            this.selectedModels = [item.modelId];
            this.parameters = { ...item.parameters };
            this.generatedImage = item.image;
            this.finalImage = item.image;
            this.imageQuality = item.quality;
            this.showHistory = false;
            this.showNotification('历史记录已加载', 'success');
        },
        
        /**
         * 删除历史记录项
         * @param {number} index - 索引
         */
        deleteHistoryItem(index) {
            this.generationHistory.splice(this.generationHistory.length - 1 - index, 1);
            this.saveHistoryToStorage();
            this.showNotification('历史记录已删除', 'success');
        },
        
        /**
         * 清空历史记录
         */
        clearHistory() {
            this.generationHistory = [];
            this.saveHistoryToStorage();
            this.showNotification('历史记录已清空', 'success');
        },
        
        /**
         * 保存历史记录到本地存储
         */
        saveHistoryToStorage() {
            try {
                localStorage.setItem('meme-generator-history', JSON.stringify(this.generationHistory));
            } catch (error) {
                console.error('保存历史记录失败:', error);
            }
        },
        
        /**
         * 从本地存储加载历史记录
         */
        loadHistory() {
            try {
                const saved = localStorage.getItem('meme-generator-history');
                if (saved) {
                    this.generationHistory = JSON.parse(saved);
                }
            } catch (error) {
                console.error('加载历史记录失败:', error);
                this.generationHistory = [];
            }
        },
        
        /**
         * 格式化日期显示
         * @param {number} timestamp - 时间戳
         * @returns {string} 格式化的日期
         */
        formatDate(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN');
        },
        
        /**
         * 获取最常用的模型
         * @returns {string} 模型名称
         */
        getMostUsedModel() {
            if (this.generationHistory.length === 0) return '-';
            
            const modelCount = {};
            this.generationHistory.forEach(item => {
                modelCount[item.modelName] = (modelCount[item.modelName] || 0) + 1;
            });
            
            return Object.keys(modelCount).reduce((a, b) => 
                modelCount[a] > modelCount[b] ? a : b
            );
        },
        
        /**
         * 获取最常用的风格
         * @returns {string} 风格名称
         */
        getMostUsedStyle() {
            if (this.generationHistory.length === 0) return '-';
            
            const styleCount = {};
            this.generationHistory.forEach(item => {
                styleCount[item.styleName] = (styleCount[item.styleName] || 0) + 1;
            });
            
            return Object.keys(styleCount).reduce((a, b) => 
                styleCount[a] > styleCount[b] ? a : b
            );
        },
        
        /**
         * 获取平均质量评分
         * @returns {number} 平均评分
         */
        getAverageQuality() {
            if (this.generationHistory.length === 0) return 0;
            
            const total = this.generationHistory.reduce((sum, item) => sum + item.quality, 0);
            return Math.round(total / this.generationHistory.length);
        },
        
        /**
         * 保存API密钥
         */
        saveAPIKeys() {
            try {
                // 更新API配置管理器
                window.apiConfigManager.setAPIKey('openai', this.apiKeys.openai);
                window.apiConfigManager.setAPIKey('stability', this.apiKeys.stability);
                window.apiConfigManager.setAPIKey('midjourney', this.apiKeys.midjourney);
                
                // 保存到本地存储
                localStorage.setItem('meme-generator-api-keys', JSON.stringify(this.apiKeys));
                this.showNotification('API配置已保存', 'success');
            } catch (error) {
                console.error('保存API配置失败:', error);
                this.showNotification('保存失败', 'error');
            }
        },
        
        /**
         * 加载API密钥
         */
        loadAPIKeys() {
            try {
                const saved = localStorage.getItem('meme-generator-api-keys');
                if (saved) {
                    this.apiKeys = JSON.parse(saved);
                    // 更新API配置管理器
                    window.apiConfigManager.setAPIKey('openai', this.apiKeys.openai);
                    window.apiConfigManager.setAPIKey('stability', this.apiKeys.stability);
                    window.apiConfigManager.setAPIKey('midjourney', this.apiKeys.midjourney);
                }
            } catch (error) {
                console.error('加载API配置失败:', error);
            }
        },
        
        /**
         * 清空API密钥
         */
        clearAPIKeys() {
            this.apiKeys = {
                openai: '',
                stability: '',
                midjourney: ''
            };
            localStorage.removeItem('meme-generator-api-keys');
            this.showNotification('API配置已清空', 'success');
        },
        
        /**
         * 测试API连接
         */
        async testAPIConnection() {
            this.showNotification('正在测试API连接...', 'info');
            
            const results = [];
            
            if (this.apiKeys.openai) {
                const success = await window.apiConfigManager.testConnection('openai');
                results.push(`OpenAI: ${success ? '✅' : '❌'}`);
            }
            
            if (this.apiKeys.stability) {
                const success = await window.apiConfigManager.testConnection('stability');
                results.push(`Stability AI: ${success ? '✅' : '❌'}`);
            }
            
            if (this.apiKeys.midjourney) {
                const success = await window.apiConfigManager.testConnection('midjourney');
                results.push(`Midjourney: ${success ? '✅' : '❌'}`);
            }
            
            if (results.length === 0) {
                this.showNotification('请先配置API密钥', 'error');
            } else {
                this.showNotification(`连接测试结果: ${results.join(', ')}`, 'info');
            }
        },
        
        /**
         * 验证自定义API表单
         */
        validateCustomAPIForm() {
            const errors = {};
            
            if (!this.customAPIForm.name.trim()) {
                errors.name = '请输入接口名称';
            }
            
            if (!this.customAPIForm.method) {
                errors.method = '请选择请求方法';
            }
            
            if (!this.customAPIForm.endpoint.trim()) {
                errors.endpoint = '请输入API端点';
            } else {
                try {
                    new URL(this.customAPIForm.endpoint);
                } catch (e) {
                    errors.endpoint = '请输入有效的URL地址';
                }
            }
            
            if (this.customAPIForm.parameters.trim()) {
                try {
                    JSON.parse(this.customAPIForm.parameters);
                } catch (e) {
                    errors.parameters = '请输入有效的JSON格式';
                }
            }
            
            this.customAPIForm.errors = errors;
            return Object.keys(errors).length === 0;
        },
        
        /**
         * 测试自定义API接口
         */
        async testCustomAPI() {
            if (!this.validateCustomAPIForm()) {
                this.showNotification('请检查表单输入', 'error');
                return;
            }
            
            this.isTestingCustomAPI = true;
            
            try {
                const testParams = {
                    description: '测试图片生成',
                    size: '512x512',
                    style: 'cute',
                    steps: 20,
                    guidance: 7
                };
                
                const result = await this.callCustomAPI(this.customAPIForm, testParams);
                
                if (result.success) {
                    this.showNotification('API接口测试成功！', 'success');
                } else {
                    this.showNotification(`测试失败: ${result.error}`, 'error');
                }
            } catch (error) {
                this.showNotification(`测试失败: ${error.message}`, 'error');
            } finally {
                this.isTestingCustomAPI = false;
            }
        },
        
        /**
         * 调用自定义API
         */
        async callCustomAPI(apiConfig, params) {
            try {
                // 替换参数中的变量
                let requestBody = apiConfig.parameters;
                if (requestBody) {
                    const parsedParams = JSON.parse(requestBody);
                    const processedParams = this.replaceVariables(parsedParams, params);
                    requestBody = JSON.stringify(processedParams);
                }
                
                // 构建请求头
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                // 添加认证信息
                if (apiConfig.authType === 'bearer' && apiConfig.authValue) {
                    headers['Authorization'] = `Bearer ${apiConfig.authValue}`;
                } else if (apiConfig.authType === 'apikey' && apiConfig.authValue) {
                    headers['X-API-Key'] = apiConfig.authValue;
                } else if (apiConfig.authType === 'basic' && apiConfig.authValue) {
                    const encoded = btoa(apiConfig.authValue);
                    headers['Authorization'] = `Basic ${encoded}`;
                }
                
                // 发送请求
                const requestOptions = {
                    method: apiConfig.method,
                    headers: headers
                };
                
                if (apiConfig.method !== 'GET' && requestBody) {
                    requestOptions.body = requestBody;
                }
                
                const response = await fetch(apiConfig.endpoint, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // 提取图片URL
                let imageUrl = null;
                if (apiConfig.responsePath) {
                    imageUrl = this.getNestedValue(data, apiConfig.responsePath);
                }
                
                return {
                    success: true,
                    data: data,
                    imageUrl: imageUrl
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        },
        
        /**
         * 替换参数中的变量
         */
        replaceVariables(obj, params) {
            if (typeof obj === 'string') {
                return obj.replace(/\{\{(\w+)\}\}/g, (match, key) => {
                    return params[key] || match;
                });
            } else if (Array.isArray(obj)) {
                return obj.map(item => this.replaceVariables(item, params));
            } else if (typeof obj === 'object' && obj !== null) {
                const result = {};
                for (const [key, value] of Object.entries(obj)) {
                    result[key] = this.replaceVariables(value, params);
                }
                return result;
            }
            return obj;
        },
        
        /**
         * 获取嵌套对象的值
         */
        getNestedValue(obj, path) {
            return path.split('.').reduce((current, key) => {
                if (current && typeof current === 'object') {
                    // 处理数组索引
                    if (/^\d+$/.test(key)) {
                        return current[parseInt(key)];
                    }
                    return current[key];
                }
                return undefined;
            }, obj);
        },
        
        /**
         * 保存自定义API配置
         */
        saveCustomAPI() {
            if (!this.validateCustomAPIForm()) {
                this.showNotification('请检查表单输入', 'error');
                return;
            }
            
            const apiConfig = {
                name: this.customAPIForm.name.trim(),
                method: this.customAPIForm.method,
                endpoint: this.customAPIForm.endpoint.trim(),
                authType: this.customAPIForm.authType,
                authValue: this.customAPIForm.authValue,
                parameters: this.customAPIForm.parameters.trim(),
                responsePath: this.customAPIForm.responsePath.trim() || 'data.image_url',
                status: 'untested',
                lastError: null,
                createdAt: Date.now()
            };
            
            if (this.editingAPIIndex >= 0) {
                // 编辑现有配置
                this.customAPIs[this.editingAPIIndex] = apiConfig;
                this.editingAPIIndex = -1;
                this.showNotification('API配置已更新', 'success');
            } else {
                // 添加新配置
                this.customAPIs.push(apiConfig);
                this.showNotification('API配置已保存', 'success');
            }
            
            this.saveCustomAPIsToStorage();
            this.resetCustomAPIForm();
        },
        
        /**
         * 重置自定义API表单
         */
        resetCustomAPIForm() {
            this.customAPIForm = {
                name: '',
                method: '',
                endpoint: '',
                authType: 'none',
                authValue: '',
                parameters: '',
                responsePath: 'data.image_url',
                errors: {}
            };
            this.showCustomAPIForm = false;
            this.editingAPIIndex = -1;
        },
        
        /**
         * 编辑自定义API配置
         */
        editCustomAPI(index) {
            const api = this.customAPIs[index];
            this.customAPIForm = {
                name: api.name,
                method: api.method,
                endpoint: api.endpoint,
                authType: api.authType,
                authValue: api.authValue,
                parameters: api.parameters,
                responsePath: api.responsePath,
                errors: {}
            };
            this.editingAPIIndex = index;
            this.showCustomAPIForm = true;
        },
        
        /**
         * 删除自定义API配置
         */
        deleteCustomAPI(index) {
            if (confirm('确定要删除这个API配置吗？')) {
                this.customAPIs.splice(index, 1);
                this.saveCustomAPIsToStorage();
                this.showNotification('API配置已删除', 'success');
            }
        },
        
        /**
         * 测试单个自定义API
         */
        async testSingleCustomAPI(index) {
            const api = this.customAPIs[index];
            this.isTestingCustomAPI = true;
            
            try {
                const testParams = {
                    description: '测试图片生成',
                    size: '512x512',
                    style: 'cute',
                    steps: 20,
                    guidance: 7
                };
                
                const result = await this.callCustomAPI(api, testParams);
                
                if (result.success) {
                    api.status = 'active';
                    api.lastError = null;
                    this.showNotification(`${api.name} 测试成功！`, 'success');
                } else {
                    api.status = 'error';
                    api.lastError = result.error;
                    this.showNotification(`${api.name} 测试失败: ${result.error}`, 'error');
                }
                
                this.saveCustomAPIsToStorage();
            } catch (error) {
                api.status = 'error';
                api.lastError = error.message;
                this.showNotification(`${api.name} 测试失败: ${error.message}`, 'error');
                this.saveCustomAPIsToStorage();
            } finally {
                this.isTestingCustomAPI = false;
            }
        },
        
        /**
         * 保存自定义API配置到本地存储
         */
        saveCustomAPIsToStorage() {
            try {
                // 加密存储敏感信息
                const encryptedAPIs = this.customAPIs.map(api => ({
                    ...api,
                    authValue: api.authValue ? this.simpleEncrypt(api.authValue) : ''
                }));
                localStorage.setItem('meme_generator_custom_apis', JSON.stringify(encryptedAPIs));
            } catch (error) {
                console.error('保存自定义API配置失败:', error);
            }
        },
        
        /**
         * 从本地存储加载自定义API配置
         */
        loadCustomAPIs() {
            try {
                const stored = localStorage.getItem('meme_generator_custom_apis');
                if (stored) {
                    const encryptedAPIs = JSON.parse(stored);
                    this.customAPIs = encryptedAPIs.map(api => ({
                        ...api,
                        authValue: api.authValue ? this.simpleDecrypt(api.authValue) : ''
                    }));
                }
            } catch (error) {
                console.error('加载自定义API配置失败:', error);
                this.customAPIs = [];
            }
        },
        
        /**
         * 简单加密（仅用于本地存储，不是真正的安全加密）
         */
        simpleEncrypt(text) {
            return btoa(encodeURIComponent(text));
        },
        
        /**
         * 简单解密
         */
        simpleDecrypt(encrypted) {
            try {
                return decodeURIComponent(atob(encrypted));
            } catch (error) {
                return '';
            }
        },
        
        /**
         * 导出自定义API配置
         */
        exportCustomAPIs() {
            if (this.customAPIs.length === 0) {
                this.showNotification('没有可导出的API配置', 'warning');
                return;
            }
            
            try {
                // 创建导出数据（不包含敏感信息）
                const exportData = {
                    version: '1.0',
                    exportTime: new Date().toISOString(),
                    apis: this.customAPIs.map(api => ({
                        name: api.name,
                        method: api.method,
                        endpoint: api.endpoint,
                        authType: api.authType,
                        // 不导出实际的认证值，只导出占位符
                        authValue: api.authValue ? '[需要重新配置]' : '',
                        parameters: api.parameters,
                        responsePath: api.responsePath
                    }))
                };
                
                // 创建下载链接
                const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `meme-generator-apis-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showNotification('API配置已导出', 'success');
            } catch (error) {
                this.showNotification(`导出失败: ${error.message}`, 'error');
            }
        },
        
        /**
         * 导入自定义API配置
         */
        importCustomAPIs() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = (event) => {
                const file = event.target.files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const importData = JSON.parse(e.target.result);
                        
                        // 验证导入数据格式
                        if (!importData.apis || !Array.isArray(importData.apis)) {
                            throw new Error('无效的配置文件格式');
                        }
                        
                        // 验证每个API配置
                        const validAPIs = [];
                        for (const api of importData.apis) {
                            if (api.name && api.method && api.endpoint) {
                                validAPIs.push({
                                    name: api.name,
                                    method: api.method,
                                    endpoint: api.endpoint,
                                    authType: api.authType || 'none',
                                    authValue: '', // 导入时清空认证信息
                                    parameters: api.parameters || '',
                                    responsePath: api.responsePath || 'data.image_url',
                                    status: 'untested',
                                    lastError: null,
                                    createdAt: Date.now()
                                });
                            }
                        }
                        
                        if (validAPIs.length === 0) {
                            throw new Error('没有找到有效的API配置');
                        }
                        
                        // 询问是否替换现有配置
                        const replace = confirm(
                            `找到 ${validAPIs.length} 个有效配置。\n` +
                            `是否替换现有配置？\n` +
                            `点击"确定"替换，点击"取消"追加到现有配置。`
                        );
                        
                        if (replace) {
                            this.customAPIs = validAPIs;
                        } else {
                            this.customAPIs.push(...validAPIs);
                        }
                        
                        this.saveCustomAPIsToStorage();
                        this.showNotification(
                            `成功导入 ${validAPIs.length} 个API配置${replace ? '（已替换）' : '（已追加）'}`,
                            'success'
                        );
                        
                    } catch (error) {
                        this.showNotification(`导入失败: ${error.message}`, 'error');
                    }
                };
                reader.readAsText(file);
            };
            input.click();
        },
        
        /**
         * 清空所有自定义API配置
         */
        clearAllCustomAPIs() {
            if (this.customAPIs.length === 0) {
                this.showNotification('没有可清空的API配置', 'warning');
                return;
            }
            
            if (confirm(`确定要清空所有 ${this.customAPIs.length} 个API配置吗？此操作不可恢复。`)) {
                this.customAPIs = [];
                this.saveCustomAPIsToStorage();
                this.showNotification('所有API配置已清空', 'success');
            }
        },
        
        /**
         * 复制API配置
         */
        duplicateCustomAPI(index) {
            const api = this.customAPIs[index];
            const duplicatedAPI = {
                ...api,
                name: `${api.name} (副本)`,
                status: 'untested',
                lastError: null,
                createdAt: Date.now()
            };
            
            this.customAPIs.push(duplicatedAPI);
            this.saveCustomAPIsToStorage();
            this.showNotification('API配置已复制', 'success');
        },
        
        /**
         * 获取API配置状态的显示文本
         */
        getAPIStatusText(status) {
            const statusMap = {
                'untested': '未测试',
                'active': '正常',
                'error': '错误'
            };
            return statusMap[status] || '未知';
        },
        
        /**
         * 获取API配置状态的样式类
         */
        getAPIStatusClass(status) {
            const classMap = {
                'untested': 'bg-gray-100 text-gray-600',
                'active': 'bg-green-100 text-green-600',
                'error': 'bg-red-100 text-red-600'
            };
            return classMap[status] || 'bg-gray-100 text-gray-600';
        },
        
        /**
         * 重置所有设置
         */
        resetAll() {
            this.description = '';
            this.selectedStyle = 'cute';
            this.selectedModels = ['dalle3'];
            this.parameters = {
                size: '512x512',
                steps: 30,
                guidance: 7,
                negativePrompt: ''
            };
            this.generatedImage = null;
            this.finalImage = null;
            this.imageQuality = null;
            this.showParallelResults = false;
            this.parallelResults = [];
            this.textSettings = {
                topText: '',
                bottomText: '',
                fontSize: 40,
                color: '#FFFFFF',
                shadowBlur: 3
            };
            this.showNotification('已重置所有设置', 'success');
        }
    }
}).mount('#app');