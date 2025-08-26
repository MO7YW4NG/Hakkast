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

  // 生成播客
  const generatePodcast = async (request: PodcastGenerationRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      // 模拟生成过程
      generationStatus.value.isGenerating = true
      generationStatus.value.progress = 0
      
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        if (generationStatus.value.progress < 100) {
          generationStatus.value.progress += Math.random() * 20
          if (generationStatus.value.progress > 100) {
            generationStatus.value.progress = 100
          }
          
          // 更新当前步骤
          const stepIndex = Math.floor(generationStatus.value.progress / 16.67)
          if (stepIndex < generationStatus.value.steps.length) {
            generationStatus.value.currentStep = generationStatus.value.steps[stepIndex]
          }
        }
      }, 500)
      
      // 调用mock service生成播客
      const podcast = await mockPodcastService.generatePodcast(request)
      
      // 清除进度更新
      clearInterval(progressInterval)
      generationStatus.value.isGenerating = false
      generationStatus.value.progress = 100
      generationStatus.value.currentStep = '完成'
      
      // 添加到播客列表
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

  // 获取所有播客
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

  // 根据ID获取播客
  const getPodcast = async (id: string) => {
    try {
      return await mockPodcastService.getPodcast(id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcast'
      throw err
    }
  }

  // 删除播客
  const deletePodcast = async (id: string) => {
    try {
      await mockPodcastService.deletePodcast(id)
      podcasts.value = podcasts.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete podcast'
      throw err
    }
  }

  // 搜索播客
  const searchPodcasts = async (query: string) => {
    try {
      return await mockPodcastService.searchPodcasts(query)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to search podcasts'
      throw err
    }
  }

  // 根据主题筛选播客
  const getPodcastsByTopic = async (topic: string) => {
    try {
      return await mockPodcastService.getPodcastsByTopic(topic)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcasts by topic'
      throw err
    }
  }

  // 获取生成状态
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

  // 获取生成历史
  const getGenerationHistory = async () => {
    try {
      return await mockPodcastService.getGenerationHistory()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch generation history'
      throw err
    }
  }

  // 获取统计数据
  const getStats = async () => {
    try {
      return await mockPodcastService.getStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch stats'
      throw err
    }
  }

  // 获取热门话题
  const getTrendingTopics = async () => {
    try {
      return await mockPodcastService.getTrendingTopics()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch trending topics'
      throw err
    }
  }

  // 获取搜索建议
  const getSearchSuggestions = async (query: string) => {
    try {
      return await mockPodcastService.getSearchSuggestions(query)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch search suggestions'
      throw err
    }
  }

  // 获取用户反馈
  const getUserFeedback = async () => {
    try {
      return await mockPodcastService.getUserFeedback()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch user feedback'
      throw err
    }
  }

  // 添加用户反馈
  const addUserFeedback = async (podcastId: string, rating: number, comment: string) => {
    try {
      await mockPodcastService.addUserFeedback(podcastId, rating, comment)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add user feedback'
      throw err
    }
  }

  // 重置生成状态
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
