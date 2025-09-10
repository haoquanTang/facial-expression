/**
 * 拉斯维加斯巨型球主控制器
 * 负责表情播放、动画控制、设置管理和用户交互
 */

class VegasSphere {
    constructor() {
        // 核心状态
        this.currentExpressionIndex = 0;
        this.isPlaying = true;
        this.playTimer = null;
        this.progressTimer = null;
        this.currentProgress = 0;
        
        // 设置配置
        this.settings = { ...DEFAULT_SETTINGS };
        
        // DOM元素引用
        this.elements = {};
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化应用
     */
    async init() {
        try {
            // 等待DOM加载完成
            if (document.readyState === 'loading') {
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }
            
            // 验证表情数据
            if (!validateExpressions()) {
                throw new Error('表情数据验证失败');
            }
            
            // 获取DOM元素
            this.getDOMElements();
            
            // 加载设置
            this.loadSettings();
            
            // 初始化UI
            this.initializeUI();
            
            // 绑定事件
            this.bindEvents();
            
            // 创建背景粒子
            this.createParticles();
            
            // 开始播放
            this.startPlayback();
            
            console.log('拉斯维加斯巨型球初始化完成');
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('应用初始化失败，请刷新页面重试');
        }
    }
    
    /**
     * 获取DOM元素引用
     */
    getDOMElements() {
        const elementIds = [
            'expressionEmoji', 'currentExpressionName', 'playStatus',
            'progressFill', 'timeDisplay', 'playPauseBtn', 'prevBtn', 'nextBtn',
            'speedSlider', 'speedValue', 'expressionList', 'settingsBtn',
            'settingsPanel', 'closeSettingsBtn', 'autoPlayToggle',
            'shuffleToggle', 'repeatToggle', 'brightnessSlider', 'brightnessValue',
            'glowEffectToggle', 'particlesToggle', 'transitionSlider',
            'transitionValue', 'particles-bg', 'megaSphere'
        ];
        
        elementIds.forEach(id => {
            this.elements[id] = document.getElementById(id);
            if (!this.elements[id]) {
                console.warn(`元素 ${id} 未找到`);
            }
        });
    }
    
    /**
     * 初始化用户界面
     */
    initializeUI() {
        // 创建表情选择按钮
        this.createExpressionButtons();
        
        // 设置初始表情
        this.setCurrentExpression(0);
        
        // 初始化控件状态
        this.updatePlayButton();
        this.updateSpeedDisplay();
        this.updateSettingsUI();
        
        // 应用主题
        this.applyTheme(this.settings.theme);
    }
    
    /**
     * 创建表情选择按钮
     */
    createExpressionButtons() {
        if (!this.elements.expressionList) return;
        
        this.elements.expressionList.innerHTML = '';
        
        EXPRESSIONS.forEach((expression, index) => {
            const button = document.createElement('button');
            button.className = 'expression-btn';
            button.textContent = expression.emoji;
            button.title = expression.name;
            button.dataset.index = index;
            
            button.addEventListener('click', () => {
                this.setCurrentExpression(index);
                this.restartPlayback();
            });
            
            this.elements.expressionList.appendChild(button);
        });
    }
    
    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 播放控制按钮
        this.elements.playPauseBtn?.addEventListener('click', () => this.togglePlayback());
        this.elements.prevBtn?.addEventListener('click', () => this.previousExpression());
        this.elements.nextBtn?.addEventListener('click', () => this.nextExpression());
        
        // 速度滑块
        this.elements.speedSlider?.addEventListener('input', (e) => {
            this.settings.playSpeed = parseInt(e.target.value);
            this.updateSpeedDisplay();
            this.saveSettings();
            if (this.isPlaying) {
                this.restartPlayback();
            }
        });
        
        // 设置面板
        this.elements.settingsBtn?.addEventListener('click', () => this.openSettings());
        this.elements.closeSettingsBtn?.addEventListener('click', () => this.closeSettings());
        
        // 设置控件
        this.bindSettingsEvents();
        
        // 主题按钮
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const theme = e.target.dataset.theme;
                this.applyTheme(theme);
                this.settings.theme = theme;
                this.saveSettings();
            });
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // 窗口大小变化
        window.addEventListener('resize', () => this.handleResize());
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    }
    
    /**
     * 绑定设置相关事件
     */
    bindSettingsEvents() {
        // 自动播放开关
        this.elements.autoPlayToggle?.addEventListener('change', (e) => {
            this.settings.autoPlay = e.target.checked;
            this.saveSettings();
            if (e.target.checked && !this.isPlaying) {
                this.startPlayback();
            } else if (!e.target.checked && this.isPlaying) {
                this.pausePlayback();
            }
        });
        
        // 随机播放开关
        this.elements.shuffleToggle?.addEventListener('change', (e) => {
            this.settings.shuffle = e.target.checked;
            this.saveSettings();
        });
        
        // 循环播放开关
        this.elements.repeatToggle?.addEventListener('change', (e) => {
            this.settings.repeat = e.target.checked;
            this.saveSettings();
        });
        
        // 亮度滑块
        this.elements.brightnessSlider?.addEventListener('input', (e) => {
            this.settings.brightness = parseInt(e.target.value);
            this.updateBrightness();
            this.updateBrightnessDisplay();
            this.saveSettings();
        });
        
        // 光晕效果开关
        this.elements.glowEffectToggle?.addEventListener('change', (e) => {
            this.settings.glowEffect = e.target.checked;
            this.updateGlowEffect();
            this.saveSettings();
        });
        
        // 背景粒子开关
        this.elements.particlesToggle?.addEventListener('change', (e) => {
            this.settings.particles = e.target.checked;
            this.updateParticles();
            this.saveSettings();
        });
        
        // 过渡时长滑块
        this.elements.transitionSlider?.addEventListener('input', (e) => {
            this.settings.transitionDuration = parseInt(e.target.value);
            this.updateTransitionDisplay();
            animationManager.setTransitionDuration(this.settings.transitionDuration);
            this.saveSettings();
        });
    }
    
    /**
     * 设置当前表情
     * @param {number} index - 表情索引
     */
    setCurrentExpression(index) {
        if (index < 0 || index >= EXPRESSIONS.length) return;
        
        const expression = EXPRESSIONS[index];
        this.currentExpressionIndex = index;
        
        // 更新表情显示
        if (this.elements.expressionEmoji) {
            // 应用过渡动画
            animationManager.applyTransition(
                this.elements.expressionEmoji,
                'fadeOut',
                () => {
                    this.elements.expressionEmoji.textContent = expression.emoji;
                    
                    // 添加表情特定的样式类
                    if (expression.id) {
                        this.elements.expressionEmoji.classList.add(expression.id);
                    }
                    
                    animationManager.applyTransition(this.elements.expressionEmoji, 'fadeIn');
                    
                    // 应用表情动画
                    setTimeout(() => {
                        animationManager.applyAnimation(
                            this.elements.expressionEmoji,
                            expression.animation
                        );
                        
                        // 处理动画序列
                        if (expression.sequence && expression.sequence.length > 0) {
                            this.playAnimationSequence(expression);
                        }
                    }, this.settings.transitionDuration);
                }
            );
        }
        
        // 更新状态显示
        if (this.elements.currentExpressionName) {
            this.elements.currentExpressionName.textContent = expression.name;
        }
        
        // 更新表情按钮状态
        this.updateExpressionButtons();
        
        // 重置进度
        this.currentProgress = 0;
        this.updateProgress();
    }
    
    /**
     * 开始播放
     */
    startPlayback() {
        if (!this.settings.autoPlay) return;
        
        this.isPlaying = true;
        this.updatePlayButton();
        
        const currentExpression = EXPRESSIONS[this.currentExpressionIndex];
        const duration = this.settings.playSpeed;
        
        // 清除现有定时器
        this.clearTimers();
        
        // 设置播放定时器
        this.playTimer = setTimeout(() => {
            this.nextExpression();
        }, duration);
        
        // 设置进度更新定时器
        this.startProgressTimer(duration);
    }
    
    /**
     * 暂停播放
     */
    pausePlayback() {
        this.isPlaying = false;
        this.updatePlayButton();
        this.clearTimers();
        
        // 暂停动画
        if (this.elements.expressionEmoji) {
            animationManager.pauseAnimation(this.elements.expressionEmoji);
        }
    }
    
    /**
     * 切换播放状态
     */
    togglePlayback() {
        if (this.isPlaying) {
            this.pausePlayback();
        } else {
            this.startPlayback();
            // 恢复动画
            if (this.elements.expressionEmoji) {
                animationManager.resumeAnimation(this.elements.expressionEmoji);
            }
        }
    }
    
    /**
     * 重新开始播放
     */
    restartPlayback() {
        this.clearTimers();
        if (this.settings.autoPlay) {
            this.startPlayback();
        }
    }
    
    /**
     * 下一个表情
     */
    nextExpression() {
        let nextIndex;
        
        if (this.settings.shuffle) {
            // 随机模式
            const availableIndices = EXPRESSIONS.map((_, i) => i)
                .filter(i => i !== this.currentExpressionIndex);
            nextIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];
        } else {
            // 顺序模式
            nextIndex = (this.currentExpressionIndex + 1) % EXPRESSIONS.length;
        }
        
        // 检查是否需要循环
        if (!this.settings.repeat && nextIndex === 0 && this.currentExpressionIndex === EXPRESSIONS.length - 1) {
            this.pausePlayback();
            return;
        }
        
        this.setCurrentExpression(nextIndex);
        this.restartPlayback();
    }
    
    /**
     * 上一个表情
     */
    previousExpression() {
        let prevIndex;
        
        if (this.settings.shuffle) {
            // 随机模式
            const availableIndices = EXPRESSIONS.map((_, i) => i)
                .filter(i => i !== this.currentExpressionIndex);
            prevIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];
        } else {
            // 顺序模式
            prevIndex = this.currentExpressionIndex === 0 
                ? EXPRESSIONS.length - 1 
                : this.currentExpressionIndex - 1;
        }
        
        this.setCurrentExpression(prevIndex);
        this.restartPlayback();
    }
    
    /**
     * 开始进度计时器
     * @param {number} duration - 持续时间
     */
    startProgressTimer(duration) {
        const interval = 50; // 50ms更新一次
        const steps = duration / interval;
        let currentStep = 0;
        
        this.progressTimer = setInterval(() => {
            currentStep++;
            this.currentProgress = (currentStep / steps) * 100;
            this.updateProgress();
            
            if (currentStep >= steps) {
                clearInterval(this.progressTimer);
            }
        }, interval);
    }
    
    /**
     * 更新进度显示
     */
    updateProgress() {
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${this.currentProgress}%`;
        }
        
        if (this.elements.timeDisplay) {
            const current = Math.floor((this.currentProgress / 100) * (this.settings.playSpeed / 1000));
            const total = Math.floor(this.settings.playSpeed / 1000);
            this.elements.timeDisplay.textContent = 
                `${this.formatTime(current)} / ${this.formatTime(total)}`;
        }
    }
    
    /**
     * 格式化时间显示
     * @param {number} seconds - 秒数
     * @returns {string} 格式化的时间字符串
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * 清除所有定时器
     */
    clearTimers() {
        if (this.playTimer) {
            clearTimeout(this.playTimer);
            this.playTimer = null;
        }
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
            this.progressTimer = null;
        }
    }
    
    /**
     * 更新播放按钮状态
     */
    updatePlayButton() {
        if (!this.elements.playPauseBtn) return;
        
        const icon = this.elements.playPauseBtn.querySelector('i');
        if (icon) {
            icon.className = this.isPlaying ? 'fas fa-pause' : 'fas fa-play';
        }
        
        if (this.elements.playStatus) {
            const statusIcon = this.elements.playStatus.querySelector('i');
            const statusText = this.elements.playStatus.querySelector('span');
            
            if (statusIcon) {
                statusIcon.className = this.isPlaying ? 'fas fa-play' : 'fas fa-pause';
            }
            if (statusText) {
                statusText.textContent = this.isPlaying ? '播放中' : '已暂停';
            }
        }
    }
    
    /**
     * 更新速度显示
     */
    updateSpeedDisplay() {
        if (this.elements.speedSlider) {
            this.elements.speedSlider.value = this.settings.playSpeed;
        }
        if (this.elements.speedValue) {
            this.elements.speedValue.textContent = `${(this.settings.playSpeed / 1000).toFixed(1)}s`;
        }
    }
    
    /**
     * 更新表情按钮状态
     */
    updateExpressionButtons() {
        const buttons = this.elements.expressionList?.querySelectorAll('.expression-btn');
        if (!buttons) return;
        
        buttons.forEach((button, index) => {
            button.classList.toggle('active', index === this.currentExpressionIndex);
        });
    }
    
    /**
     * 创建背景粒子效果
     */
    createParticles() {
        if (!this.elements['particles-bg'] || !this.settings.particles) return;
        
        const particlesContainer = this.elements['particles-bg'];
        particlesContainer.innerHTML = '';
        
        // 创建粒子
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: var(--primary-neon);
                border-radius: 50%;
                opacity: ${Math.random() * 0.5 + 0.2};
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: particleFloat ${Math.random() * 10 + 10}s linear infinite;
                box-shadow: 0 0 6px var(--primary-neon);
            `;
            
            particlesContainer.appendChild(particle);
        }
    }
    
    /**
     * 打开设置面板
     */
    openSettings() {
        if (this.elements.settingsPanel) {
            this.elements.settingsPanel.classList.add('open');
        }
    }
    
    /**
     * 关闭设置面板
     */
    closeSettings() {
        if (this.elements.settingsPanel) {
            this.elements.settingsPanel.classList.remove('open');
        }
    }
    
    /**
     * 更新设置UI
     */
    updateSettingsUI() {
        // 更新开关状态
        if (this.elements.autoPlayToggle) {
            this.elements.autoPlayToggle.checked = this.settings.autoPlay;
        }
        if (this.elements.shuffleToggle) {
            this.elements.shuffleToggle.checked = this.settings.shuffle;
        }
        if (this.elements.repeatToggle) {
            this.elements.repeatToggle.checked = this.settings.repeat;
        }
        if (this.elements.glowEffectToggle) {
            this.elements.glowEffectToggle.checked = this.settings.glowEffect;
        }
        if (this.elements.particlesToggle) {
            this.elements.particlesToggle.checked = this.settings.particles;
        }
        
        // 更新滑块
        if (this.elements.brightnessSlider) {
            this.elements.brightnessSlider.value = this.settings.brightness;
        }
        if (this.elements.transitionSlider) {
            this.elements.transitionSlider.value = this.settings.transitionDuration;
        }
        
        // 更新显示值
        this.updateBrightnessDisplay();
        this.updateTransitionDisplay();
        
        // 更新主题按钮
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.settings.theme);
        });
    }
    
    /**
     * 更新亮度显示
     */
    updateBrightnessDisplay() {
        if (this.elements.brightnessValue) {
            this.elements.brightnessValue.textContent = `${this.settings.brightness}%`;
        }
    }
    
    /**
     * 更新过渡时长显示
     */
    updateTransitionDisplay() {
        if (this.elements.transitionValue) {
            this.elements.transitionValue.textContent = `${(this.settings.transitionDuration / 1000).toFixed(1)}s`;
        }
    }
    
    /**
     * 更新亮度效果
     */
    updateBrightness() {
        const brightness = this.settings.brightness / 100;
        document.documentElement.style.setProperty('--brightness-factor', brightness);
        
        if (this.elements.megaSphere) {
            this.elements.megaSphere.style.filter = `brightness(${brightness})`;
        }
    }
    
    /**
     * 更新光晕效果
     */
    updateGlowEffect() {
        const glowElements = document.querySelectorAll('.sphere-glow, .sphere-pulse');
        glowElements.forEach(element => {
            element.style.display = this.settings.glowEffect ? 'block' : 'none';
        });
    }
    
    /**
     * 更新背景粒子
     */
    updateParticles() {
        if (this.elements['particles-bg']) {
            this.elements['particles-bg'].style.display = this.settings.particles ? 'block' : 'none';
        }
        
        if (this.settings.particles) {
            this.createParticles();
        }
    }
    
    /**
     * 应用主题
     * @param {string} themeName - 主题名称
     */
    applyTheme(themeName) {
        const theme = THEMES[themeName];
        if (!theme) return;
        
        const root = document.documentElement;
        root.style.setProperty('--primary-neon', theme.colors.primary);
        root.style.setProperty('--secondary-neon', theme.colors.secondary);
        root.style.setProperty('--accent-neon', theme.colors.accent);
        
        // 更新主题按钮状态
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === themeName);
        });
    }
    
    /**
     * 处理键盘事件
     * @param {KeyboardEvent} e - 键盘事件
     */
    handleKeyboard(e) {
        // 如果设置面板打开，ESC关闭
        if (e.key === 'Escape' && this.elements.settingsPanel?.classList.contains('open')) {
            this.closeSettings();
            return;
        }
        
        // 其他快捷键
        switch (e.key) {
            case ' ': // 空格键播放/暂停
                e.preventDefault();
                this.togglePlayback();
                break;
            case 'ArrowLeft': // 左箭头上一个
                e.preventDefault();
                this.previousExpression();
                break;
            case 'ArrowRight': // 右箭头下一个
                e.preventDefault();
                this.nextExpression();
                break;
            case 's': // S键打开设置
                if (e.ctrlKey || e.metaKey) return; // 避免与保存冲突
                this.openSettings();
                break;
        }
    }
    
    /**
     * 处理窗口大小变化
     */
    handleResize() {
        // 重新创建粒子以适应新尺寸
        if (this.settings.particles) {
            this.createParticles();
        }
    }
    
    /**
     * 处理页面可见性变化
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // 页面隐藏时暂停
            if (this.isPlaying) {
                this.pausePlayback();
                this._wasPlayingBeforeHidden = true;
            }
        } else {
            // 页面显示时恢复
            if (this._wasPlayingBeforeHidden && this.settings.autoPlay) {
                this.startPlayback();
                this._wasPlayingBeforeHidden = false;
            }
        }
    }
    
    /**
     * 保存设置到本地存储
     */
    saveSettings() {
        try {
            localStorage.setItem('sphereSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('保存设置失败:', error);
        }
    }
    
    /**
     * 从本地存储加载设置
     */
    loadSettings() {
        try {
            const saved = localStorage.getItem('sphereSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.settings = { ...DEFAULT_SETTINGS, ...settings };
            }
        } catch (error) {
            console.warn('加载设置失败:', error);
            this.settings = { ...DEFAULT_SETTINGS };
        }
    }
    
    /**
     * 重置设置为默认值
     */
    resetSettings() {
        this.settings = { ...DEFAULT_SETTINGS };
        this.saveSettings();
        this.updateSettingsUI();
        this.applyTheme(this.settings.theme);
        this.updateBrightness();
        this.updateGlowEffect();
        this.updateParticles();
    }
    
    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            z-index: 10000;
            text-align: center;
            font-family: 'Orbitron', monospace;
        `;
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            document.body.removeChild(errorDiv);
        }, 5000);
    }
    
    /**
     * 播放动画序列
     * @param {Object} expression - 包含序列的表情对象
     */
    playAnimationSequence(expression) {
        if (!expression.sequence || expression.sequence.length === 0) return;
        
        const emoji = this.elements.expressionEmoji;
        let sequenceIndex = 0;
        const sequenceDuration = expression.duration / expression.sequence.length;
        
        const playNextSequence = () => {
            if (sequenceIndex >= expression.sequence.length) {
                sequenceIndex = 0; // 循环播放序列
            }
            
            const sequenceStep = expression.sequence[sequenceIndex];
            
            // 根据序列步骤应用特殊效果
            switch (sequenceStep) {
                case 'surprised_start':
                    emoji.style.transform = 'scale(1)';
                    break;
                case 'surprised_peak':
                    emoji.style.transform = 'scale(1.5) translateY(-10px)';
                    break;
                case 'surprised_blink':
                    emoji.style.transform = 'scale(1.3) translateY(-5px)';
                    break;
                case 'crying_start':
                    emoji.style.filter = 'drop-shadow(0 0 25px rgba(0, 191, 255, 0.5))';
                    break;
                case 'crying_flow':
                    emoji.style.filter = 'drop-shadow(0 0 35px rgba(0, 191, 255, 0.9))';
                    break;
                case 'crying_sob':
                    emoji.style.transform = 'scale(1.1)';
                    break;
                case 'pumpkin_grin':
                    emoji.style.filter = 'hue-rotate(0deg) brightness(1)';
                    break;
                case 'pumpkin_glow':
                    emoji.style.filter = 'hue-rotate(30deg) brightness(1.3)';
                    break;
                case 'pumpkin_flicker':
                    emoji.style.filter = 'hue-rotate(60deg) brightness(0.7)';
                    break;
                case 'eye_center':
                    emoji.style.transform = 'translateX(0) translateY(0)';
                    break;
                case 'eye_left':
                    emoji.style.transform = 'translateX(-15px) translateY(0)';
                    break;
                case 'eye_right':
                    emoji.style.transform = 'translateX(15px) translateY(0)';
                    break;
                case 'eye_up':
                    emoji.style.transform = 'translateX(0) translateY(-15px)';
                    break;
                case 'eye_down':
                    emoji.style.transform = 'translateX(0) translateY(15px)';
                    break;
                case 'wink_open':
                    emoji.style.transform = 'scaleY(1)';
                    break;
                case 'wink_close':
                    emoji.style.transform = 'scaleY(0.1)';
                    break;
                case 'dizzy_start':
                    emoji.style.transform = 'rotate(0deg) scale(1)';
                    break;
                case 'dizzy_spin':
                    emoji.style.transform = 'rotate(180deg) scale(1.2)';
                    break;
                case 'dizzy_recover':
                    emoji.style.transform = 'rotate(360deg) scale(1)';
                    break;
            }
            
            sequenceIndex++;
            
            // 如果不是自动播放模式，只播放一次序列
            if (this.settings.autoPlay) {
                setTimeout(playNextSequence, sequenceDuration);
            }
        };
        
        // 开始播放序列
        playNextSequence();
    }
    
    /**
     * 销毁实例，清理资源
     */
    destroy() {
        this.clearTimers();
        
        // 移除事件监听器
        document.removeEventListener('keydown', this.handleKeyboard);
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        console.log('拉斯维加斯巨型球已销毁');
    }
}

// 页面加载完成后初始化应用
let vegasSphere;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        vegasSphere = new VegasSphere();
    });
} else {
    vegasSphere = new VegasSphere();
}

// 导出给全局使用
if (typeof window !== 'undefined') {
    window.VegasSphere = VegasSphere;
    window.vegasSphere = vegasSphere;
}