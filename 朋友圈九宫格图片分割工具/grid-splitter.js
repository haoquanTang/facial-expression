/**
 * 朋友圈九宫格图片分割工具
 * 主要功能：图片上传、分割、美化、打包下载
 */
class GridSplitter {
    constructor() {
        // 初始化DOM元素
        this.initElements();
        // 初始化事件监听
        this.initEventListeners();
        // 初始化配置
        this.initConfig();
        // 存储原始图片和分割结果
        this.originalImage = null;
        this.splitImages = [];
    }

    /**
     * 初始化DOM元素引用
     */
    initElements() {
        // 上传相关
        this.uploadArea = document.getElementById('uploadArea');
        this.imageInput = document.getElementById('imageInput');
        this.originalPreview = document.getElementById('originalPreview');
        this.originalImage = document.getElementById('originalImage');
        this.imageInfo = document.getElementById('imageInfo');
        
        // 预览相关
        this.splitPreview = document.getElementById('splitPreview');
        this.previewGrid = document.getElementById('previewGrid');
        this.previewBtn = document.getElementById('previewBtn');
        
        // 下载相关
        this.downloadBtn = document.getElementById('downloadBtn');
        this.downloadIcon = document.getElementById('downloadIcon');
        this.downloadText = document.getElementById('downloadText');
        
        // 控制面板
        this.splitModeInputs = document.querySelectorAll('input[name="splitMode"]');
        this.borderWidth = document.getElementById('borderWidth');
        this.borderWidthValue = document.getElementById('borderWidthValue');
        this.borderColor = document.getElementById('borderColor');
        this.borderRadius = document.getElementById('borderRadius');
        this.borderRadiusValue = document.getElementById('borderRadiusValue');
        this.watermarkText = document.getElementById('watermarkText');
        this.watermarkPosition = document.getElementById('watermarkPosition');
        this.resetBtn = document.getElementById('resetBtn');
        
        // 通知
        this.notification = document.getElementById('notification');
        this.notificationText = document.getElementById('notification-text');
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 文件上传事件
        this.uploadArea.addEventListener('click', () => this.imageInput.click());
        this.imageInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // 拖拽上传事件
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // 控制面板事件
        this.splitModeInputs.forEach(input => {
            input.addEventListener('change', () => this.updatePreview());
        });
        
        this.borderWidth.addEventListener('input', (e) => {
            this.borderWidthValue.textContent = e.target.value + 'px';
            this.updatePreview();
        });
        
        this.borderRadius.addEventListener('input', (e) => {
            this.borderRadiusValue.textContent = e.target.value + 'px';
            this.updatePreview();
        });
        
        this.borderColor.addEventListener('change', () => this.updatePreview());
        this.watermarkText.addEventListener('input', () => this.updatePreview());
        this.watermarkPosition.addEventListener('change', () => this.updatePreview());
        
        // 按钮事件
        this.previewBtn.addEventListener('click', () => this.generatePreview());
        this.downloadBtn.addEventListener('click', () => this.downloadImages());
        this.resetBtn.addEventListener('click', () => this.resetSettings());
    }

    /**
     * 初始化默认配置
     */
    initConfig() {
        this.config = {
            splitMode: 'grid3x3',
            borderWidth: 2,
            borderColor: '#ffffff',
            borderRadius: 0,
            watermarkText: '',
            watermarkPosition: 'none'
        };
    }

    /**
     * 处理拖拽悬停事件
     */
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    /**
     * 处理拖拽离开事件
     */
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    /**
     * 处理拖拽放置事件
     */
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    /**
     * 处理文件选择事件
     */
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    /**
     * 处理上传的文件
     */
    processFile(file) {
        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            this.showNotification('请选择图片文件！', 'error');
            return;
        }
        
        // 验证文件大小（限制10MB）
        if (file.size > 10 * 1024 * 1024) {
            this.showNotification('图片文件过大，请选择小于10MB的图片！', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.loadImage(e.target.result);
        };
        reader.readAsDataURL(file);
    }

    /**
     * 加载图片并显示预览
     */
    loadImage(src) {
        const img = new Image();
        img.onload = () => {
            this.originalImage = img;
            this.showOriginalPreview(src, img);
            this.previewBtn.disabled = false;
            this.generatePreview();
        };
        img.onerror = () => {
            this.showNotification('图片加载失败，请重试！', 'error');
        };
        img.src = src;
    }

    /**
     * 显示原图预览
     */
    showOriginalPreview(src, img) {
        document.getElementById('originalImage').src = src;
        this.imageInfo.textContent = `尺寸: ${img.width} × ${img.height} 像素`;
        this.originalPreview.classList.remove('hidden');
    }

    /**
     * 获取当前配置
     */
    getCurrentConfig() {
        return {
            splitMode: document.querySelector('input[name="splitMode"]:checked').value,
            borderWidth: parseInt(this.borderWidth.value),
            borderColor: this.borderColor.value,
            borderRadius: parseInt(this.borderRadius.value),
            watermarkText: this.watermarkText.value.trim(),
            watermarkPosition: this.watermarkPosition.value
        };
    }

    /**
     * 生成分割预览
     */
    async generatePreview() {
        if (!this.originalImage) return;
        
        this.showLoading(true);
        
        try {
            const config = this.getCurrentConfig();
            this.splitImages = await this.splitImage(this.originalImage, config);
            this.displayPreview(config.splitMode);
            this.downloadBtn.disabled = false;
            this.showNotification('预览生成成功！', 'success');
        } catch (error) {
            console.error('生成预览失败:', error);
            this.showNotification('生成预览失败，请重试！', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 核心图片分割算法
     */
    async splitImage(img, config) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // 计算分割参数
        const splitInfo = this.getSplitInfo(config.splitMode);
        const { rows, cols, pieces } = splitInfo;
        
        // 确保图片是正方形
        const size = Math.min(img.width, img.height);
        const offsetX = (img.width - size) / 2;
        const offsetY = (img.height - size) / 2;
        
        // 计算每个分割块的尺寸
        const pieceWidth = size / cols;
        const pieceHeight = size / rows;
        
        const results = [];
        
        for (let i = 0; i < pieces.length; i++) {
            const piece = pieces[i];
            
            // 设置画布尺寸
            canvas.width = pieceWidth + config.borderWidth * 2;
            canvas.height = pieceHeight + config.borderWidth * 2;
            
            // 清空画布
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // 绘制边框背景
            if (config.borderWidth > 0) {
                ctx.fillStyle = config.borderColor;
                this.drawRoundedRect(ctx, 0, 0, canvas.width, canvas.height, config.borderRadius);
                ctx.fill();
            }
            
            // 绘制图片片段
            ctx.save();
            
            // 创建圆角裁剪路径
            if (config.borderRadius > 0) {
                this.drawRoundedRect(
                    ctx, 
                    config.borderWidth, 
                    config.borderWidth, 
                    pieceWidth, 
                    pieceHeight, 
                    Math.max(0, config.borderRadius - config.borderWidth)
                );
                ctx.clip();
            }
            
            // 绘制图片
            ctx.drawImage(
                img,
                offsetX + piece.x * pieceWidth, offsetY + piece.y * pieceHeight,
                pieceWidth, pieceHeight,
                config.borderWidth, config.borderWidth,
                pieceWidth, pieceHeight
            );
            
            ctx.restore();
            
            // 添加水印
            if (config.watermarkText && config.watermarkPosition !== 'none') {
                this.drawWatermark(ctx, config.watermarkText, config.watermarkPosition, canvas.width, canvas.height);
            }
            
            // 转换为blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.9);
            });
            
            results.push({
                blob: blob,
                filename: `${String(i + 1).padStart(2, '0')}.jpg`,
                dataUrl: canvas.toDataURL('image/jpeg', 0.9)
            });
        }
        
        return results;
    }

    /**
     * 获取分割信息
     */
    getSplitInfo(mode) {
        switch (mode) {
            case 'grid3x3':
                return {
                    rows: 3, cols: 3,
                    pieces: [
                        {x: 0, y: 0}, {x: 1, y: 0}, {x: 2, y: 0},
                        {x: 0, y: 1}, {x: 1, y: 1}, {x: 2, y: 1},
                        {x: 0, y: 2}, {x: 1, y: 2}, {x: 2, y: 2}
                    ]
                };
            case 'top3':
                return {
                    rows: 1, cols: 3,
                    pieces: [{x: 0, y: 0}, {x: 1, y: 0}, {x: 2, y: 0}]
                };
            case 'left3':
                return {
                    rows: 3, cols: 1,
                    pieces: [{x: 0, y: 0}, {x: 0, y: 1}, {x: 0, y: 2}]
                };
            case 'center':
                return {
                    rows: 3, cols: 3,
                    pieces: [
                        {x: 0, y: 0}, {x: 1, y: 0}, {x: 2, y: 0},
                        {x: 0, y: 1}, {x: 1, y: 1}, {x: 2, y: 1},
                        {x: 0, y: 2}, {x: 1, y: 2}, {x: 2, y: 2}
                    ]
                };
            default:
                return this.getSplitInfo('grid3x3');
        }
    }

    /**
     * 绘制圆角矩形路径
     */
    drawRoundedRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    /**
     * 绘制水印
     */
    drawWatermark(ctx, text, position, canvasWidth, canvasHeight) {
        ctx.save();
        
        // 设置水印样式
        const fontSize = Math.max(12, Math.min(canvasWidth, canvasHeight) * 0.05);
        ctx.font = `${fontSize}px Arial`;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.lineWidth = 1;
        
        // 测量文字尺寸
        const metrics = ctx.measureText(text);
        const textWidth = metrics.width;
        const textHeight = fontSize;
        
        // 计算位置
        let x, y;
        const padding = 10;
        
        switch (position) {
            case 'top-left':
                x = padding;
                y = padding + textHeight;
                break;
            case 'top-right':
                x = canvasWidth - textWidth - padding;
                y = padding + textHeight;
                break;
            case 'bottom-left':
                x = padding;
                y = canvasHeight - padding;
                break;
            case 'bottom-right':
                x = canvasWidth - textWidth - padding;
                y = canvasHeight - padding;
                break;
            case 'center':
                x = (canvasWidth - textWidth) / 2;
                y = (canvasHeight + textHeight) / 2;
                break;
            default:
                return;
        }
        
        // 绘制水印
        ctx.strokeText(text, x, y);
        ctx.fillText(text, x, y);
        
        ctx.restore();
    }

    /**
     * 显示分割预览
     */
    displayPreview(splitMode) {
        // 清空预览容器
        this.previewGrid.innerHTML = '';
        
        // 设置网格样式
        this.previewGrid.className = `preview-grid ${this.getGridClass(splitMode)}`;
        
        // 添加预览图片
        this.splitImages.forEach((imageData, index) => {
            const img = document.createElement('img');
            img.src = imageData.dataUrl;
            img.className = 'w-full h-full object-cover rounded';
            img.alt = `分割图片 ${index + 1}`;
            
            if (splitMode === 'center' && index === 4) {
                img.className += ' center-piece';
            }
            
            this.previewGrid.appendChild(img);
        });
        
        this.splitPreview.classList.remove('hidden');
    }

    /**
     * 获取网格CSS类名
     */
    getGridClass(splitMode) {
        switch (splitMode) {
            case 'grid3x3':
            case 'center':
                return 'grid-3x3';
            case 'top3':
                return 'grid-1x3';
            case 'left3':
                return 'grid-3x1';
            default:
                return 'grid-3x3';
        }
    }

    /**
     * 更新预览（实时预览）
     */
    updatePreview() {
        if (this.originalImage && this.splitImages.length > 0) {
            // 延迟更新以避免频繁操作
            clearTimeout(this.updateTimer);
            this.updateTimer = setTimeout(() => {
                this.generatePreview();
            }, 300);
        }
    }

    /**
     * 下载分割后的图片
     */
    async downloadImages() {
        if (this.splitImages.length === 0) {
            this.showNotification('请先生成预览！', 'error');
            return;
        }
        
        this.showLoading(true, '正在打包...');
        
        try {
            const zip = new JSZip();
            
            // 添加图片到压缩包
            for (const imageData of this.splitImages) {
                zip.file(imageData.filename, imageData.blob);
            }
            
            // 生成压缩包
            const content = await zip.generateAsync({type: 'blob'});
            
            // 下载文件
            const url = URL.createObjectURL(content);
            const a = document.createElement('a');
            a.href = url;
            a.download = `九宫格分割_${new Date().getTime()}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('下载成功！', 'success');
        } catch (error) {
            console.error('下载失败:', error);
            this.showNotification('下载失败，请重试！', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 重置所有设置
     */
    resetSettings() {
        // 重置表单
        document.querySelector('input[name="splitMode"][value="grid3x3"]').checked = true;
        this.borderWidth.value = 2;
        this.borderWidthValue.textContent = '2px';
        this.borderColor.value = '#ffffff';
        this.borderRadius.value = 0;
        this.borderRadiusValue.textContent = '0px';
        this.watermarkText.value = '';
        this.watermarkPosition.value = 'none';
        
        // 更新预览
        this.updatePreview();
        
        this.showNotification('设置已重置！', 'success');
    }

    /**
     * 显示/隐藏加载状态
     */
    showLoading(show, text = '处理中...') {
        if (show) {
            this.downloadIcon.classList.add('loading');
            this.downloadText.textContent = text;
            this.downloadBtn.disabled = true;
        } else {
            this.downloadIcon.classList.remove('loading');
            this.downloadText.textContent = '打包下载';
            this.downloadBtn.disabled = false;
        }
    }

    /**
     * 显示通知消息
     */
    showNotification(message, type = 'success') {
        this.notificationText.textContent = message;
        
        // 设置通知样式
        const notificationDiv = this.notification.querySelector('div');
        notificationDiv.className = `px-6 py-3 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        
        // 显示通知
        this.notification.classList.add('show');
        
        // 3秒后自动隐藏
        setTimeout(() => {
            this.notification.classList.remove('show');
        }, 3000);
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new GridSplitter();
});

// 防止页面意外刷新时丢失数据
window.addEventListener('beforeunload', (e) => {
    const splitter = window.gridSplitter;
    if (splitter && splitter.originalImage) {
        e.preventDefault();
        e.returnValue = '确定要离开吗？未保存的图片将会丢失。';
    }
});