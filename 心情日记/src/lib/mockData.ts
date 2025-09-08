/**
 * 模拟数据生成器
 * 为应用提供预生成的示例数据，帮助用户理解功能
 */

import { EmotionRecord, Tag, EmotionStats, TrendDataPoint, WordCloudData } from '../types';
import { EMOTION_CONFIGS, PRESET_TAGS } from './constants';

/**
 * 生成随机日期
 * @param daysAgo 几天前
 * @returns ISO 日期字符串
 */
function getRandomDate(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  // 随机设置时间
  date.setHours(Math.floor(Math.random() * 24));
  date.setMinutes(Math.floor(Math.random() * 60));
  return date.toISOString();
}

/**
 * 生成随机情绪记录
 * @param id 记录ID
 * @param daysAgo 几天前
 * @returns 情绪记录对象
 */
function generateMockRecord(id: string, daysAgo: number): EmotionRecord {
  const emotionTypes = Object.keys(EMOTION_CONFIGS);
  const randomEmotion = emotionTypes[Math.floor(Math.random() * emotionTypes.length)];
  const recordedAt = getRandomDate(daysAgo);
  
  // 根据情绪类型生成相应的日记内容
  const diaryContents = {
    happy: [
      '今天心情特别好！工作进展顺利，和朋友聊天也很开心。',
      '阳光明媚的一天，做了喜欢的事情，感觉生活充满希望。',
      '收到了好消息，整个人都轻松了很多，笑容满面。'
    ],
    sad: [
      '今天有些低落，可能是天气的原因，总觉得心情沉重。',
      '想起了一些往事，心情有点复杂，需要时间来调整。',
      '工作上遇到了挫折，感觉有些失望，但相信明天会更好。'
    ],
    anxious: [
      '明天有重要的会议，心里有些紧张，希望一切顺利。',
      '最近压力有点大，总是担心各种事情，需要放松一下。',
      '对未来有些不确定，心里七上八下的，需要静下心来思考。'
    ],
    calm: [
      '今天很平静，做了冥想，感觉内心很安宁。',
      '散步的时候看到夕阳，心情变得很平和，生活真美好。',
      '读了一本好书，思绪清晰，感觉很充实。'
    ],
    angry: [
      '今天遇到了一些不公平的事情，心里很愤怒，需要发泄一下。',
      '交通堵塞让我很烦躁，情绪有些失控，要学会控制。',
      '和同事产生了分歧，心情不太好，希望能够理解彼此。'
    ],
    excited: [
      '今天收到了期待已久的好消息，兴奋得睡不着！',
      '计划了很久的旅行终于要开始了，心情超级激动！',
      '学会了新技能，成就感满满，对未来充满期待。'
    ],
    tired: [
      '今天工作了一整天，身心俱疲，需要好好休息。',
      '最近睡眠不足，感觉很疲惫，要调整作息时间。',
      '连续加班几天了，精力有些透支，周末要好好放松。'
    ],
    neutral: [
      '今天是平常的一天，没有特别的事情发生。',
      '心情比较平稳，按部就班地完成了日常工作。',
      '普通的一天，但也有它的美好之处。'
    ]
  };
  
  const contents = diaryContents[randomEmotion as keyof typeof diaryContents];
  const randomContent = contents[Math.floor(Math.random() * contents.length)];
  
  return {
    id,
    user_id: 'mock-user-id',
    emotion_type: randomEmotion as any,
    emotion_intensity: (Math.floor(Math.random() * 5) + 1) as any,
    diary_content: randomContent,
    recorded_at: recordedAt,
    created_at: recordedAt,
    updated_at: recordedAt,
    tags: PRESET_TAGS.slice(0, Math.floor(Math.random() * 3) + 1).map((tag, index) => ({
      ...tag,
      id: `tag-${index}`,
      created_at: recordedAt
    }))
  };
}

/**
 * 生成模拟情绪记录数据
 * @param count 记录数量
 * @returns 情绪记录数组
 */
export function generateMockRecords(count: number = 30): EmotionRecord[] {
  const records: EmotionRecord[] = [];
  
  for (let i = 0; i < count; i++) {
    const daysAgo = Math.floor(Math.random() * 90); // 90天内的随机日期
    records.push(generateMockRecord(`record-${i + 1}`, daysAgo));
  }
  
  // 按日期排序（最新的在前）
  return records.sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime());
}

/**
 * 生成情绪统计数据
 * @param records 情绪记录数组
 * @returns 情绪统计数组
 */
export function generateEmotionStats(records: EmotionRecord[]): EmotionStats[] {
  const emotionCounts: Record<string, { count: number; totalIntensity: number }> = {};
  
  // 统计各情绪的出现次数和强度总和
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
    percentage: Math.round((data.count / totalRecords) * 100),
    avg_intensity: Math.round((data.totalIntensity / data.count) * 10) / 10
  }));
}

/**
 * 生成趋势数据
 * @param records 情绪记录数组
 * @param days 天数
 * @returns 趋势数据点数组
 */
export function generateTrendData(records: EmotionRecord[], days: number = 30): TrendDataPoint[] {
  const trendData: TrendDataPoint[] = [];
  const today = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    
    // 获取当天的记录
    const dayRecords = records.filter(record => {
      const recordDate = new Date(record.recorded_at).toISOString().split('T')[0];
      return recordDate === dateStr;
    });
    
    if (dayRecords.length > 0) {
      // 计算当天的平均情绪强度
      const avgIntensity = dayRecords.reduce((sum, record) => sum + record.emotion_intensity, 0) / dayRecords.length;
      // 获取最频繁的情绪类型
      const emotionCounts: Record<string, number> = {};
      dayRecords.forEach(record => {
        emotionCounts[record.emotion_type] = (emotionCounts[record.emotion_type] || 0) + 1;
      });
      const mostFrequentEmotion = Object.entries(emotionCounts).reduce((a, b) => a[1] > b[1] ? a : b)[0];
      
      trendData.push({
        date: dateStr,
        emotion_type: mostFrequentEmotion as any,
        intensity: Math.round(avgIntensity) as any,
        count: dayRecords.length
      });
    }
  }
  
  return trendData;
}

/**
 * 生成词云数据
 * @param records 情绪记录数组
 * @returns 词云数据数组
 */
export function generateWordCloudData(records: EmotionRecord[]): WordCloudData[] {
  const wordCounts: Record<string, number> = {};
  
  // 提取所有日记内容中的词汇
  records.forEach(record => {
    if (record.diary_content) {
      // 简单的中文分词（实际项目中可能需要更复杂的分词算法）
      const words = record.diary_content
        .replace(/[，。！？；：