/**
 * 应用状态管理
 * 使用 Zustand 管理全局状态
 */

import { create } from 'zustand';
import { EmotionRecord, UserProfile, Tag, AppSettings, ComponentStatus } from '../types';
import { DEFAULT_APP_SETTINGS, MOCK_RECORDS, PRESET_TAGS } from './constants';
import { MOCK_TODAY_OVERVIEW } from './mockData';

// 应用主状态接口
interface AppState {
  // 用户相关
  user: UserProfile | null;
  isAuthenticated: boolean;
  
  // 记录相关
  records: EmotionRecord[];
  currentRecord: Partial<EmotionRecord> | null;
  
  // 标签相关
  tags: Tag[];
  
  // 应用设置
  settings: AppSettings;
  
  // UI状态
  loading: ComponentStatus;
  error: string | null;
  
  // 今日概览
  todayOverview: {
    todayCount: number;
    streakDays: number;
    totalRecords: number;
    lastRecord: EmotionRecord | null;
  };
}

// 应用操作接口
interface AppActions {
  // 用户操作
  setUser: (user: UserProfile | null) => void;
  setAuthenticated: (authenticated: boolean) => void;
  
  // 记录操作
  setRecords: (records: EmotionRecord[]) => void;
  addRecord: (record: EmotionRecord) => void;
  updateRecord: (id: string, updates: Partial<EmotionRecord>) => void;
  deleteRecord: (id: string) => void;
  setCurrentRecord: (record: Partial<EmotionRecord> | null) => void;
  
  // 标签操作
  setTags: (tags: Tag[]) => void;
  addTag: (tag: Tag) => void;
  updateTag: (id: string, updates: Partial<Tag>) => void;
  deleteTag: (id: string) => void;
  
  // 设置操作
  updateSettings: (updates: Partial<AppSettings>) => void;
  
  // UI状态操作
  setLoading: (status: ComponentStatus) => void;
  setError: (error: string | null) => void;
  
  // 数据刷新
  refreshTodayOverview: () => void;
  
  // 初始化
  initializeApp: () => void;
}

/**
 * 计算今日概览数据
 * @param records 情绪记录数组
 * @returns 今日概览对象
 */
function calculateTodayOverview(records: EmotionRecord[]) {
  const today = new Date().toISOString().split('T')[0];
  const todayRecords = records.filter(record => {
    const recordDate = new Date(record.recorded_at).toISOString().split('T')[0];
    return recordDate === today;
  });
  
  // 计算连续记录天数
  const sortedDates = [...new Set(records.map(record => 
    new Date(record.recorded_at).toISOString().split('T')[0]
  ))].sort().reverse();
  
  let streakDays = 0;
  const currentDate = new Date();
  
  for (let i = 0; i < sortedDates.length; i++) {
    const checkDate = new Date(currentDate);
    checkDate.setDate(checkDate.getDate() - i);
    const checkDateStr = checkDate.toISOString().split('T')[0];
    
    if (sortedDates.includes(checkDateStr)) {
      streakDays++;
    } else {
      break;
    }
  }
  
  return {
    todayCount: todayRecords.length,
    streakDays,
    totalRecords: records.length,
    lastRecord: records[0] || null
  };
}

// 创建应用状态store
export const useAppStore = create<AppState & AppActions>((set, get) => ({
  // 初始状态
  user: null,
  isAuthenticated: false,
  records: [],
  currentRecord: null,
  tags: [],
  settings: DEFAULT_APP_SETTINGS,
  loading: 'idle',
  error: null,
  todayOverview: {
    todayCount: 0,
    streakDays: 0,
    totalRecords: 0,
    lastRecord: null
  },
  
  // 用户操作
  setUser: (user) => set({ user }),
  setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  
  // 记录操作
  setRecords: (records) => {
    set({ records });
    // 自动更新今日概览
    const todayOverview = calculateTodayOverview(records);
    set({ todayOverview });
  },
  
  addRecord: (record) => {
    const { records } = get();
    const newRecords = [record, ...records].sort(
      (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime()
    );
    set({ records: newRecords });
    
    // 更新今日概览
    const todayOverview = calculateTodayOverview(newRecords);
    set({ todayOverview });
  },
  
  updateRecord: (id, updates) => {
    const { records } = get();
    const newRecords = records.map(record => 
      record.id === id ? { ...record, ...updates, updated_at: new Date().toISOString() } : record
    );
    set({ records: newRecords });
    
    // 更新今日概览
    const todayOverview = calculateTodayOverview(newRecords);
    set({ todayOverview });
  },
  
  deleteRecord: (id) => {
    const { records } = get();
    const newRecords = records.filter(record => record.id !== id);
    set({ records: newRecords });
    
    // 更新今日概览
    const todayOverview = calculateTodayOverview(newRecords);
    set({ todayOverview });
  },
  
  setCurrentRecord: (currentRecord) => set({ currentRecord }),
  
  // 标签操作
  setTags: (tags) => set({ tags }),
  
  addTag: (tag) => {
    const { tags } = get();
    set({ tags: [...tags, tag] });
  },
  
  updateTag: (id, updates) => {
    const { tags } = get();
    const newTags = tags.map(tag => 
      tag.id === id ? { ...tag, ...updates } : tag
    );
    set({ tags: newTags });
  },
  
  deleteTag: (id) => {
    const { tags } = get();
    const newTags = tags.filter(tag => tag.id !== id);
    set({ tags: newTags });
  },
  
  // 设置操作
  updateSettings: (updates) => {
    const { settings } = get();
    const newSettings = { ...settings, ...updates };
    set({ settings: newSettings });
    
    // 保存到本地存储
    try {
      localStorage.setItem('mood_diary_settings', JSON.stringify(newSettings));
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error);
    }
  },
  
  // UI状态操作
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  // 数据刷新
  refreshTodayOverview: () => {
    const { records } = get();
    const todayOverview = calculateTodayOverview(records);
    set({ todayOverview });
  },
  
  // 初始化应用
  initializeApp: () => {
    try {
      // 从本地存储加载设置
      const savedSettings = localStorage.getItem('mood_diary_settings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        set({ settings: { ...DEFAULT_APP_SETTINGS, ...settings } });
      }
      
      // 加载模拟数据（实际项目中这里会从API加载）
      const records = MOCK_RECORDS;
      const tags = PRESET_TAGS.map((tag, index) => ({
        ...tag,
        id: `tag-${index}`,
        created_at: new Date().toISOString()
      }));
      
      set({ 
        records,
        tags,
        todayOverview: MOCK_TODAY_OVERVIEW,
        loading: 'success'
      });
      
    } catch (error) {
      console.error('Failed to initialize app:', error);
      set({ 
        error: '应用初始化失败',
        loading: 'error'
      });
    }
  }
}));

// 选择器函数，用于优化性能
export const useRecords = () => useAppStore(state => state.records);
export const useTags = () => useAppStore(state => state.tags);
export const useSettings = () => useAppStore(state => state.settings);
export const useTodayOverview = () => useAppStore(state => state.todayOverview);
export const useLoading = () => useAppStore(state => state.loading);
export const useError = () => useAppStore(state => state.error);
export const useCurrentRecord = () => useAppStore(state => state.currentRecord);

// 计算选择器
export const useEmotionStats = () => {
  return useAppStore(state => {
    const records = state.records;
    const emotionCounts: Record<string, { count: number; totalIntensity: number }> = {};
    
    records.forEach(record => {
      const emotion = record.emotion_type;
      if (!emotionCounts[emotion]) {
        emotionCounts[emotion] = { count: 0, totalIntensity: 0 };
      }
      emotionCounts[emotion].count++;
      emotionCounts[emotion].totalIntensity += record.emotion_intensity;
    });
    
    const totalRecords = records.length;
    
    return Object.entries(emotionCounts).map(([emotion, data]) => ({
      emotion_type: emotion as any,
      count: data.count,
      percentage: totalRecords > 0 ? Math.round((data.count / totalRecords) * 100) : 0,
      avg_intensity: data.count > 0 ? Math.round((data.totalIntensity / data.count) * 10) / 10 : 0
    }));
  });
};

export const useRecentRecords = (limit: number = 10) => {
  return useAppStore(state => 
    state.records.slice(0, limit)
  );
};