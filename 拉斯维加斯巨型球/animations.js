/**
 * 动画配置模块 - 定义所有动画效果和控制逻辑
 * 包含CSS关键帧定义、动画参数配置和动画控制函数
 */

// CSS动画关键帧定义
const ANIMATIONS = {
    bounce: {
        name: '弹跳',
        keyframes: `
            @keyframes bounce {
                0%, 100% { transform: scale(1) translateY(0); }
                25% { transform: scale(1.1) translateY(-10px); }
                50% { transform: scale(1.2) translateY(-20px); }
                75% { transform: scale(1.1) translateY(-10px); }
            }
        `,
        duration: '1s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    pulse: {
        name: '脉冲',
        keyframes: `
            @keyframes pulse {
                0%, 100% { 
                    opacity: 1; 
                    transform: scale(1);
                    filter: drop-shadow(0 0 20px var(--primary-neon));
                }
                50% { 
                    opacity: 0.7; 
                    transform: scale(1.15);
                    filter: drop-shadow(0 0 40px var(--primary-neon));
                }
            }
        `,
        duration: '1.5s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    rotate: {
        name: '旋转',
        keyframes: `
            @keyframes rotate {
                0% { 
                    transform: rotate(0deg) scale(1);
                    filter: hue-rotate(0deg);
                }
                25% { 
                    transform: rotate(90deg) scale(1.05);
                    filter: hue-rotate(90deg);
                }
                50% { 
                    transform: rotate(180deg) scale(1.1);
                    filter: hue-rotate(180deg);
                }
                75% { 
                    transform: rotate(270deg) scale(1.05);
                    filter: hue-rotate(270deg);
                }
                100% { 
                    transform: rotate(360deg) scale(1);
                    filter: hue-rotate(360deg);
                }
            }
        `,
        duration: '3s',
        timing: 'linear',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    shake: {
        name: '摇摆',
        keyframes: `
            @keyframes shake {
                0%, 100% { transform: translateX(0) rotate(0deg); }
                10% { transform: translateX(-10px) rotate(-2deg); }
                20% { transform: translateX(10px) rotate(2deg); }
                30% { transform: translateX(-8px) rotate(-1deg); }
                40% { transform: translateX(8px) rotate(1deg); }
                50% { transform: translateX(-6px) rotate(-0.5deg); }
                60% { transform: translateX(6px) rotate(0.5deg); }
                70% { transform: translateX(-4px) rotate(-0.25deg); }
                80% { transform: translateX(4px) rotate(0.25deg); }
                90% { transform: translateX(-2px) rotate(-0.125deg); }
            }
        `,
        duration: '0.8s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    flicker: {
        name: '闪烁',
        keyframes: `
            @keyframes flicker {
                0%, 100% { 
                    opacity: 1; 
                    filter: brightness(1) drop-shadow(0 0 20px var(--accent-neon));
                }
                10% { 
                    opacity: 0.8; 
                    filter: brightness(1.2) drop-shadow(0 0 30px var(--accent-neon));
                }
                20% { 
                    opacity: 0.9; 
                    filter: brightness(0.8) drop-shadow(0 0 15px var(--accent-neon));
                }
                30% { 
                    opacity: 0.7; 
                    filter: brightness(1.5) drop-shadow(0 0 40px var(--accent-neon));
                }
                40% { 
                    opacity: 0.95; 
                    filter: brightness(0.9) drop-shadow(0 0 25px var(--accent-neon));
                }
                50% { 
                    opacity: 0.6; 
                    filter: brightness(1.8) drop-shadow(0 0 50px var(--accent-neon));
                }
                60% { 
                    opacity: 0.85; 
                    filter: brightness(1.1) drop-shadow(0 0 35px var(--accent-neon));
                }
                70% { 
                    opacity: 0.75; 
                    filter: brightness(1.3) drop-shadow(0 0 45px var(--accent-neon));
                }
                80% { 
                    opacity: 0.9; 
                    filter: brightness(0.95) drop-shadow(0 0 20px var(--accent-neon));
                }
                90% { 
                    opacity: 0.8; 
                    filter: brightness(1.4) drop-shadow(0 0 35px var(--accent-neon));
                }
            }
        `,
        duration: '0.6s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    glow: {
        name: '发光',
        keyframes: `
            @keyframes glow {
                0%, 100% { 
                    filter: drop-shadow(0 0 20px var(--primary-neon)) brightness(1);
                    transform: scale(1);
                }
                50% { 
                    filter: drop-shadow(0 0 60px var(--primary-neon)) brightness(1.3);
                    transform: scale(1.08);
                }
            }
        `,
        duration: '2s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    float: {
        name: '漂浮',
        keyframes: `
            @keyframes float {
                0%, 100% { 
                    transform: translateY(0px) rotate(0deg);
                }
                25% { 
                    transform: translateY(-15px) rotate(1deg);
                }
                50% { 
                    transform: translateY(-25px) rotate(0deg);
                }
                75% { 
                    transform: translateY(-15px) rotate(-1deg);
                }
            }
        `,
        duration: '4s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    // 新增拉斯维加斯巨型球风格动画
    bigEyes: {
        name: '大眼睛',
        keyframes: `
            @keyframes bigEyes {
                0% { transform: scale(1); }
                30% { transform: scale(1.5) translateY(-10px); }
                60% { transform: scale(1.3) translateY(-5px); }
                100% { transform: scale(1); }
            }
        `,
        duration: '2s',
        timing: 'ease-out',
        iteration: '1',
        fillMode: 'both'
    },
    
    tears: {
        name: '眼泪',
        keyframes: `
            @keyframes tears {
                0% { transform: scale(1); opacity: 1; }
                25% { transform: scale(1.1); }
                50% { transform: scale(1.05); opacity: 0.8; }
                75% { transform: scale(1.1); }
                100% { transform: scale(1); opacity: 1; }
            }
        `,
        duration: '3s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    spooky: {
        name: '诡异',
        keyframes: `
            @keyframes spooky {
                0%, 100% { filter: hue-rotate(0deg) brightness(1); }
                25% { filter: hue-rotate(30deg) brightness(1.2); }
                50% { filter: hue-rotate(60deg) brightness(0.8); }
                75% { filter: hue-rotate(30deg) brightness(1.2); }
            }
        `,
        duration: '2.5s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    eyeRoll: {
        name: '翻白眼',
        keyframes: `
            @keyframes eyeRoll {
                0% { transform: translateX(0) translateY(0); }
                20% { transform: translateX(-15px) translateY(0); }
                40% { transform: translateX(15px) translateY(0); }
                60% { transform: translateX(0) translateY(-15px); }
                80% { transform: translateX(0) translateY(15px); }
                100% { transform: translateX(0) translateY(0); }
            }
        `,
        duration: '3s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    },
    
    blink: {
        name: '眨眼',
        keyframes: `
            @keyframes blink {
                0%, 100% { transform: scaleY(1); }
                50% { transform: scaleY(0.1); }
            }
        `,
        duration: '1.5s',
        timing: 'ease-in-out',
        iteration: '1',
        fillMode: 'both'
    },
    
    spiral: {
        name: '螺旋',
        keyframes: `
            @keyframes spiral {
                0% { transform: rotate(0deg) scale(1); }
                50% { transform: rotate(180deg) scale(1.2); }
                100% { transform: rotate(360deg) scale(1); }
            }
        `,
        duration: '2.5s',
        timing: 'ease-in-out',
        iteration: 'infinite',
        fillMode: 'both'
    }
};

// 过渡动画配置
const TRANSITIONS = {
    fadeIn: {
        name: '淡入',
        keyframes: `
            @keyframes fadeIn {
                from { 
                    opacity: 0; 
                    transform: scale(0.8);
                }
                to { 
                    opacity: 1; 
                    transform: scale(1);
                }
            }
        `,
        duration: '0.5s',
        timing: 'ease-out',
        fillMode: 'both'
    },
    
    fadeOut: {
        name: '淡出',
        keyframes: `
            @keyframes fadeOut {
                from { 
                    opacity: 1; 
                    transform: scale(1);
                }
                to { 
                    opacity: 0; 
                    transform: scale(0.8);
                }
            }
        `,
        duration: '0.3s',
        timing: 'ease-in',
        fillMode: 'both'
    },
    
    slideIn: {
        name: '滑入',
        keyframes: `
            @keyframes slideIn {
                from { 
                    opacity: 0; 
                    transform: translateY(50px) scale(0.9);
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0) scale(1);
                }
            }
        `,
        duration: '0.6s',
        timing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        fillMode: 'both'
    },
    
    zoomIn: {
        name: '缩放进入',
        keyframes: `
            @keyframes zoomIn {
                from { 
                    opacity: 0; 
                    transform: scale(0.3) rotate(180deg);
                }
                50% {
                    opacity: 0.8;
                    transform: scale(1.1) rotate(90deg);
                }
                to { 
                    opacity: 1; 
                    transform: scale(1) rotate(0deg);
                }
            }
        `,
        duration: '0.8s',
        timing: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        fillMode: 'both'
    }
};

/**
 * 动画管理器类
 */
class AnimationManager {
    constructor() {
        this.styleSheet = null;
        this.currentAnimation = null;
        this.transitionDuration = 500;
        this.init();
    }
    
    /**
     * 初始化动画管理器
     */
    init() {
        this.createStyleSheet();
        this.injectAnimations();
    }
    
    /**
     * 创建样式表
     */
    createStyleSheet() {
        this.styleSheet = document.createElement('style');
        this.styleSheet.id = 'animation-styles';
        document.head.appendChild(this.styleSheet);
    }
    
    /**
     * 注入所有动画CSS
     */
    injectAnimations() {
        let css = '';
        
        // 注入主要动画
        Object.values(ANIMATIONS).forEach(animation => {
            css += animation.keyframes;
        });
        
        // 注入过渡动画
        Object.values(TRANSITIONS).forEach(transition => {
            css += transition.keyframes;
        });
        
        this.styleSheet.textContent = css;
    }
    
    /**
     * 应用动画到元素
     * @param {HTMLElement} element - 目标元素
     * @param {string} animationType - 动画类型
     * @param {Object} options - 动画选项
     */
    applyAnimation(element, animationType, options = {}) {
        if (!element || !ANIMATIONS[animationType]) {
            console.warn(`Animation ${animationType} not found`);
            return;
        }
        
        const animation = ANIMATIONS[animationType];
        const {
            duration = animation.duration,
            timing = animation.timing,
            iteration = animation.iteration,
            fillMode = animation.fillMode,
            delay = '0s'
        } = options;
        
        // 清除之前的动画
        this.clearAnimation(element);
        
        // 应用新动画
        element.style.animation = `${animationType} ${duration} ${timing} ${delay} ${iteration} ${fillMode}`;
        this.currentAnimation = animationType;
    }
    
    /**
     * 应用过渡动画
     * @param {HTMLElement} element - 目标元素
     * @param {string} transitionType - 过渡类型
     * @param {Function} callback - 完成回调
     */
    applyTransition(element, transitionType, callback = null) {
        if (!element || !TRANSITIONS[transitionType]) {
            console.warn(`Transition ${transitionType} not found`);
            return;
        }
        
        const transition = TRANSITIONS[transitionType];
        
        // 应用过渡动画
        element.style.animation = `${transitionType} ${transition.duration} ${transition.timing} ${transition.fillMode}`;
        
        // 监听动画结束
        const handleAnimationEnd = () => {
            element.removeEventListener('animationend', handleAnimationEnd);
            if (callback) callback();
        };
        
        element.addEventListener('animationend', handleAnimationEnd);
    }
    
    /**
     * 清除元素动画
     * @param {HTMLElement} element - 目标元素
     */
    clearAnimation(element) {
        if (element) {
            element.style.animation = '';
        }
    }
    
    /**
     * 暂停动画
     * @param {HTMLElement} element - 目标元素
     */
    pauseAnimation(element) {
        if (element) {
            element.style.animationPlayState = 'paused';
        }
    }
    
    /**
     * 恢复动画
     * @param {HTMLElement} element - 目标元素
     */
    resumeAnimation(element) {
        if (element) {
            element.style.animationPlayState = 'running';
        }
    }
    
    /**
     * 设置动画速度
     * @param {HTMLElement} element - 目标元素
     * @param {number} speed - 速度倍数 (0.5 = 慢一半, 2 = 快一倍)
     */
    setAnimationSpeed(element, speed) {
        if (element && this.currentAnimation) {
            const animation = ANIMATIONS[this.currentAnimation];
            const newDuration = parseFloat(animation.duration) / speed + 's';
            
            element.style.animation = element.style.animation.replace(
                /[\d.]+s/, 
                newDuration
            );
        }
    }
    
    /**
     * 获取所有可用动画
     * @returns {Array} 动画列表
     */
    getAvailableAnimations() {
        return Object.keys(ANIMATIONS).map(key => ({
            id: key,
            name: ANIMATIONS[key].name
        }));
    }
    
    /**
     * 设置过渡时长
     * @param {number} duration - 时长（毫秒）
     */
    setTransitionDuration(duration) {
        this.transitionDuration = duration;
    }
}

// 创建全局动画管理器实例
const animationManager = new AnimationManager();

// 导出给全局使用
if (typeof window !== 'undefined') {
    window.ANIMATIONS = ANIMATIONS;
    window.TRANSITIONS = TRANSITIONS;
    window.AnimationManager = AnimationManager;
    window.animationManager = animationManager;
}