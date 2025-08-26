import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Subscription, SubscriptionRequest, PodcastFeed } from '../types/subscription'
import { mockSubscriptionService } from '../mock/mockService'

export const useMockSubscriptionStore = defineStore('mockSubscription', () => {
  const subscriptions = ref<Subscription[]>([])
  const podcastFeeds = ref<PodcastFeed[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Create subscription
  const createSubscription = async (subscriptionData: SubscriptionRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const newSubscription = await mockSubscriptionService.createSubscription(subscriptionData)
      subscriptions.value.push(newSubscription)
      return newSubscription
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create subscription'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Fetch all subscriptions
  const fetchSubscriptions = async (email?: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      if (email) {
        const fetchedSubscriptions = await mockSubscriptionService.getSubscriptionsByEmail(email)
        subscriptions.value = fetchedSubscriptions
      } else {
        // If no email specified, fetch all subscriptions (for demo)
        subscriptions.value = await mockSubscriptionService.getSubscriptionsByEmail('user@example.com')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch subscriptions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Get subscription by ID
  const getSubscription = async (subscriptionId: string) => {
    try {
      return await mockSubscriptionService.getSubscription(subscriptionId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch subscription'
      throw err
    }
  }

  // Update subscription
  const updateSubscription = async (subscriptionId: string, updateData: Partial<SubscriptionRequest>) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updatedSubscription = await mockSubscriptionService.updateSubscription(subscriptionId, updateData)
      
      // Update local state
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index > -1) {
        subscriptions.value[index] = updatedSubscription
      }
      
      return updatedSubscription
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update subscription'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Toggle subscription status
  const toggleSubscription = async (subscriptionId: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      const updatedSubscription = await mockSubscriptionService.toggleSubscription(subscriptionId)
      
      // Update local state
      const index = subscriptions.value.findIndex(s => s.id === subscriptionId)
      if (index > -1) {
        subscriptions.value[index] = updatedSubscription
      }
      
      return updatedSubscription
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to toggle subscription'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Delete subscription
  const deleteSubscription = async (subscriptionId: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      await mockSubscriptionService.deleteSubscription(subscriptionId)
      
      // Remove from local state
      subscriptions.value = subscriptions.value.filter(s => s.id !== subscriptionId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete subscription'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Fetch podcast feeds
  const fetchPodcastFeeds = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const fetchedFeeds = await mockSubscriptionService.getPodcastFeeds()
      podcastFeeds.value = fetchedFeeds
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcast feeds'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Get feed by subscription ID
  const getPodcastFeedBySubscription = async (subscriptionId: string) => {
    try {
      return await mockSubscriptionService.getPodcastFeedBySubscription(subscriptionId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcast feed'
      throw err
    }
  }

  // Get RSS URL
  const getRSSUrl = (subscriptionId: string, token: string) => {
    return mockSubscriptionService.getRSSUrl(subscriptionId, token)
  }

  // Get unsubscribe URL
  const getUnsubscribeUrl = (subscriptionId: string) => {
    return mockSubscriptionService.getUnsubscribeUrl(subscriptionId)
  }

  // Get active subscription count
  const getActiveSubscriptionCount = () => {
    return subscriptions.value.filter(s => s.isActive).length
  }

  // Get subscription statistics
  const getSubscriptionStats = () => {
    const total = subscriptions.value.length
    const active = subscriptions.value.filter(s => s.isActive).length
    const daily = subscriptions.value.filter(s => s.frequency === 'daily').length
    const weekly = subscriptions.value.filter(s => s.frequency === 'weekly').length
    
    // Stats by topic
    const topicStats = subscriptions.value.reduce((acc, sub) => {
      acc[sub.topic] = (acc[sub.topic] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    // Stats by language
    const languageStats = subscriptions.value.reduce((acc, sub) => {
      acc[sub.language] = (acc[sub.language] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return {
      total,
      active,
      daily,
      weekly,
      topicStats,
      languageStats
    }
  }

  // Search subscriptions
  const searchSubscriptions = (query: string) => {
    const lowercaseQuery = query.toLowerCase()
    return subscriptions.value.filter(sub => 
      sub.topic.toLowerCase().includes(lowercaseQuery) ||
      sub.email.toLowerCase().includes(lowercaseQuery) ||
      sub.frequency.toLowerCase().includes(lowercaseQuery)
    )
  }

  // Filter subscriptions by topic
  const getSubscriptionsByTopic = (topic: string) => {
    return subscriptions.value.filter(sub => sub.topic === topic)
  }

  // Filter subscriptions by frequency
  const getSubscriptionsByFrequency = (frequency: 'daily' | 'weekly') => {
    return subscriptions.value.filter(sub => sub.frequency === frequency)
  }

  // Filter subscriptions by status
  const getSubscriptionsByStatus = (isActive: boolean) => {
    return subscriptions.value.filter(sub => sub.isActive === isActive)
  }

  // Reset state
  const resetState = () => {
    subscriptions.value = []
    podcastFeeds.value = []
    isLoading.value = false
    error.value = null
  }

  return {
    subscriptions,
    podcastFeeds,
    isLoading,
    error,
    createSubscription,
    fetchSubscriptions,
    getSubscription,
    updateSubscription,
    toggleSubscription,
    deleteSubscription,
    fetchPodcastFeeds,
    getPodcastFeedBySubscription,
    getRSSUrl,
    getUnsubscribeUrl,
    getActiveSubscriptionCount,
    getSubscriptionStats,
    searchSubscriptions,
    getSubscriptionsByTopic,
    getSubscriptionsByFrequency,
    getSubscriptionsByStatus,
    resetState
  }
})
