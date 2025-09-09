/**
 * 个性代码雨生成器 - 核心动画逻辑
 * 实现仿《黑客帝国》风格的代码雨特效
 */

class MatrixRain {
    constructor() {
        // Canvas相关
        this.canvas = document.getElementById('matrix-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // 动画参数
        this.animationId = null;
        this.isRunning = false;
        this.columns = [];
        this.fontSize = 14;
        this.columnWidth = this.fontSize;
        
        // 配置参数
        this.config = {
            charset: 'matrix',
            textColor: '#00ff00',
            backgroundColor: '#000000',
            speed: 50,
            density: 50,
            opacity: 80,
            watermarkText: '',
            watermarkPosition: 'none'
        };
        
        // 字符集定义
        this.charsets = {
            english: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            chinese: '的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严',
            numbers: '0123456789',
            mixed: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?',
            matrix: 'ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        };
        
        // GIF录制相关
        this.gif = null;
        this.isRecording = false;
        this.recordStartTime = 0;
        this.maxRecordTime = 10000; // 最大录制时间10秒
        
        this.init();
    }
    
    /**
     * 初始化函数
     */
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.setupColumns();
        this.updateWatermark();
        
        // 默认启动动画
        this.start();
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.setupColumns();
        });
    }
    
    /**
     * 设置Canvas尺寸
     */
    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // 计算列数
        this.numColumns = Math.floor(this.canvas.width / this.columnWidth);
    }
    
    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 控制面板切换
        document.getElementById('toggle-panel').addEventListener('click', () => {
            const panel = document.getElementById('control-panel');
            panel.classList.toggle('hidden');
        });
        
        // 字符集选择
        document.getElementById('charset').addEventListener('change', (e) => {
            this.config.charset = e.target.value;
        });
        
        // 颜色设置
        document.getElementById('text-color').addEventListener('change', (e) => {
            this.config.textColor = e.target.value;
        });
        
        document.getElementById('bg-color').addEventListener('change', (e) => {
            this.config.backgroundColor = e.target.value;
        });
        
        // 速度设置
        document.getElementById('speed').addEventListener('input', (e) => {
            this.config.speed = parseInt(e.target.value);
            document.getElementById('speed-value').textContent = e.target.value;
        });
        
        // 密度设置
        document.getElementById('density').addEventListener('input', (e) => {
            this.config.density = parseInt(e.target.value);
            document.getElementById('density-value').textContent = e.target.value;
            this.setupColumns(); // 重新设置列
        });
        
        // 透明度设置
        document.getElementById('opacity').addEventListener('input', (e) => {
            this.config.opacity = parseInt(e.target.value);
            document.getElementById('opacity-value').textContent = e.target.value;
        });
        
        // 水印设置
        document.getElementById('watermark-text').addEventListener('input', (e) => {
            this.config.watermarkText = e.target.value;
            this.updateWatermark();
        });
        
        document.getElementById('watermark-position').addEventListener('change', (e) => {
            this.config.watermarkPosition = e.target.value;
            this.updateWatermark();
        });
        
        // 控制按钮
        document.getElementById('start-btn').addEventListener('click', () => this.start());
        document.getElementById('stop-btn').addEventListener('click', () => this.stop());
        document.getElementById('screenshot-btn').addEventListener('click', () => this.takeScreenshot());
        document.getElementById('record-btn').addEventListener('click', () => this.startRecording());
        document.getElementById('stop-record-btn').addEventListener('click', () => this.stopRecording());
        document.getElementById('reset-btn').addEventListener('click', () => this.resetConfig());
        document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case ' ': // 空格键暂停/继续
                    e.preventDefault();
                    this.isRunning ? this.stop() : this.start();
                    break;
                case 'f': // F键全屏
                case 'F':
                    this.toggleFullscreen();
                    break;
                case 's': // S键截图
                case 'S':
                    this.takeScreenshot();
                    break;
            }
        });
    }
    
    /**
     * 设置列数据结构
     */
    setupColumns() {
        this.columns = [];
        const density = this.config.density / 100;
        
        for (let i = 0; i < this.numColumns; i++) {
            // 根据密度随机决定是否创建列
            if (Math.random() < density) {
                this.columns.push({
                    x: i * this.columnWidth,
                    y: Math.random() * this.canvas.height,
                    chars: [],
                    speed: (Math.random() * 0.5 + 0.5) * (this.config.speed / 50),
                    length: Math.floor(Math.random() * 20) + 10
                });
            }
        }
    }
    
    /**
     * 获取随机字符
     */
    getRandomChar() {
        const charset = this.charsets[this.config.charset];
        return charset[Math.floor(Math.random() * charset.length)];
    }
    
    /**
     * 更新水印显示
     */
    updateWatermark() {
        const watermark = document.getElementById('watermark');
        
        if (this.config.watermarkPosition === 'none' || !this.config.watermarkText) {
            watermark.classList.add('hidden');
        } else {
            watermark.classList.remove('hidden');
            watermark.textContent = this.config.watermarkText;
            watermark.className = `watermark ${this.config.watermarkPosition}`;
        }
    }
    
    /**
     * 动画渲染函数
     */
    render() {
        // 设置背景
        this.ctx.fillStyle = this.config.backgroundColor;
        this.ctx.globalAlpha = 0.05; // 创建拖尾效果
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 设置字符样式
        this.ctx.globalAlpha = this.config.opacity / 100;
        this.ctx.fillStyle = this.config.textColor;
        this.ctx.font = `${this.fontSize}px 'Courier New', monospace`;
        
        // 渲染每一列
        this.columns.forEach(column => {
            // 更新列位置
            column.y += column.speed;
            
            // 如果列超出屏幕，重置位置
            if (column.y > this.canvas.height + column.length * this.fontSize) {
                column.y = -column.length * this.fontSize;
                column.speed = (Math.random() * 0.5 + 0.5) * (this.config.speed / 50);
            }
            
            // 生成字符
            if (column.chars.length < column.length) {
                column.chars.push(this.getRandomChar());
            }
            
            // 渲染字符
            column.chars.forEach((char, index) => {
                const charY = column.y - index * this.fontSize;
                
                if (charY > -this.fontSize && charY < this.canvas.height + this.fontSize) {
                    // 头部字符更亮
                    if (index === 0) {
                        this.ctx.fillStyle = '#ffffff';
                    } else {
                        // 渐变效果
                        const alpha = Math.max(0, 1 - index / column.length);
                        this.ctx.fillStyle = this.hexToRgba(this.config.textColor, alpha * (this.config.opacity / 100));
                    }
                    
                    this.ctx.fillText(char, column.x, charY);
                    
                    // 随机改变字符
                    if (Math.random() < 0.02) {
                        column.chars[index] = this.getRandomChar();
                    }
                }
            });
        });
        
        // 继续动画循环
        if (this.isRunning) {
            this.animationId = requestAnimationFrame(() => this.render());
            
            // GIF录制
            if (this.isRecording) {
                this.captureFrame();
            }
        }
    }
    
    /**
     * 十六进制颜色转RGBA
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    /**
     * 开始动画
     */
    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.render();
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
        }
    }
    
    /**
     * 停止动画
     */
    stop() {
        if (this.isRunning) {
            this.isRunning = false;
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
            }
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
        }
    }
    
    /**
     * 截图功能
     */
    async takeScreenshot() {
        try {
            const canvas = await html2canvas(document.body, {
                backgroundColor: null,
                scale: 1,
                logging: false
            });
            
            // 创建下载链接
            const link = document.createElement('a');
            link.download = `matrix-rain-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
            
            // 显示成功提示
            this.showNotification('截图已保存！');
        } catch (error) {
            console.error('截图失败:', error);
            this.showNotification('截图失败，请重试');
        }
    }
    
    /**
     * 开始GIF录制
     */
    startRecording() {
        if (this.isRecording) return;
        
        this.isRecording = true;
        this.recordStartTime = Date.now();
        
        // 初始化GIF
        this.gif = new GIF({
            workers: 2,
            quality: 10,
            width: this.canvas.width,
            height: this.canvas.height
        });
        
        // 更新UI
        document.getElementById('record-btn').disabled = true;
        document.getElementById('stop-record-btn').disabled = false;
        document.getElementById('record-btn').classList.add('recording');
        
        this.showNotification('开始录制GIF...');
        
        // 自动停止录制（10秒后）
        setTimeout(() => {
            if (this.isRecording) {
                this.stopRecording();
            }
        }, this.maxRecordTime);
    }
    
    /**
     * 捕获帧用于GIF
     */
    captureFrame() {
        if (!this.isRecording || !this.gif) return;
        
        const now = Date.now();
        if (now - this.recordStartTime > this.maxRecordTime) {
            this.stopRecording();
            return;
        }
        
        // 每100ms捕获一帧
        if (now % 100 < 16) {
            this.gif.addFrame(this.canvas, { delay: 100 });
        }
    }
    
    /**
     * 停止GIF录制
     */
    stopRecording() {
        if (!this.isRecording) return;
        
        this.isRecording = false;
        
        // 更新UI
        document.getElementById('record-btn').disabled = false;
        document.getElementById('stop-record-btn').disabled = true;
        document.getElementById('record-btn').classList.remove('recording');
        
        this.showNotification('正在生成GIF...');
        
        // 渲染GIF
        this.gif.on('finished', (blob) => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = `matrix-rain-${Date.now()}.gif`;
            link.href = url;
            link.click();
            
            this.showNotification('GIF已保存！');
        });
        
        this.gif.render();
    }
    
    /**
     * 重置配置
     */
    resetConfig() {
        // 重置配置参数
        this.config = {
            charset: 'matrix',
            textColor: '#00ff00',
            backgroundColor: '#000000',
            speed: 50,
            density: 50,
            opacity: 80,
            watermarkText: '',
            watermarkPosition: 'none'
        };
        
        // 更新UI控件
        document.getElementById('charset').value = 'matrix';
        document.getElementById('text-color').value = '#00ff00';
        document.getElementById('bg-color').value = '#000000';
        document.getElementById('speed').value = '50';
        document.getElementById('density').value = '50';
        document.getElementById('opacity').value = '80';
        document.getElementById('watermark-text').value = '';
        document.getElementById('watermark-position').value = 'none';
        
        // 更新显示值
        document.getElementById('speed-value').textContent = '50';
        document.getElementById('density-value').textContent = '50';
        document.getElementById('opacity-value').textContent = '80';
        
        // 重新设置列和水印
        this.setupColumns();
        this.updateWatermark();
        
        this.showNotification('参数已重置');
    }
    
    /**
     * 切换全屏模式
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('无法进入全屏模式:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    /**
     * 显示通知
     */
    showNotification(message) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 20px;
            border: 1px solid #00ff00;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            z-index: 10000;
            animation: fadeInOut 2s ease-in-out;
        `;
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        // 2秒后移除通知
        setTimeout(() => {
            document.body.removeChild(notification);
            document.head.removeChild(style);
        }, 2000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new MatrixRain();
});