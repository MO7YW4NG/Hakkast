import { 
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
} from './mockData'
import type { Podcast, PodcastGenerationRequest } from '../types/podcast'
import type { Subscription, SubscriptionRequest, PodcastFeed } from '../types/subscription'

// Simulate delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Simulate random delay (100-500ms)
const randomDelay = () => delay(Math.random() * 400 + 100)

// Mock podcast generation service
export class MockPodcastService {
  private static instance: MockPodcastService
  
  static getInstance(): MockPodcastService {
    if (!MockPodcastService.instance) {
      MockPodcastService.instance = new MockPodcastService()
    }
    return MockPodcastService.instance
  }

  // Generate podcast
  async generatePodcast(request: PodcastGenerationRequest): Promise<Podcast> {
    await randomDelay()
    
    // Simulate generation process
    const newPodcast: Podcast = {
      id: `podcast-${Date.now()}`,
      title: this.generateTitle(request.topic, request.tone),
      chineseContent: this.generateContent(request.topic, request.tone),
      hakkaContent: this.generateContent(request.topic, request.tone),
      romanization: this.generateRomanization(request.topic),
      topic: request.topic,
      tone: request.tone,
      duration: request.duration,
      language: request.language,
      interests: request.interests,
      createdAt: new Date().toISOString(),
      audioUrl: `/sample-podcast.wav`,
      audioDuration: request.duration
    }
    
    // Add to mock data
    mockPodcasts.unshift(newPodcast)
    
    return newPodcast
  }

  // Get all podcasts
  async getPodcasts(): Promise<Podcast[]> {
    await randomDelay()
    return [...mockPodcasts]
  }

  // Get podcast by ID
  async getPodcast(id: string): Promise<Podcast | null> {
    await randomDelay()
    return mockPodcasts.find(p => p.id === id) || null
  }

  // Delete podcast
  async deletePodcast(id: string): Promise<void> {
    await randomDelay()
    const index = mockPodcasts.findIndex(p => p.id === id)
    if (index > -1) {
      mockPodcasts.splice(index, 1)
    }
  }

  // Search podcasts
  async searchPodcasts(query: string): Promise<Podcast[]> {
    await randomDelay()
    const lowercaseQuery = query.toLowerCase()
    return mockPodcasts.filter(p => 
      p.title.toLowerCase().includes(lowercaseQuery) ||
      p.chineseContent.toLowerCase().includes(lowercaseQuery) ||
      p.topic.toLowerCase().includes(lowercaseQuery)
    )
  }

  // Filter podcasts by topic
  async getPodcastsByTopic(topic: string): Promise<Podcast[]> {
    await randomDelay()
    return mockPodcasts.filter(p => p.topic === topic)
  }

  // Get generation status
  async getGenerationStatus(): Promise<typeof mockGenerationStatus> {
    await randomDelay()
    return { ...mockGenerationStatus }
  }

  // Get generation history
  async getGenerationHistory(): Promise<typeof mockGenerationHistory> {
    await randomDelay()
    return [...mockGenerationHistory]
  }

  // Get statistics
  async getStats(): Promise<typeof mockStats> {
    await randomDelay()
    return { ...mockStats }
  }

  // Get trending topics
  async getTrendingTopics(): Promise<typeof mockTrendingTopics> {
    await randomDelay()
    return [...mockTrendingTopics]
  }

  // Get search suggestions
  async getSearchSuggestions(query: string): Promise<string[]> {
    await randomDelay()
    const lowercaseQuery = query.toLowerCase()
    return mockSearchSuggestions.filter(suggestion => 
      suggestion.toLowerCase().includes(lowercaseQuery)
    ).slice(0, 5)
  }

  // Get user feedback
  async getUserFeedback(): Promise<typeof mockUserFeedback> {
    await randomDelay()
    return [...mockUserFeedback]
  }

  // Add user feedback
  async addUserFeedback(podcastId: string, rating: number, comment: string): Promise<void> {
    await randomDelay()
    const newFeedback = {
      id: `feedback-${Date.now()}`,
      podcastId,
      rating,
      comment,
      timestamp: new Date().toISOString(),
      userEmail: mockUser.email
    }
    mockUserFeedback.push(newFeedback)
  }

  // Private method: Generate title
  private generateTitle(topic: string, _tone: string): string {
    const topicTitles = {
      research_deep_learning: [
        '深度學習在醫療影像診斷中的突破性應用',
        '人工智慧在教育領域的創新應用',
        '機器學習算法優化的最新進展',
        '神經網絡在自然語言處理中的應用'
      ],
      technology_news: [
        '量子計算：未來科技的新前沿',
        '區塊鏈技術在供應鏈管理中的應用',
        '5G技術推動智慧城市發展',
        '物聯網設備的安全挑戰與解決方案'
      ],
      finance_economics: [
        '永續投資：ESG理念如何改變金融市場',
        '數位貨幣對傳統銀行的衝擊',
        '綠色金融：氣候變遷下的投資機會',
        '人工智慧在風險管理中的應用'
      ]
    }
    
    const titles = topicTitles[topic as keyof typeof topicTitles] || ['新播客內容']
    return titles[Math.floor(Math.random() * titles.length)]
  }

  // Private method: Generate content
  private generateContent(topic: string, _tone: string): string {
    const baseContent = {
      research_deep_learning: '深度學習技術正在各個領域展現出驚人的潛力。透過先進的算法和大量的數據訓練，AI系統能夠完成以往需要人類專家才能完成的複雜任務。這項技術不僅提高了工作效率，還為科學研究和實際應用開闢了新的可能性。',
      technology_news: '科技產業正在經歷前所未有的變革，新技術層出不窮，為人類社會帶來深遠的影響。從人工智慧到量子計算，從區塊鏈到物聯網，這些創新技術正在重塑我們的生活方式和工作模式。',
      finance_economics: '金融市場和經濟環境正在經歷重大轉型，數位化技術的普及和永續發展理念的興起，正在改變傳統的投資思維和商業模式。投資者越來越關注企業的社會責任和環境影響。'
    }
    
    return baseContent[topic as keyof typeof baseContent] || '這是一個關於最新科技發展的播客內容。'
  }

  // Private method: Generate romanization
  private generateRomanization(topic: string): string {
    const romanizations = {
      research_deep_learning: 'tsim1 tshu5 hok8 sip8 ki4 sut8',
      technology_news: 'ki4 sut8 sin5 mun5',
      finance_economics: 'kim5 yung5 king5 ki5'
    }
    
    return romanizations[topic as keyof typeof romanizations] || 'mo5 kuk5'
  }
}

// Mock subscription service
export class MockSubscriptionService {
  private static instance: MockSubscriptionService
  
  static getInstance(): MockSubscriptionService {
    if (!MockSubscriptionService.instance) {
      MockSubscriptionService.instance = new MockSubscriptionService()
    }
    return MockSubscriptionService.instance
  }

  // Create subscription
  async createSubscription(subscriptionData: SubscriptionRequest): Promise<Subscription> {
    await randomDelay()
    
    const newSubscription: Subscription = {
      id: `sub-${Date.now()}`,
      email: subscriptionData.email,
      frequency: subscriptionData.frequency,
      topic: subscriptionData.topic,
      language: subscriptionData.language,
      tone: subscriptionData.tone,
      isActive: true,
      createdAt: new Date().toISOString(),
      lastSent: undefined,
      preferences: subscriptionData.preferences
    }
    
    mockSubscriptions.push(newSubscription)
    return newSubscription
  }

  // Get subscription
  async getSubscription(subscriptionId: string): Promise<Subscription | null> {
    await randomDelay()
    return mockSubscriptions.find(s => s.id === subscriptionId) || null
  }

  // Get subscriptions by email
  async getSubscriptionsByEmail(email: string): Promise<Subscription[]> {
    await randomDelay()
    return mockSubscriptions.filter(s => s.email === email)
  }

  // Update subscription
  async updateSubscription(subscriptionId: string, updateData: Partial<SubscriptionRequest>): Promise<Subscription> {
    await randomDelay()
    
    const subscription = mockSubscriptions.find(s => s.id === subscriptionId)
    if (!subscription) {
      throw new Error('Subscription not found')
    }
    
    Object.assign(subscription, updateData)
    return subscription
  }

  // Toggle subscription status
  async toggleSubscription(subscriptionId: string): Promise<Subscription> {
    await randomDelay()
    
    const subscription = mockSubscriptions.find(s => s.id === subscriptionId)
    if (!subscription) {
      throw new Error('Subscription not found')
    }
    
    subscription.isActive = !subscription.isActive
    return subscription
  }

  // Delete subscription
  async deleteSubscription(subscriptionId: string): Promise<void> {
    await randomDelay()
    
    const index = mockSubscriptions.findIndex(s => s.id === subscriptionId)
    if (index > -1) {
      mockSubscriptions.splice(index, 1)
    }
  }

  // Get RSS URL
  getRSSUrl(subscriptionId: string, token: string): string {
    return `/api/subscription/rss/${subscriptionId}?token=${token}`
  }

  // Get unsubscribe URL
  getUnsubscribeUrl(subscriptionId: string): string {
    return `/api/subscription/unsubscribe/${subscriptionId}`
  }

  // Get podcast feed
  async getPodcastFeeds(): Promise<PodcastFeed[]> {
    await randomDelay()
    return [...mockPodcastFeeds]
  }

  // Get feed by subscription ID
  async getPodcastFeedBySubscription(subscriptionId: string): Promise<PodcastFeed | null> {
    await randomDelay()
    
    const subscription = mockSubscriptions.find(s => s.id === subscriptionId)
    if (!subscription) {
      return null
    }
    
    return mockPodcastFeeds.find(f => 
      f.episodes.some((e: any) => e.topics.includes(subscription.topic))
    ) || null
  }
}

// Mock user service
export class MockUserService {
  private static instance: MockUserService
  
  static getInstance(): MockUserService {
    if (!MockUserService.instance) {
      MockUserService.instance = new MockUserService()
    }
    return MockUserService.instance
  }

  // Get user information
  async getUser(): Promise<typeof mockUser> {
    await randomDelay()
    return { ...mockUser }
  }

  // Get notifications
  async getNotifications(): Promise<typeof mockNotifications> {
    await randomDelay()
    return [...mockNotifications]
  }

  // Mark notification as read
  async markNotificationAsRead(notificationId: string): Promise<void> {
    await randomDelay()
    
    const notification = mockNotifications.find(n => n.id === notificationId)
    if (notification) {
      notification.isRead = true
    }
  }

  // Get system settings
  async getSystemSettings(): Promise<typeof mockSystemSettings> {
    await randomDelay()
    return { ...mockSystemSettings }
  }

  // Update system settings
  async updateSystemSettings(settings: Partial<typeof mockSystemSettings>): Promise<typeof mockSystemSettings> {
    await randomDelay()
    
    Object.assign(mockSystemSettings, settings)
    return { ...mockSystemSettings }
  }
}

// Export singleton instances
export const mockPodcastService = MockPodcastService.getInstance()
export const mockSubscriptionService = MockSubscriptionService.getInstance()
export const mockUserService = MockUserService.getInstance()

// Export all mock data
export {
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
