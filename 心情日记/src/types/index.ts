/**
 * 情绪记录疗愈 App 核心类型定义
 * 定义应用中使用的所有数据结构和类型
 */

// 情绪类型枚举
export type EmotionType = 
  | 'happy'     // 开心
  | 'sad'       // 难过
  | 'anxious'   // 焦虑
  | 'calm'      // 平静
  | 'angry'     // 愤怒
  | 'excited'   // 兴奋
  | 'tired'     // 疲惫
  | 'neutral';  // 中性

// 情绪强度 (1-5级)
export type EmotionIntensity = 1 | 2 | 3 | 4 | 5;

// 媒体文件类型
export type MediaFileType = 'image' | 'audio';

// 用户配置信息
export interface UserProfile {
  id: string;
  username?: string;
  avatar_url?: string;
  timezone: string;
  notification_enabled: boolean;
  daily_reminder_time: string;
  created_at: string;
  updated_at: string;
}

// 情绪记录
export interface EmotionRecord {
  id: string;
  user_id: string;
  emotion_type: EmotionType;
  emotion_intensity: EmotionIntensity;
  diary_content?: string;
  recorded_at: string;
  created_at: string;
  updated_at: string;
  tags?: Tag[];
  media_files?: MediaFile[];
}

// 媒体文件
export interface MediaFile {
  id: string;
  record_id: string;
  file_type: MediaFileType;
  file_url: string;
  file_name: string;
  file_size?: number;
  created_at: string;
}

// 标签
export interface Tag {
  id: string;
  user_id?: string;
  name: string;
  color: string;
  created_at: string;
}

// 记录标签关联
export interface RecordTag {
  record_id: string;
  tag_id: string;
  created_at: string;
}

// 情绪统计数据
export interface EmotionStats {
  emotion_type: EmotionType;
  count: number;
  percentage: number;
  avg_intensity: number;
}

// 趋势数据点
export interface TrendDataPoint {
  date: string;
  emotion_type: EmotionType;
  intensity: EmotionIntensity;
  count: number;
}

// 词云数据
export interface WordCloudData {
  text: string;
  value: number;
  color?: string;
}

// API 响应基础结构
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 分页参数
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

// 记录查询参数
export interface RecordQueryParams extends PaginationParams {
  start_date?: string;
  end_date?: string;
  emotion_type?: EmotionType;
  tags?: string[];
  search?: string;
}

// 统计查询参数
export interface AnalyticsParams {
  period: '7d' | '30d' | '90d';
  chart_type?: 'line' | 'pie' | 'wordcloud';
}

// 情绪配置
export interface EmotionConfig {
  type: EmotionType;
  label: string;
  color: string;
  icon: string;
  description: string;
}

// 应用主题色彩
export interface ThemeColors {
  primary: string;      // 奶白色 #FEFCF8
  secondary: string;    // 雾紫色 #E8D5F2
  accent: string;       // 淡蓝色 #B8E0F5
  soft_pink: string;    // 柔和粉色 #F5E6E8
  mint_green: string;   // 薄荷绿 #E0F2E7
  warm_gray: string;    // 暖灰色 #F0F0F0
}

// 组件状态
export type ComponentStatus = 'idle' | 'loading' | 'success' | 'error';

// 表单验证错误
export interface FormErrors {
  [key: string]: string | undefined;
}

// 导出格式
export type ExportFormat = 'pdf' | 'json' | 'csv';

// 提醒设置
export interface ReminderSettings {
  enabled: boolean;
  time: string;
  frequency: 'daily' | 'weekly' | 'custom';
  days?: number[]; // 0-6 表示周日到周六
}

// 应用设置
export interface AppSettings {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh' | 'en';
  reminder: ReminderSettings;
  privacy: {
    analytics_enabled: boolean;
    crash_reports