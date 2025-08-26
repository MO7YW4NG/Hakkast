import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Podcast, PodcastGenerationRequest } from '../types/podcast'
import { mockPodcastService } from '../mock/mockService'

export const useMockPodcastStore = defineStore('mockPodcast', () => {
  const podcasts = ref<Podcast[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const generationStatus = ref({
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
  })

  // Generate podcast
  const generatePodcast = async (request: PodcastGenerationRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      // Simulate generation process
      generationStatus.value.isGenerating = true
      generationStatus.value.progress = 0
      
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        if (generationStatus.value.progress < 100) {
          generationStatus.value.progress += Math.random() * 20
          if (generationStatus.value.progress > 100) {
            generationStatus.value.progress = 100
          }
          
          // Update current step
          const stepIndex = Math.floor(generationStatus.value.progress / 16.67)
          if (stepIndex < generationStatus.value.steps.length) {
            generationStatus.value.currentStep = generationStatus.value.steps[stepIndex]
          }
        }
      }, 500)
      
      // Call mock service to generate podcast
      const podcast = await mockPodcastService.generatePodcast(request)
      
      // Clear progress updater
      clearInterval(progressInterval)
      generationStatus.value.isGenerating = false
      generationStatus.value.progress = 100
      generationStatus.value.currentStep = '完成'
      
      // Add to podcast list
      podcasts.value.unshift(podcast)
      
      return podcast
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to generate podcast'
      generationStatus.value.isGenerating = false
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Fetch all podcasts
  const fetchPodcasts = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const fetchedPodcasts = await mockPodcastService.getPodcasts()
      podcasts.value = fetchedPodcasts
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcasts'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Get podcast by ID
  const getPodcast = async (id: string) => {
    try {
      return await mockPodcastService.getPodcast(id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcast'
      throw err
    }
  }

  // Delete podcast
  const deletePodcast = async (id: string) => {
    try {
      await mockPodcastService.deletePodcast(id)
      podcasts.value = podcasts.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete podcast'
      throw err
    }
  }

  // Search podcasts
  const searchPodcasts = async (query: string) => {
    try {
      return await mockPodcastService.searchPodcasts(query)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to search podcasts'
      throw err
    }
  }

  // Filter podcasts by topic
  const getPodcastsByTopic = async (topic: string) => {
    try {
      return await mockPodcastService.getPodcastsByTopic(topic)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcasts by topic'
      throw err
    }
  }

  // Fetch generation status
  const getGenerationStatus = async () => {
    try {
      const status = await mockPodcastService.getGenerationStatus()
      generationStatus.value = status
      return status
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch generation status'
      throw err
    }
  }

  // Fetch generation history
  const getGenerationHistory = async () => {
    try {
      return await mockPodcastService.getGenerationHistory()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch generation history'
      throw err
    }
  }

  // Fetch statistics
  const getStats = async () => {
    try {
      return await mockPodcastService.getStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch stats'
      throw err
    }
  }

  // Fetch trending topics
  const getTrendingTopics = async () => {
    try {
      return await mockPodcastService.getTrendingTopics()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch trending topics'
      throw err
    }
  }

  // Fetch search suggestions
  const getSearchSuggestions = async (query: string) => {
    try {
      return await mockPodcastService.getSearchSuggestions(query)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch search suggestions'
      throw err
    }
  }

  // Fetch user feedback
  const getUserFeedback = async () => {
    try {
      return await mockPodcastService.getUserFeedback()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch user feedback'
      throw err
    }
  }

  // Add user feedback
  const addUserFeedback = async (podcastId: string, rating: number, comment: string) => {
    try {
      await mockPodcastService.addUserFeedback(podcastId, rating, comment)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add user feedback'
      throw err
    }
  }

  // Reset generation status
  const resetGenerationStatus = () => {
    generationStatus.value = {
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
  }

  return {
    podcasts,
    isLoading,
    error,
    generationStatus,
    generatePodcast,
    fetchPodcasts,
    getPodcast,
    deletePodcast,
    searchPodcasts,
    getPodcastsByTopic,
    getGenerationStatus,
    getGenerationHistory,
    getStats,
    getTrendingTopics,
    getSearchSuggestions,
    getUserFeedback,
    addUserFeedback,
    resetGenerationStatus
  }
})
