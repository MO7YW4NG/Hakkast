<template>
  <div v-if="podcast" class="card max-w-5xl mx-auto overflow-hidden">
    <!-- Header -->
    <div class="card-gradient p-8 text-white">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <div class="flex items-center space-x-3 mb-4">
            <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <span class="text-3xl">🎙️</span>
            </div>
            <div>
              <h3 class="text-2xl font-display font-bold mb-1">{{ podcast.title }}</h3>
              <div class="flex items-center space-x-4 text-white/80 text-sm">
                <span>{{ formatDate(podcast.createdAt) }}</span>
                <span>•</span>
                <span>{{ podcast.duration }}分鐘</span>
                <span>•</span>
                <span>{{ getToneLabel(podcast.tone) }}</span>
              </div>
            </div>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="p-2 hover:bg-white/20 rounded-xl transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Audio Player -->
      <div v-if="podcast.audioUrl" class="mt-6">
        <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
          <div class="flex items-center space-x-4 mb-4">
            <button 
              @click="togglePlay"
              class="w-12 h-12 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-colors"
            >
              <span class="text-2xl">{{ isPlaying ? '⏸️' : '▶️' }}</span>
            </button>
            <div class="flex-1">
              <div class="flex items-center justify-between text-sm text-white/80 mb-2">
                <span>正在播放</span>
                <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
              </div>
              <div class="h-2 bg-white/20 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-hakkast-gold transition-all duration-300"
                  :style="{ width: progressPercentage + '%' }"
                ></div>
              </div>
            </div>
          </div>
          
          <audio 
            ref="audioPlayer" 
            :src="podcast.audioUrl"
            @loadedmetadata="onLoadedMetadata"
            @timeupdate="onTimeUpdate"
            @ended="onEnded"
            class="hidden"
          ></audio>
          
          <div class="flex justify-between items-center">
            <div class="flex space-x-2">
              <button class="btn btn-gold btn-sm">
                <span class="mr-2">💾</span>
                下載
              </button>
              <button class="btn btn-ghost btn-sm">
                <span class="mr-2">📤</span>
                分享
              </button>
            </div>
            <div class="flex items-center space-x-3 text-white/60 text-sm">
              <span>🎵 高品質客語音檔</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Tabs -->
    <div class="bg-white">
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8 px-8">
          <button
            v-for="tab in contentTabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center space-x-2',
              activeTab === tab.id
                ? 'border-hakkast-purple text-hakkast-purple'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <span>{{ tab.emoji }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </nav>
      </div>
      
      <div class="p-8">
        <div class="max-h-96 overflow-y-auto">
          <div v-if="activeTab === 'hakka'" class="prose max-w-none">
            <div class="text-gray-700 whitespace-pre-wrap leading-relaxed text-lg">
              {{ podcast.hakkaContent }}
            </div>
          </div>
          <div v-if="activeTab === 'chinese'" class="prose max-w-none">
            <div class="text-gray-700 whitespace-pre-wrap leading-relaxed text-lg">
              {{ podcast.chineseContent }}
            </div>
          </div>
          <div v-if="activeTab === 'romanization' && podcast.romanization" class="prose max-w-none">
            <div class="text-gray-700 whitespace-pre-wrap leading-relaxed text-lg font-mono">
              {{ podcast.romanization }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="bg-gray-50 px-8 py-6 flex justify-between items-center">
      <div class="text-sm text-gray-500">
        <span class="font-medium">主題：</span>{{ podcast.topic }}
        <span class="mx-2">•</span>
        <span class="font-medium">語言：</span>{{ getLanguageLabel(podcast.language) }}
      </div>
      <div class="flex space-x-3">
        <button class="btn btn-secondary">
          <span class="mr-2">📋</span>
          複製內容
        </button>
        <button
          @click="$emit('close')"
          class="btn btn-primary"
        >
          <span class="mr-2">✨</span>
          關閉播放器
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Podcast } from '../types/podcast'

interface Props {
  podcast: Podcast | null
}

defineProps<Props>()
defineEmits<{
  close: []
}>()

const activeTab = ref('hakka')
const audioPlayer = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

const contentTabs = [
  { id: 'hakka', label: '客語內容', emoji: '🏮' },
  { id: 'chinese', label: '中文原稿', emoji: '📝' },
  { id: 'romanization', label: '羅馬拼音', emoji: '🔤' }
]

const progressPercentage = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const togglePlay = () => {
  if (!audioPlayer.value) return
  
  if (isPlaying.value) {
    audioPlayer.value.pause()
  } else {
    audioPlayer.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const onLoadedMetadata = () => {
  if (audioPlayer.value) {
    duration.value = audioPlayer.value.duration
  }
}

const onTimeUpdate = () => {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime
  }
}

const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
}

const formatTime = (seconds: number) => {
  if (isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getToneLabel = (tone: string) => {
  const labels = {
    'casual': '輕鬆對話',
    'educational': '教育知識',
    'storytelling': '故事敘述',
    'interview': '訪談對話'
  }
  return labels[tone as keyof typeof labels] || tone
}

const getLanguageLabel = (language: string) => {
  const labels = {
    'hakka': '純客語',
    'mixed': '客華混合',
    'bilingual': '雙語模式'
  }
  return labels[language as keyof typeof labels] || language
}

onMounted(() => {
  // Add keyboard event listener for ESC key
  const handleEscape = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      // Emit close event
    }
  }
  document.addEventListener('keydown', handleEscape)
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleEscape)
    if (audioPlayer.value) {
      audioPlayer.value.pause()
    }
  })
})
</script>