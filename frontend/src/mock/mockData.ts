import type { Podcast, PodcastGenerationRequest } from '../types/podcast'
import type { Subscription, PodcastFeed } from '../types/subscription'

// Mock podcast data
export const mockPodcasts: Podcast[] = [
  {
    id: 'podcast-001',
    title: '深度學習在醫療影像診斷中的突破性應用',
    chineseContent: '深度學習技術在醫療影像診斷領域展現出驚人的潛力。透過卷積神經網絡和遷移學習，AI系統能夠以接近人類專家的準確率識別X光片、CT掃描和MRI圖像中的異常。這項技術不僅提高了診斷效率，還能在早期階段發現疾病，為患者爭取寶貴的治療時間。',
    hakkaContent: '深度學習技術在醫療影像診斷領域展現出驚人的潛力。透過卷積神經網絡和遷移學習，AI系統能夠以接近人類專家的準確率識別X光片、CT掃描和MRI圖像中的異常。這項技術不僅提高了診斷效率，還能在早期階段發現疾病，為患者爭取寶貴的治療時間。',
    romanization: 'tsim1 tshu5 hok8 sip8 ki4 sut8 tsai1 i1 liau5 iang5 siang5 tsan1 tu5 tsung1 ti1 thuat8 pho5 sing5 ki5 ung5 yung5',
    topic: 'research_deep_learning',
    tone: 'educational',
    duration: 15,
    language: 'bilingual',
    interests: 'AI, 醫療科技, 深度學習',
    createdAt: '2024-01-15T10:30:00Z',
    audioUrl: '/static/audio/podcast-001.mp3',
    audioDuration: 15
  },
  {
    id: 'podcast-002',
    title: '量子計算：未來科技的新前沿',
    chineseContent: '量子計算代表了計算技術的下一個重大突破。與傳統計算機使用二進制位不同，量子計算機利用量子比特的疊加態和糾纏特性，能夠同時處理多個計算任務。這使得量子計算機在密碼學、藥物發現和氣候建模等領域具有巨大優勢。',
    hakkaContent: '量子計算代表了計算技術的下一個重大突破。與傳統計算機使用二進制位不同，量子計算機利用量子比特的疊加態和糾纏特性，能夠同時處理多個計算任務。這使得量子計算機在密碼學、藥物發現和氣候建模等領域具有巨大優勢。',
    romanization: 'lien5 tsu3 kien5 sut8 tai5 piau5 liau5 kien5 sut8 ki4 sut8 ti1 ha5 i1 ke5 tshung5 ta5 pho5 thuat8',
    topic: 'technology_news',
    tone: 'casual',
    duration: 12,
    language: 'hakka',
    interests: '量子科技, 計算機科學',
    createdAt: '2024-01-14T14:20:00Z',
    audioUrl: '/static/audio/podcast-002.mp3',
    audioDuration: 12
  },
  {
    id: 'podcast-003',
    title: '永續投資：ESG理念如何改變金融市場',
    chineseContent: '環境、社會和治理（ESG）投資理念正在重塑全球金融市場。投資者越來越關注企業的永續發展表現，這推動了綠色債券、社會責任投資和影響力投資的快速增長。ESG投資不僅能帶來財務回報，還能創造正面的社會和環境影響。',
    hakkaContent: '環境、社會和治理（ESG）投資理念正在重塑全球金融市場。投資者越來越關注企業的永續發展表現，這推動了綠色債券、社會責任投資和影響力投資的快速增長。ESG投資不僅能帶來財務回報，還能創造正面的社會和環境影響。',
    romanization: 'yun5 siok8 thau5 tsi5 ESG li5 ngien5 ho5 nai5 kai5 pien5 kim5 yung5 shi5 tshiong5',
    topic: 'finance_economics',
    tone: 'storytelling',
    duration: 18,
    language: 'bilingual',
    interests: '投資理財, 永續發展, 金融科技',
    createdAt: '2024-01-13T09:15:00Z',
    audioUrl: '/static/audio/podcast-003.mp3',
    audioDuration: 18
  },
  {
    id: 'podcast-004',
    title: '人工智慧在教育領域的創新應用',
    chineseContent: 'AI技術正在改變傳統教育模式，為學生提供個性化學習體驗。智能輔導系統能夠根據學生的學習進度和理解程度調整教學內容，虛擬現實技術則讓抽象概念變得具體可感。這些創新不僅提高了學習效率，還激發了學生的學習興趣。',
    hakkaContent: 'AI技術正在改變傳統教育模式，為學生提供個性化學習體驗。智能輔導系統能夠根據學生的學習進度和理解程度調整教學內容，虛擬現實技術則讓抽象概念變得具體可感。這些創新不僅提高了學習效率，還激發了學生的學習興趣。',
    romanization: 'ngin5 kung5 tshi5 ngie5 tsai1 kau5 yuk8 ling5 yuk8 ti1 tshung5 sin5 ung5 yung5',
    topic: 'research_deep_learning',
    tone: 'interview',
    duration: 20,
    language: 'hakka',
    interests: '教育科技, AI應用, 學習創新',
    createdAt: '2024-01-12T16:45:00Z',
    audioUrl: '/static/audio/podcast-004.mp3',
    audioDuration: 20
  },
  {
    id: 'podcast-005',
    title: '區塊鏈技術在供應鏈管理中的應用',
    chineseContent: '區塊鏈技術為供應鏈管理帶來了前所未有的透明度和可追溯性。透過分布式賬本技術，企業能夠實時追蹤產品從原材料到最終消費者的完整旅程。這不僅提高了供應鏈效率，還增強了食品安全和產品真實性的驗證能力。',
    hakkaContent: '區塊鏈技術為供應鏈管理帶來了前所未有的透明度和可追溯性。透過分布式賬本技術，企業能夠實時追蹤產品從原材料到最終消費者的完整旅程。這不僅提高了供應鏈效率，還增強了食品安全和產品真實性的驗證能力。',
    romanization: 'khi5 khau5 lien5 ki4 sut8 tsai1 kung5 ying5 lien5 kuan5 li5 tsung1 ti1 ung5 yung5',
    topic: 'technology_news',
    tone: 'educational',
    duration: 16,
    language: 'bilingual',
    interests: '區塊鏈, 供應鏈, 數位轉型',
    createdAt: '2024-01-11T11:30:00Z',
    audioUrl: '/static/audio/podcast-005.mp3',
    audioDuration: 16
  }
]

// Mock subscription data
export const mockSubscriptions: Subscription[] = [
  {
    id: 'sub-001',
    email: 'user@example.com',
    frequency: 'daily',
    topic: 'research_deep_learning',
    language: 'bilingual',
    tone: 'educational',
    isActive: true,
    createdAt: '2024-01-10T08:00:00Z',
    lastSent: '2024-01-15T08:00:00Z',
    preferences: {
      deliveryTime: '08:00',
      deliveryDays: [1, 2, 3, 4, 5],
      maxDuration: 15,
      includeTranscript: true,
      includeRomanization: true,
      notificationEmail: true
    }
  },
  {
    id: 'sub-002',
    email: 'user@example.com',
    frequency: 'weekly',
    topic: 'technology_news',
    language: 'hakka',
    tone: 'casual',
    isActive: true,
    createdAt: '2024-01-08T10:00:00Z',
    lastSent: '2024-01-14T10:00:00Z',
    preferences: {
      deliveryTime: '10:00',
      deliveryDays: [1, 4],
      maxDuration: 20,
      includeTranscript: true,
      includeRomanization: false,
      notificationEmail: true
    }
  },
  {
    id: 'sub-003',
    email: 'user@example.com',
    frequency: 'weekly',
    topic: 'finance_economics',
    language: 'bilingual',
    tone: 'storytelling',
    isActive: false,
    createdAt: '2024-01-05T14:00:00Z',
    lastSent: '2024-01-12T14:00:00Z',
    preferences: {
      deliveryTime: '14:00',
      deliveryDays: [2, 5],
      maxDuration: 25,
      includeTranscript: true,
      includeRomanization: true,
      notificationEmail: false
    }
  }
]

// Mock podcast generation request data
export const mockGenerationRequests: PodcastGenerationRequest[] = [
  {
    topic: 'research_deep_learning',
    tone: 'educational',
    duration: 15,
    language: 'bilingual',
    interests: 'AI, 醫療科技, 深度學習'
  },
  {
    topic: 'technology_news',
    tone: 'casual',
    duration: 12,
    language: 'hakka',
    interests: '量子科技, 計算機科學'
  },
  {
    topic: 'finance_economics',
    tone: 'storytelling',
    duration: 18,
    language: 'bilingual',
    interests: '投資理財, 永續發展, 金融科技'
  }
]

// Mock podcast feed data
export const mockPodcastFeeds: PodcastFeed[] = [
  {
    id: 'feed-001',
    title: '深度學習研究播客',
    description: '每日更新的深度學習研究前沿資訊，結合客家文化視角，為您提供專業且易懂的AI知識。',
    episodes: mockPodcasts.filter(p => p.topic === 'research_deep_learning').map(p => ({
      id: p.id,
      title: p.title,
      description: p.chineseContent.substring(0, 100) + '...',
      audioUrl: p.audioUrl || '',
      publishedAt: p.createdAt,
      duration: p.audioDuration || p.duration * 60,
      topics: [p.topic],
      hakkaContent: p.hakkaContent,
      chineseContent: p.chineseContent,
      romanization: p.romanization
    })),
    lastUpdated: '2024-01-15T08:00:00Z',
    rssUrl: '/api/subscription/rss/feed-001?token=mock-token-001'
  },
  {
    id: 'feed-002',
    title: '科技新聞播客',
    description: '每週精選最新科技動態，用客語為您解讀科技趨勢，讓您掌握數位時代的脈動。',
    episodes: mockPodcasts.filter(p => p.topic === 'technology_news').map(p => ({
      id: p.id,
      title: p.title,
      description: p.chineseContent.substring(0, 100) + '...',
      audioUrl: p.audioUrl || '',
      publishedAt: p.createdAt,
      duration: p.audioDuration || p.duration * 60,
      topics: [p.topic],
      hakkaContent: p.hakkaContent,
      chineseContent: p.chineseContent,
      romanization: p.romanization
    })),
    lastUpdated: '2024-01-14T10:00:00Z',
    rssUrl: '/api/subscription/rss/feed-002?token=mock-token-002'
  }
]

// Mock user data
export const mockUser = {
  id: 'user-001',
  email: 'user@example.com',
  name: '客家播客愛好者',
  preferences: {
    defaultLanguage: 'bilingual',
    defaultTone: 'educational',
    defaultDuration: 15,
    favoriteTopics: ['research_deep_learning', 'technology_news']
  },
  stats: {
    totalPodcasts: 5,
    totalListeningTime: 81, // minutes
    favoriteTopic: 'research_deep_learning',
    subscriptionCount: 2
  }
}

// Mock generation status data
export const mockGenerationStatus = {
  isGenerating: false,
  progress: 0,
  currentStep: '',
  estimatedTime: 0,
  steps: [
    '分析主題內容',
    '爬取相關資訊',
    '生成播客腳本',
    '客語翻譯',
    '文字轉語音',
    '音頻後處理'
  ]
}

// Mock topic configuration data
export const mockTopicConfigs = [
  {
    value: 'research_deep_learning',
    label: '深度學習研究',
    emoji: '🧠',
    category: 'dynamic',
    badge: '研究',
    description: 'AI和機器學習領域的最新研究進展',
    color: 'blue',
    icon: '🔬'
  },
  {
    value: 'technology_news',
    label: '科技新聞',
    emoji: '💻',
    category: 'dynamic',
    badge: '最新',
    description: '全球科技產業的最新動態和趨勢',
    color: 'green',
    icon: '📱'
  },
  {
    value: 'finance_economics',
    label: '財經動態',
    emoji: '💰',
    category: 'dynamic',
    badge: '最新',
    description: '金融市場和經濟發展的最新資訊',
    color: 'orange',
    icon: '📊'
  }
]

// Mock podcast generation history
export const mockGenerationHistory = [
  {
    id: 'gen-001',
    topic: 'research_deep_learning',
    status: 'completed',
    createdAt: '2024-01-15T10:30:00Z',
    completedAt: '2024-01-15T10:45:00Z',
    duration: 15,
    language: 'bilingual',
    tone: 'educational',
    result: mockPodcasts[0]
  },
  {
    id: 'gen-002',
    topic: 'technology_news',
    status: 'completed',
    createdAt: '2024-01-14T14:20:00Z',
    completedAt: '2024-01-14T14:32:00Z',
    duration: 12,
    language: 'hakka',
    tone: 'casual',
    result: mockPodcasts[1]
  },
  {
    id: 'gen-003',
    topic: 'finance_economics',
    status: 'completed',
    createdAt: '2024-01-13T09:15:00Z',
    completedAt: '2024-01-13T09:33:00Z',
    duration: 18,
    language: 'bilingual',
    tone: 'storytelling',
    result: mockPodcasts[2]
  }
]

// Mock statistics data
export const mockStats = {
  totalPodcasts: 5,
  totalSubscriptions: 3,
  activeSubscriptions: 2,
  totalListeningTime: 81,
  averageDuration: 16.2,
  mostPopularTopic: 'research_deep_learning',
  mostPopularTone: 'educational',
  mostPopularLanguage: 'bilingual',
  weeklyGrowth: 25,
  monthlyGrowth: 120
}

// Mock notification data
export const mockNotifications = [
  {
    id: 'notif-001',
    type: 'podcast_ready',
    title: '新播客已準備就緒',
    message: '您的「深度學習在醫療影像診斷中的突破性應用」播客已生成完成',
    timestamp: '2024-01-15T10:45:00Z',
    isRead: false,
    actionUrl: '/library/podcast-001'
  },
  {
    id: 'notif-002',
    type: 'subscription_reminder',
    title: '訂閱提醒',
    message: '您的每日深度學習播客將在明天早上8點發送',
    timestamp: '2024-01-15T20:00:00Z',
    isRead: true,
    actionUrl: '/subscription'
  },
  {
    id: 'notif-003',
    type: 'system_update',
    title: '系統更新通知',
    message: '我們已更新客語TTS引擎，提供更自然的語音品質',
    timestamp: '2024-01-14T15:00:00Z',
    isRead: false,
    actionUrl: '/'
  }
]

// Mock search suggestions
export const mockSearchSuggestions = [
  '深度學習',
  '人工智慧',
  '機器學習',
  '自然語言處理',
  '電腦視覺',
  '量子計算',
  '區塊鏈',
  '雲端計算',
  '物聯網',
  '5G技術',
  '電動車',
  '再生能源',
  '永續發展',
  'ESG投資',
  '數位轉型'
]

// Mock trending topics
export const mockTrendingTopics = [
  {
    topic: 'research_deep_learning',
    label: '深度學習研究',
    count: 15,
    growth: '+25%',
    emoji: '🧠'
  },
  {
    topic: 'technology_news',
    label: '科技新聞',
    count: 12,
    growth: '+18%',
    emoji: '💻'
  },
  {
    topic: 'finance_economics',
    label: '財經動態',
    count: 8,
    growth: '+12%',
    emoji: '💰'
  }
]

// Mock user feedback
export const mockUserFeedback = [
  {
    id: 'feedback-001',
    podcastId: 'podcast-001',
    rating: 5,
    comment: '內容非常專業且易懂，客語發音清晰，很適合學習！',
    timestamp: '2024-01-15T11:00:00Z',
    userEmail: 'user@example.com'
  },
  {
    id: 'feedback-002',
    podcastId: 'podcast-002',
    rating: 4,
    comment: '量子計算的解釋很生動，希望能有更多相關主題',
    timestamp: '2024-01-14T15:30:00Z',
    userEmail: 'user@example.com'
  }
]

// Mock system settings
export const mockSystemSettings = {
  tts: {
    availableVoices: [
      { id: 'voice-001', name: '佳昀', gender: 'female', dialect: 'sihxian', preview: '/static/audio/voice-preview-001.mp3' },
      { id: 'voice-002', name: '敏權', gender: 'male', dialect: 'sihxian', preview: '/static/audio/voice-preview-002.mp3' },
      { id: 'voice-003', name: '美玲', gender: 'female', dialect: 'hailu', preview: '/static/audio/voice-preview-003.mp3' }
    ],
    defaultVoice: 'voice-001',
    speed: 1.0,
    pitch: 1.0
  },
  language: {
    defaultLanguage: 'bilingual',
    availableLanguages: ['hakka', 'bilingual'],
    romanizationSystem: 'numbered' // 'numbered' | 'tone_marks'
  },
  notification: {
    email: true,
    push: false,
    frequency: 'immediate'
  }
}

export default {
  mockPodcasts,
  mockSubscriptions,
  mockGenerationRequests,
  mockPodcastFeeds,
  mockUser,
  mockGenerationStatus,
  mockTopicConfigs,
  mockGenerationHistory,
  mockStats,
  mockNotifications,
  mockSearchSuggestions,
  mockTrendingTopics,
  mockUserFeedback,
  mockSystemSettings
}
