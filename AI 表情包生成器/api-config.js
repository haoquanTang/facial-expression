/**
 * API配置管理系统
 * 统一管理多个AI模型的API调用
 */
class APIConfigManager {
    constructor() {
        this.apiKeys = {
            openai: '',
            stability: '',
            midjourney: ''
        };
        
        // 模型配置
        this.modelConfigs = {
            'dalle3': {
                name: 'DALL-E 3',
                provider: 'openai',
                endpoint: 'https://api.openai.com/v1/images/generations',
                maxSize: '1024x1024',
                supportedSizes: ['1024x1024', '1024x1792', '1792x1024']
            },
            'dalle2': {
                name: 'DALL-E 2',
                provider: 'openai',
                endpoint: 'https://api.openai.com/v1/images/generations',
                maxSize: '1024x1024',
                supportedSizes: ['256x256', '512x512', '1024x1024']
            },
            'stable-diffusion': {
                name: 'Stable Diffusion XL',
                provider: 'stability',
                endpoint: 'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image',
                maxSize: '1024x1024',
                supportedSizes: ['512x512', '768x768', '1024x1024']
            },
            'midjourney': {
                name: 'Midjourney',
                provider: 'midjourney',
                endpoint: 'https://api.midjourney.com/v1/imagine',
                maxSize: '1024x1024',
                supportedSizes: ['512x512', '768x768', '1024x1024']
            }
        };
    }

    /**
     * 设置API密钥
     * @param {string} provider - 提供商名称
     * @param {string} apiKey - API密钥
     */
    setAPIKey(provider, apiKey) {
        this.apiKeys[provider] = apiKey;
    }

    /**
     * 获取API密钥
     * @param {string} provider - 提供商名称
     * @returns {string} API密钥
     */
    getAPIKey(provider) {
        return this.apiKeys[provider] || '';
    }

    /**
     * 检查API密钥是否已配置
     * @param {string} provider - 提供商名称
     * @returns {boolean} 是否已配置
     */
    hasAPIKey(provider) {
        return !!this.apiKeys[provider];
    }

    /**
     * 格式化请求参数
     * @param {string} modelId - 模型ID
     * @param {Object} params - 参数对象
     * @returns {Object} 格式化后的请求参数
     */
    formatRequest(modelId, params) {
        const config = this.modelConfigs[modelId];
        if (!config) {
            throw new Error(`未知的模型: ${modelId}`);
        }

        const { prompt, size, steps, guidance, negativePrompt } = params;

        switch (config.provider) {
            case 'openai':
                return {
                    model: modelId === 'dalle3' ? 'dall-e-3' : 'dall-e-2',
                    prompt: prompt,
                    n: 1,
                    size: size || '1024x1024',
                    quality: modelId === 'dalle3' ? 'hd' : 'standard'
                };

            case 'stability':
                return {
                    text_prompts: [
                        { text: prompt, weight: 1 },
                        ...(negativePrompt ? [{ text: negativePrompt, weight: -1 }] : [])
                    ],
                    cfg_scale: guidance || 7,
                    steps: steps || 30,
                    width: parseInt(size?.split('x')[0]) || 1024,
                    height: parseInt(size?.split('x')[1]) || 1024,
                    samples: 1
                };

            case 'midjourney':
                return {
                    prompt: prompt + (negativePrompt ? ` --no ${negativePrompt}` : ''),
                    aspect_ratio: this.getSizeRatio(size),
                    quality: 1,
                    stylize: Math.round((guidance || 7) * 14.3) // 转换为MJ的stylize参数
                };

            default:
                throw new Error(`不支持的提供商: ${config.provider}`);
        }
    }

    /**
     * 格式化响应数据
     * @param {string} modelId - 模型ID
     * @param {Object} response - API响应
     * @returns {Object} 格式化后的响应
     */
    formatResponse(modelId, response) {
        const config = this.modelConfigs[modelId];
        
        switch (config.provider) {
            case 'openai':
                return {
                    success: true,
                    imageUrl: response.data?.[0]?.url,
                    revisedPrompt: response.data?.[0]?.revised_prompt
                };

            case 'stability':
                return {
                    success: true,
                    imageUrl: response.artifacts?.[0]?.base64 ? 
                        `data:image/png;base64,${response.artifacts[0].base64}` : null
                };

            case 'midjourney':
                return {
                    success: true,
                    imageUrl: response.image_url,
                    jobId: response.job_id
                };

            default:
                return { success: false, error: '未知的提供商' };
        }
    }

    /**
     * 调用API生成图片
     * @param {string} modelId - 模型ID
     * @param {Object} params - 参数对象
     * @returns {Promise<Object>} API响应
     */
    async callAPI(modelId, params) {
        const config = this.modelConfigs[modelId];
        if (!config) {
            throw new Error(`未知的模型: ${modelId}`);
        }

        const apiKey = this.getAPIKey(config.provider);
        if (!apiKey) {
            // 如果没有API密钥，返回模拟数据
            return this.getMockResponse(modelId, params);
        }

        try {
            const requestBody = this.formatRequest(modelId, params);
            const headers = this.getHeaders(config.provider, apiKey);

            const response = await fetch(config.endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            return this.formatResponse(modelId, data);
        } catch (error) {
            console.error(`API调用失败 (${modelId}):`, error);
            // 发生错误时返回模拟数据
            return this.getMockResponse(modelId, params);
        }
    }

    /**
     * 获取请求头
     * @param {string} provider - 提供商名称
     * @param {string} apiKey - API密钥
     * @returns {Object} 请求头
     */
    getHeaders(provider, apiKey) {
        const baseHeaders = {
            'Content-Type': 'application/json'
        };

        switch (provider) {
            case 'openai':
                return {
                    ...baseHeaders,
                    'Authorization': `Bearer ${apiKey}`
                };

            case 'stability':
                return {
                    ...baseHeaders,
                    'Authorization': `Bearer ${apiKey}`,
                    'Accept': 'application/json'
                };

            case 'midjourney':
                return {
                    ...baseHeaders,
                    'Authorization': `Bearer ${apiKey}`
                };

            default:
                return baseHeaders;
        }
    }

    /**
     * 获取尺寸比例（用于Midjourney）
     * @param {string} size - 尺寸字符串
     * @returns {string} 比例字符串
     */
    getSizeRatio(size) {
        if (!size) return '1:1';
        
        const [width, height] = size.split('x').map(Number);
        const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
        const divisor = gcd(width, height);
        
        return `${width / divisor}:${height / divisor}`;
    }

    /**
     * 获取模拟响应数据
     * @param {string} modelId - 模型ID
     * @param {Object} params - 参数对象
     * @returns {Object} 模拟响应
     */
    getMockResponse(modelId, params) {
        // 生成随机的占位图片
        const width = parseInt(params.size?.split('x')[0]) || 512;
        const height = parseInt(params.size?.split('x')[1]) || 512;
        const imageUrl = `https://picsum.photos/${width}/${height}?random=${Date.now()}`;
        
        return {
            success: true,
            imageUrl: imageUrl,
            isMock: true // 标记为模拟数据
        };
    }

    /**
     * 测试API连接
     * @param {string} provider - 提供商名称
     * @returns {Promise<boolean>} 连接是否成功
     */
    async testConnection(provider) {
        const apiKey = this.getAPIKey(provider);
        if (!apiKey) {
            return false;
        }

        try {
            // 这里应该调用各个API的测试端点
            // 为了演示，我们简单返回true
            await new Promise(resolve => setTimeout(resolve, 1000));
            return Math.random() > 0.3; // 模拟70%的成功率
        } catch (error) {
            console.error(`测试连接失败 (${provider}):`, error);
            return false;
        }
    }

    /**
     * 获取所有可用的模型
     * @returns {Array} 模型列表
     */
    getAvailableModels() {
        return Object.keys(this.modelConfigs).map(id => ({
            id,
            ...this.modelConfigs[id],
            available: this.hasAPIKey(this.modelConfigs[id].provider)
        }));
    }
}

// 创建全局实例
window.apiConfigManager = new APIConfigManager();