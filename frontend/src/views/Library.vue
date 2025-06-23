<template>
  <div class="min-h-screen py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-12">
        <div>
          <div class="inline-flex items-center space-x-2 bg-hakkast-gold/10 rounded-full px-4 py-2 mb-4">
            <span class="text-2xl">📚</span>
            <span class="text-sm font-medium text-hakkast-navy">我的播客庫存</span>
          </div>
          <h1 class="text-4xl lg:text-5xl font-display font-bold text-hakkast-navy mb-2">
            您的<span class="text-gradient">播客收藏</span>
          </h1>
          <p class="text-xl text-gray-600">管理和播放您創作的所有客語播客內容</p>
        </div>
        <div class="mt-6 sm:mt-0">
          <router-link to="/generate" class="btn btn-primary text-lg">
            <span class="mr-2">✨</span>
            創作新播客
          </router-link>
        </div>
      </div>

      <!-- Stats Bar -->
      <div v-if="podcasts.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
        <div class="card p-6 text-center">
          <div class="text-3xl font-bold text-hakkast-navy mb-2">{{ podcasts.length }}</div>
          <div class="text-sm text-gray-600">總播客數</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-3xl font-bold text-hakkast-purple mb-2">{{ totalDuration }}</div>
          <div class="text-sm text-gray-600">總時長(分)</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-3xl font-bold text-hakkast-lavender mb-2">{{ audioCount }}</div>
          <div class="text-sm text-gray-600">含語音</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-3xl font-bold text-hakkast-gold mb-2">{{ topTone }}</div>
          <div class="text-sm text-gray-600">常用風格</div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="podcasts.length === 0" class="text-center py-20">
        <div class="max-w-md mx-auto">
          <div class="w-32 h-32 bg-hakkast-gradient rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-xl">
            <span class="text-6xl">🎙️</span>
          </div>
          <h3 class="text-2xl font-display font-bold text-hakkast-navy mb-4">
            還沒有任何播客
          </h3>
          <p class="text-gray-600 mb-8 leading-relaxed">
            開始您的客語播客創作之旅吧！使用AI技術，幾分鐘內就能創造出專業品質的內容。
          </p>
          <router-link to="/generate" class="btn btn-primary text-lg">
            <span class="mr-2">🚀</span>
            創作第一個播客
          </router-link>
        </div>
      </div>
      
      <!-- Podcast Grid -->
      <div v-else class="space-y-8">
        <!-- Filter & Sort -->
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div class="flex flex-wrap gap-2">
            <button 
              v-for="filter in filterOptions"
              :key="filter.value"
              @click="currentFilter = filter.value"
              :class="[
                'px-4 py-2 rounded-xl font-medium transition-all duration-200',
                currentFilter === filter.value
                  ? 'bg-hakkast-gradient text-white shadow-lg'
                  : 'bg-white text-hakkast-navy border border-gray-200 hover:border-hakkast-purple'
              ]"
            >
              <span class="mr-2">{{ filter.emoji }}</span>
              {{ filter.label }}
            </button>
          </div>
          
          <select v-model="sortBy" class="input max-w-xs">
            <option value="newest">最新建立</option>
            <option value="oldest">最早建立</option>
            <option value="duration-long">時長較長</option>
            <option value="duration-short">時長較短</option>
          </select>
        </div>

        <!-- Podcasts Grid -->
        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="podcast in filteredPodcasts"
            :key="podcast.id"
            class="group"
          >
            <div class="card p-6 group-hover:scale-105 transition-all duration-300">
              <!-- Header -->
              <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                  <h3 class="text-lg font-semibold text-hakkast-navy line-clamp-2 mb-2">
                    {{ podcast.title }}
                  </h3>
                  <div class="flex items-center space-x-2 text-sm text-gray-500">
                    <span>{{ formatDate(podcast.createdAt) }}</span>
                    <span>•</span>
                    <span class="capitalize">{{ getToneLabel(podcast.tone) }}</span>
                  </div>
                </div>
                <div class="ml-3 flex-shrink-0">
                  <div class="w-12 h-12 bg-hakkast-gradient rounded-xl flex items-center justify-center shadow-lg">
                    <span class="text-white text-lg">{{ getToneEmoji(podcast.tone) }}</span>
                  </div>
                </div>
              </div>

              <!-- Meta Info -->
              <div class="space-y-3 mb-6">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">主題</span>
                  <span class="text-hakkast-navy font-medium truncate ml-2">{{ podcast.topic }}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">時長</span>
                  <span class="text-hakkast-purple font-medium">{{ podcast.duration }}分鐘</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">語言</span>
                  <span class="text-hakkast-lavender font-medium">{{ getLanguageLabel(podcast.language) }}</span>
                </div>
                <div v-if="podcast.audioUrl" class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">語音</span>
                  <div class="flex items-center space-x-1">
                    <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    <span class="text-green-600 font-medium">可播放</span>
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex space-x-3">
                <button
                  @click="playPodcast(podcast)"
                  class="btn btn-primary flex-1 text-sm"
                >
                  <span class="mr-2">▶️</span>
                  播放
                </button>
                <button
                  @click="deletePodcast(podcast.id)"
                  class="btn btn-secondary text-sm px-4"
                  title="刪除播客"
                >
                  🗑️
                </button>
                <button
                  class="btn btn-ghost text-sm px-4"
                  title="分享播客"
                >
                  📤
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Enhanced Podcast Player Modal -->
    <div v-if="selectedPodcast" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="max-w-5xl w-full max-h-[90vh] overflow-y-auto animate-slide-up">
        <PodcastPlayer :podcast="selectedPodcast" @close="closePlayer" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { usePodcastStore } from '../stores/podcast'
import PodcastPlayer from '../components/PodcastPlayer.vue'
import type { Podcast } from '../types/podcast'

const podcastStore = usePodcastStore()

const podcasts = computed(() => podcastStore.podcasts)
const selectedPodcast = ref<Podcast | null>(null)
const currentFilter = ref('all')
const sortBy = ref('newest')

const filterOptions = [
  { value: 'all', label: '全部', emoji: '📂' },
  { value: 'casual', label: '輕鬆對話', emoji: '😊' },
  { value: 'educational', label: '教育知識', emoji: '📚' },
  { value: 'storytelling', label: '故事敘述', emoji: '📖' },
  { value: 'interview', label: '訪談對話', emoji: '🎤' }
]

// Computed stats
const totalDuration = computed(() => {
  return podcasts.value.reduce((total, podcast) => total + podcast.duration, 0)
})

const audioCount = computed(() => {
  return podcasts.value.filter(podcast => podcast.audioUrl).length
})

const topTone = computed(() => {
  if (podcasts.value.length === 0) return '-'
  const toneCounts = podcasts.value.reduce((acc, podcast) => {
    acc[podcast.tone] = (acc[podcast.tone] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const mostFrequent = Object.entries(toneCounts).sort(([,a], [,b]) => b - a)[0]
  return getToneLabel(mostFrequent[0])
})

// Filtered and sorted podcasts
const filteredPodcasts = computed(() => {
  let filtered = podcasts.value
  
  // Apply filter
  if (currentFilter.value !== 'all') {
    filtered = filtered.filter(podcast => podcast.tone === currentFilter.value)
  }
  
  // Apply sort
  const sorted = [...filtered].sort((a, b) => {
    switch (sortBy.value) {
      case 'newest':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      case 'oldest':
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      case 'duration-long':
        return b.duration - a.duration
      case 'duration-short':
        return a.duration - b.duration
      default:
        return 0
    }
  })
  
  return sorted
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getToneLabel = (tone: string) => {
  const labels = {
    'casual': '輕鬆',
    'educational': '教育',
    'storytelling': '故事',
    'interview': '訪談'
  }
  return labels[tone as keyof typeof labels] || tone
}

const getToneEmoji = (tone: string) => {
  const emojis = {
    'casual': '😊',
    'educational': '📚',
    'storytelling': '📖',
    'interview': '🎤'
  }
  return emojis[tone as keyof typeof emojis] || '🎙️'
}

const getLanguageLabel = (language: string) => {
  const labels = {
    'hakka': '純客語',
    'mixed': '客華混合',
    'bilingual': '雙語'
  }
  return labels[language as keyof typeof labels] || language
}

const playPodcast = (podcast: Podcast) => {
  selectedPodcast.value = podcast
}

const closePlayer = () => {
  selectedPodcast.value = null
}

const deletePodcast = async (id: string) => {
  if (confirm('確定要刪除這個播客嗎？此操作無法復原。')) {
    await podcastStore.deletePodcast(id)
    if (selectedPodcast.value?.id === id) {
      selectedPodcast.value = null
    }
  }
}
</script>