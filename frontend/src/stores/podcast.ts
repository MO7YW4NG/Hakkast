import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Podcast, PodcastGenerationRequest } from '../types/podcast'

export const usePodcastStore = defineStore('podcast', () => {
  const podcasts = ref<Podcast[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const generatePodcast = async (request: PodcastGenerationRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await fetch('/api/podcasts/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const podcast = await response.json()
      podcasts.value.unshift(podcast)
      return podcast
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to generate podcast'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchPodcasts = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await fetch('/api/podcasts')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      podcasts.value = await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcasts'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const getPodcast = async (id: string) => {
    try {
      const response = await fetch(`/api/podcasts/${id}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch podcast'
      throw err
    }
  }

  const deletePodcast = async (id: string) => {
    try {
      const response = await fetch(`/api/podcasts/${id}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      podcasts.value = podcasts.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete podcast'
      throw err
    }
  }

  return {
    podcasts,
    isLoading,
    error,
    generatePodcast,
    fetchPodcasts,
    getPodcast,
    deletePodcast,
  }
})