/**
 * 表情数据库 - 定义所有可用的表情和其属性
 * 每个表情包含：id、名称、emoji、持续时间、动画类型
 */

// 表情库定义
const EXPRESSIONS = [
    {
        id: 'happy',
        name: '开心',
        emoji: '😊',
        duration: 2000,
        animation: 'bounce'
    },
    {
        id: 'love',
        name: '爱心',
        emoji: '😍',
        duration: 2500,
        animation: 'pulse'
    },
    {
        id: 'cool',
        name: '酷炫',
        emoji: '😎',
        duration: 3000,
        animation: 'rotate'
    },
    {
        id: 'party',
        name: '派对',
        emoji: '🥳',
        duration: 2000,
        animation: 'shake'
    },
    {
        id: 'fire',
        name: '火焰',
        emoji: '🔥',
        duration: 2500,
        animation: 'flicker'
    },
    {
        id: 'star',
        name: '星星',
        emoji: '⭐',
        duration: 2000,
        animation: 'glow'
    },
    {
        id: 'rocket',
        name: '火箭',
        emoji: '🚀',
        duration: 3000,
        animation: 'bounce'
    },
    {
        id: 'diamond',
        name: '钻石',
        emoji: '💎',
        duration: 2500,
        animation: 'rotate'
    },
    {
        id: 'lightning',
        name: '闪电',
        emoji: '⚡',
        duration: 1500,
        animation: 'flicker'
    },
    {
        id: 'rainbow',
        name: '彩虹',
        emoji: '🌈',
        duration: 3000,
        animation: 'pulse'
    },
    {
        id: 'crown',
        name: '皇冠',
        emoji: '👑',
        duration: 2500,
        animation: 'glow'
    },
    {
        id: 'sparkles',
        name: '闪光',
        emoji: '✨',
        duration: 2000,
        animation: 'shake'
    },
    {
        id: 'alien',
        name: '外星人',
        emoji: '👽',
        duration: 2500,
        animation: 'bounce'
    },
    {
        id: 'robot',
        name: '机器人',
        emoji: '🤖',
        duration: 3000,
        animation: 'rotate'
    },
    {
        id: 'unicorn',
        name: '独角兽',
        emoji: '🦄',
        duration: 2500,
        animation: 'pulse'
    },
    // 新增拉斯维加斯巨型球风格表情
    {
        id: 'surprised',
        name: '惊讶',
        emoji: '😲',
        duration: 2000,
        animation: 'bigEyes',
        sequence: ['surprised_start', 'surprised_peak', 'surprised_blink']
    },
    {
        id: 'crying',
        name: '哭泣',
        emoji: '😢',
        duration: 3000,
        animation: 'tears',
        sequence: ['crying_start', 'crying_flow', 'crying_sob']
    },
    {
        id: 'pumpkin',
        name: '南瓜脸',
        emoji: '🎃',
        duration: 2500,
        animation: 'spooky',
        sequence: ['pumpkin_grin', 'pumpkin_glow', 'pumpkin_flicker']
    },
    {
        id: 'eyeball',
        name: '眼球',
        emoji: '👁️',
        duration: 3000,
        animation: 'eyeRoll',
        sequence: ['eye_center', 'eye_left', 'eye_right', 'eye_up', 'eye_down']
    },
    {
        id: 'winking',
        name: '眨眼',
        emoji: '😉',
        duration: 1500,
        animation: 'blink',
        sequence: ['wink_open', 'wink_close', 'wink_open']
    },
    {
        id: 'dizzy',
        name: '眩晕',
        emoji: '😵‍💫',
        duration: 2500,
        animation: 'spiral',
        sequence: ['dizzy_start', 'dizzy_spin', 'dizzy_recover']
    }
];

// 默认设置配置
const DEFAULT_SETTINGS = {
    playSpeed: 2000,           // 播放速度（毫秒）
    autoPlay: true,            // 是否自动播放
    brightness: 80,            // LED亮度 (0-100)
    glowEffect: true,          // 是否启用光晕效果
    theme: 'neon',            // 主题风格
    transitionDuration: 500,   // 过渡动画时长（毫秒）
    shuffle: false,           // 是否随机播放
    repeat: true,             // 是否循环播放
    particles: true           // 是否显示背景粒子
};

// 主题配置
const THEMES = {
    neon: {
        name: '霓虹',
        colors: {
            primary: '#00FFFF',
            secondary: '#8A2BE2',
            accent: '#FF1493'
        }
    },
    cyber: {
        name: '赛博',
        colors: {
            primary: '#00FF41',
            secondary: '#0080FF',
            accent: '#FF4500'
        }
    },
    retro: {
        name: '复古',
        colors: {
            primary: '#FFD700',
            secondary: '#FF6B6B',
            accent: '#4ECDC4'
        }
    }
};

/**
 * 根据ID获取表情数据
 * @param {string} id - 表情ID
 * @returns {Object|null} 表情对象或null
 */
function getExpressionById(id) {
    return EXPRESSIONS.find(expr => expr.id === id) || null;
}

/**
 * 获取所有表情列表
 * @returns {Array} 表情数组
 */
function getAllExpressions() {
    return [...EXPRESSIONS];
}

/**
 * 获取随机表情
 * @param {string} excludeId - 要排除的表情ID
 * @returns {Object} 随机表情对象
 */
function getRandomExpression(excludeId = null) {
    const availableExpressions = excludeId 
        ? EXPRESSIONS.filter(expr => expr.id !== excludeId)
        : EXPRESSIONS;
    
    const randomIndex = Math.floor(Math.random() * availableExpressions.length);
    return availableExpressions[randomIndex];
}

/**
 * 获取下一个表情
 * @param {string} currentId - 当前表情ID
 * @param {boolean} shuffle - 是否随机模式
 * @returns {Object} 下一个表情对象
 */
function getNextExpression(currentId, shuffle = false) {
    if (shuffle) {
        return getRandomExpression(currentId);
    }
    
    const currentIndex = EXPRESSIONS.findIndex(expr => expr.id === currentId);
    const nextIndex = (currentIndex + 1) % EXPRESSIONS.length;
    return EXPRESSIONS[nextIndex];
}

/**
 * 获取上一个表情
 * @param {string} currentId - 当前表情ID
 * @param {boolean} shuffle - 是否随机模式
 * @returns {Object} 上一个表情对象
 */
function getPreviousExpression(currentId, shuffle = false) {
    if (shuffle) {
        return getRandomExpression(currentId);
    }
    
    const currentIndex = EXPRESSIONS.findIndex(expr => expr.id === currentId);
    const prevIndex = currentIndex === 0 ? EXPRESSIONS.length - 1 : currentIndex - 1;
    return EXPRESSIONS[prevIndex];
}

/**
 * 验证表情数据完整性
 * @returns {boolean} 是否所有表情数据都有效
 */
function validateExpressions() {
    return EXPRESSIONS.every(expr => {
        return expr.id && 
               expr.name && 
               expr.emoji && 
               typeof expr.duration === 'number' && 
               expr.animation;
    });
}

// 导出给全局使用
if (typeof window !== 'undefined') {
    window.EXPRESSIONS = EXPRESSIONS;
    window.DEFAULT_SETTINGS = DEFAULT_SETTINGS;
    window.THEMES = THEMES;
    window.getExpressionById = getExpressionById;
    window.getAllExpressions = getAllExpressions;
    window.getRandomExpression = getRandomExpression;
    window.getNextExpression = getNextExpression;
    window.getPreviousExpression = getPreviousExpression;
    window.validateExpressions = validateExpressions;
}