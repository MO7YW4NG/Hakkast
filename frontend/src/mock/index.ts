// Mock Data unified export file
// Provides complete fake demo data and services

// Core data
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
} from './mockData'

// Mock services
export {
  mockPodcastService,
  mockSubscriptionService,
  mockUserService,
  MockPodcastService,
  MockSubscriptionService,
  MockUserService
} from './mockService'

// Mock Store
export { useMockPodcastStore } from '../stores/mockPodcastStore'
export { useMockSubscriptionStore } from '../stores/mockSubscriptionStore'
export { useMockUserStore } from '../stores/mockUserStore'

// Type definitions
export type { Podcast, PodcastGenerationRequest } from '../types/podcast'
export type { Subscription, SubscriptionRequest, PodcastFeed, PodcastEpisode } from '../types/subscription'

// Default export
export default {
      // Data
  data: {
    podcasts: () => import('./mockData').then(m => m.mockPodcasts),
    subscriptions: () => import('./mockData').then(m => m.mockSubscriptions),
    user: () => import('./mockData').then(m => m.mockUser),
    stats: () => import('./mockData').then(m => m.mockStats)
  },
  
      // Services
  services: {
    podcast: () => import('./mockService').then(m => m.mockPodcastService),
    subscription: () => import('./mockService').then(m => m.mockSubscriptionService),
    user: () => import('./mockService').then(m => m.mockUserService)
  },
  
  // Store
  stores: {
    podcast: () => import('../stores/mockPodcastStore').then(m => m.useMockPodcastStore),
    subscription: () => import('../stores/mockSubscriptionStore').then(m => m.useMockSubscriptionStore),
    user: () => import('../stores/mockUserStore').then(m => m.useMockUserStore)
  }
}
