export interface Subscription {
  id: string
  email: string
  frequency: 'daily' | 'weekly'
  topic: string
  language: 'hakka' | 'bilingual'
  tone: 'casual' | 'educational' | 'storytelling' | 'interview'
  isActive: boolean
  createdAt: string
  lastSent?: string
  preferences: SubscriptionPreferences
}

export interface SubscriptionPreferences {
  deliveryTime: string // "08:00" format
  deliveryDays?: number[] // 0-6, Sunday=0, only for weekly
  maxDuration: number // minutes
  includeTranscript: boolean
  includeRomanization: boolean
  notificationEmail: boolean
}

export interface SubscriptionRequest {
  email: string
  frequency: 'daily' | 'weekly'
  topic: string
  language: 'hakka' | 'bilingual'
  tone: 'casual' | 'educational' | 'storytelling' | 'interview'
  preferences: SubscriptionPreferences
}

export interface PodcastFeed {
  id: string
  title: string
  description: string
  episodes: PodcastEpisode[]
  lastUpdated: string
  rssUrl: string
}

export interface PodcastEpisode {
  id: string
  title: string
  description: string
  audioUrl: string
  publishedAt: string
  duration: number
  topics: string[]
  hakkaContent: string
  chineseContent: string
  romanization?: string
}

export interface EmailTemplate {
  subject: string
  htmlContent: string
  textContent: string
  podcastUrl: string
  unsubscribeUrl: string
}