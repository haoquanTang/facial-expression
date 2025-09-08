/**
 * 应用常量配置
 * 包含情绪配置、主题色彩、预设标签等常量定义
 */

import { EmotionConfig, ThemeColors, Tag } from '../types';

// 情绪配置映射
export const EMOTION_CONFIGS: Record<string, EmotionConfig> = {
  happy: {
    type: 'happy',
    label: '开心',
    color: '#FFE4B5',
    icon: '😊',
    description: '感到快乐、愉悦、满足'
  },
  sad: {
    type: 'sad',
    label: '难过',
    color: '#B8E0F5',
    icon: '😢',
    description: '感到悲伤、失落、沮丧'
  },
  anxious: {
    type: 'anxious',
    label: '焦虑',
    color: '#FFB6C1',
    icon: '😰',
    description: '感到紧张、担心、不安'
  },
  calm: {
    type: 'calm',
    label: '平静',
    color: '#E0F2E7',
    icon: '😌',
    description: '感到宁静、放松、安详'
  },
  angry: {
    type: 'angry',
    label: '愤怒',
    color: '#FFB4B4',
    icon: '😠',
    description: '感到生气、愤怒、不满'
  },
  excited: {
    type: 'excited',
    label: '兴奋',
    color: '#FFCCCB',
    icon: '🤩',
    description: '感到兴奋、激动、充满活力'
  },
  tired: {
    type: 'tired',
    label: '疲惫',
    color: '#D3D3D3',
    icon: '😴',
    description: '感到疲劳、困倦、精力不足'
  },
  neutral: {
    type: 'neutral',
    label: '中性',
    color: '#F0F0F0',
    icon: '😐',
    description: '情绪平稳、没有特别感受'
  }
};

// 主题色彩配置
export const THEME_COLORS: ThemeColors = {
  primary: '#FEFCF8',      // 奶白色
  secondary: '#E8D5F2',    // 雾紫色
  accent: '#B8E0F5',       // 淡蓝色
  soft_pink: '#F5E6E8',    // 柔和粉色
  mint_green: '#E0F2E7',   // 薄荷绿
  warm_gray: '#F0F0F0'     // 暖灰色
};

// 预设标签
export const PRESET_TAGS: Omit<Tag, 'id' | 'created_at'>[] = [
  { name: '工作', color: '#E8D5F2' },
  { name: '家庭', color: '#B8E0F5' },
  { name: '健康', color: '#E0F2E7' },
  { name: '学习', color: '#F5E6E8' },
  { name: '社交', color: '#FFF2E0' },
  { name: '运动', color: '#E0F7FA' },
  { name: '娱乐', color: '#FCE4EC' },
  { name: '旅行', color: '#F3E5F5' }
];

// 激励语句
export const MOTIVATIONAL_QUOTES = [
  '每一天都是新的开始 ✨',
  '记录情绪，拥抱真实的自己 💝',
  '小小的进步也值得庆祝 🎉',
  '情绪如天气，总会变化 🌈',
  '你比想象中更坚强 💪',
  '今天的你已经很棒了 ⭐',
  '慢慢来，一切都会好起来 🌸',
  '倾听内心的声音 🎵',
  '每个情绪都有它的意义 🌺',
  '温柔对待自己 🤗'
];

// 时间段选项
export const TIME_PERIODS = [
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' }
] as const;

// 情绪强度标签
export const INTENSITY_LABELS = {
  1: '很轻微',
  2: '轻微',
  3: '中等',
  4: '强烈',
  5: '非常强烈'
} as const;

// 导出格式选项
export const EXPORT_FORMATS = [
  { value: 'pdf', label: 'PDF 文档', icon: '📄' },
  { value: 'json', label: 'JSON 数据', icon: '📊' },
  { value: 'csv', label: 'CSV 表格', icon: '📈' }
] as const;

// 提醒时间选项
export const REMINDER_TIMES = [
  { value: '09:00', label: '上午 9:00' },
  { value: '12:00', label: '中午 12:00' },
  { value: '18:00', label: '下午 6:00' },
  { value: '21:00', label: '晚上 9:00' },
  { value: '22:00', label: '晚上 10:00' }
] as const;

// 动画配置
export const ANIMATION_CONFIG = {
  // 页面切换动画
  pageTransition: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  // 卡片悬停动画
  cardHover: {
    whileHover: { y: -4, scale: 1.02 },
    transition: { duration: 0.2, ease: 'easeOut' }
  },
  // 按钮点击动画
  buttonTap: {
    whileTap: { scale: 0.95 },
    transition: { duration: 0.1 }
  },
  // 情绪按钮波纹动画
  emotionRipple: {
    initial: { scale: 0, opacity: 0.6 },
    animate: { scale: 2, opacity: 0 },
    transition: { duration: 0.6, ease: 'easeOut' }
  }
};

// 本地存储键名
export const STORAGE_KEYS = {
  USER_SETTINGS: 'mood_diary_user_settings',
  DRAFT_RECORD: 'mood_diary_draft_record',
  LAST_SYNC: 'mood_diary_last_sync',
  ONBOARDING_COMPLETED: 'mood_diary_onboarding_completed'
} as const;

// API 端点
export const API_ENDPOINTS = {
  RECORDS: '/api/records',
  ANALYTICS: '/api/analytics',
  TAGS: '/api/tags',
  MEDIA: '/api/media',
  USER_PROFILE: '/api/user/profile',
  EXPORT: '/api/export'
} as const;

// 文件上传限制
export const FILE_UPLOAD_LIMITS = {
  MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
  MAX_AUDIO_SIZE: 10 * 1024 * 1024, // 10MB
  MAX_IMAGES_PER_RECORD: 3,
  MAX_AUDIO_DURATION: 300, // 5分钟
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/webp'],
  ALLOWED_AUDIO_TYPES: ['audio/mp3', 'audio/wav', 'audio/m4a']
} as const;

// 默认应用设置
export const DEFAULT_APP_SETTINGS = {
  theme: 'light' as const,
  language: 'zh' as const,
  reminder: {
    enabled: true,
    time: '21:00',
    frequency: 'daily' as const
  },
  privacy: {
    analytics_enabled: true,
    crash_reports_enabled: true
  }
};