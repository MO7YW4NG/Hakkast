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

      <!-- Search & Filter Bar -->
      <div class="flex flex-col md:flex-row md:items-center gap-4 mb-8">
        <input v-model="searchQuery" type="text" placeholder="搜尋標題、主題、內容..." class="input max-w-md" />
        <div class="flex flex-wrap gap-2">
          <button v-for="filter in filterOptions" :key="filter.value" @click="currentFilter = filter.value" :class="[
            'px-4 py-2 rounded-xl font-medium transition-all',
            currentFilter === filter.value ? 'bg-hakkast-gradient text-white shadow-lg' : 'bg-white text-hakkast-navy border border-gray-200 hover:border-hakkast-purple'
          ]">
            <span class="mr-2">{{ filter.emoji }}</span>{{ filter.label }}
          </button>
          <button v-for="lang in languageOptions" :key="lang.value" @click="currentLanguage = lang.value" :class="[
            'px-4 py-2 rounded-xl font-medium transition-all',
            currentLanguage === lang.value ? 'bg-hakkast-lavender text-white shadow-lg' : 'bg-white text-hakkast-lavender border border-gray-200 hover:border-hakkast-purple'
          ]">
            <span class="mr-2">🌐</span>{{ lang.label }}
          </button>
        </div>
        <div class="flex-1"></div>
        <div v-if="selectedIds.length > 0" class="flex gap-2">
          <button class="btn btn-gold" @click="batchDelete"><span class="mr-2">🗑️</span>批次刪除</button>
          <button class="btn btn-ghost" @click="showToast('批次分享功能尚未實作')"><span class="mr-2">📤</span>批次分享</button>
          <button class="btn btn-ghost" @click="showToast('批次下載功能尚未實作')"><span class="mr-2">⬇️</span>批次下載</button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredPodcasts.length === 0" class="text-center py-20">
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
      <motion.div :initial="{ opacity: 0, y: 40 }" :animate="{ opacity: 1, y: 0 }" :transition="{ duration: 0.5 }" v-if="filteredPodcasts.length > 0" class="space-y-8">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-2">
          <div class="text-gray-500 text-sm">共 {{ filteredPodcasts.length }} 筆</div>
          <div class="flex gap-2">
            <Checkbox v-model="selectAll" @update:modelValue="toggleSelectAll" label="全選" class="select-all" />
          </div>
        </div>
        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div v-for="podcast in filteredPodcasts" :key="podcast.id" class="group relative">
            <div class="card p-6 h-[18rem] flex flex-col overflow-hidden relative transition-all duration-300 hover:shadow-xl hover:-translate-y-0.5">
              <!-- Header -->
              <div class="flex items-start justify-between mb-4 flex-shrink-0">
                <div class="flex-1">
                  <div class="flex items-start gap-3">
                    <Checkbox 
                      :model-value="selectedIds.includes(podcast.id)"
                      @update:model-value="(checked) => {
                        if (checked) {
                          selectedIds.push(podcast.id)
                        } else {
                          const index = selectedIds.indexOf(podcast.id)
                          if (index > -1) selectedIds.splice(index, 1)
                        }
                      }"
                      class="card-checkbox mt-1"
                    />
                    <h3 class="text-lg font-semibold text-hakkast-navy line-clamp-2 break-words min-h-[3.5rem] mb-2 flex-1">
                      {{ podcast.title }}
                    </h3>
                  </div>
                  <div class="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                    <span>{{ formatDate(podcast.createdAt) }}</span>
                    <span>•</span>
                    <span class="capitalize">{{ getToneLabel(podcast.tone) }}</span>
                  </div>
                  <div class="flex flex-wrap gap-1 mt-1">
                    <span class="px-2 py-0.5 rounded bg-hakkast-gold text-hakkast-navy text-xs font-semibold">{{ getTopicLabel(podcast.topic) }}</span>
                    <span class="px-2 py-0.5 rounded bg-primary-600 text-white text-xs font-semibold">{{ getLanguageLabel(podcast.language) }}</span>
                    <span v-if="podcast.audioUrl" class="px-2 py-0.5 rounded bg-green-600/10 text-green-700 text-xs font-semibold">可播放</span>
                  </div>
                </div>
                <div class="ml-3 flex-shrink-0">
                  <div class="w-12 h-12 bg-hakkast-gradient rounded-xl flex items-center justify-center shadow-lg">
                    <span class="text-white text-lg">{{ getToneEmoji(podcast.tone) }}</span>
                  </div>
                </div>
              </div>
              <!-- Meta Info -->
              <div class="space-y-3 mb-6 flex-shrink-0">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">時長</span>
                  <span class="text-hakkast-purple font-medium">{{ podcast.duration }}分鐘</span>
                </div>
              </div>
              <!-- Actions -->
              <div class="flex space-x-3 mt-auto flex-shrink-0">
                <button @click="playPodcast(podcast)" class="btn btn-primary flex-1 text-sm"><span class="mr-2">▶️</span>播放</button>
                <button @click="deletePodcast(podcast.id)" class="btn btn-secondary text-sm px-4" title="刪除播客"><span>🗑️</span></button>
                <button class="btn btn-ghost text-sm px-4" title="分享播客" @click="showToast('分享功能尚未實作')"><span>📤</span></button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
    <!-- Enhanced Podcast Player Modal -->
    <div 
      v-if="selectedPodcast" 
      class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click="closePlayer"
    >
      <div 
        class="max-w-5xl w-full max-h-[90vh] overflow-y-auto"
        @click.stop
      >
        <PodcastPlayer :podcast="selectedPodcast" @close="closePlayer" />
      </div>
    </div>
    <!-- Toast -->
    <transition name="fade">
      <div v-if="toastMessage" class="fixed bottom-8 right-8 bg-hakkast-purple text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
        <span>✅</span>
        <span>{{ toastMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useMockPodcastStore } from '../stores/mockPodcastStore'
import PodcastPlayer from '../components/PodcastPlayer.vue'
import Checkbox from '../components/Checkbox.vue'
import { motion } from 'motion-v'
import type { Podcast } from '../types/podcast'

const podcastStore = useMockPodcastStore()

const podcasts = computed(() => podcastStore.podcasts)
const selectedPodcast = ref<Podcast | null>(null)
const currentFilter = ref('all')
const currentLanguage = ref('all')
const searchQuery = ref('')
const selectedIds = ref<string[]>([])
const selectAll = ref(false)
const toastMessage = ref('')

const filterOptions = [
  { value: 'all', label: '全部', emoji: '📂' },
  { value: 'casual', label: '輕鬆對話', emoji: '😊' },
  { value: 'educational', label: '教育知識', emoji: '📚' },
  { value: 'storytelling', label: '故事敘述', emoji: '📖' },
  { value: 'interview', label: '訪談對話', emoji: '🎤' }
]
const languageOptions = [
  { value: 'all', label: '全部語言' },
  { value: 'hakka', label: '純客語' },
  { value: 'bilingual', label: '客華雙語' }
]

const filteredPodcasts = computed(() => {
  let filtered = podcasts.value
  if (currentFilter.value !== 'all') {
    filtered = filtered.filter(podcast => podcast.tone === currentFilter.value)
  }
  if (currentLanguage.value !== 'all') {
    filtered = filtered.filter(podcast => podcast.language === currentLanguage.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    filtered = filtered.filter(podcast =>
      podcast.title.toLowerCase().includes(q) ||
      podcast.topic.toLowerCase().includes(q) ||
      (podcast.hakkaContent && podcast.hakkaContent.toLowerCase().includes(q)) ||
      (podcast.chineseContent && podcast.chineseContent.toLowerCase().includes(q))
    )
  }
  return filtered
})

function toggleSelectAll() {
  if (selectAll.value) {
    selectedIds.value = filteredPodcasts.value.map(p => p.id)
  } else {
    selectedIds.value = []
  }
}

function batchDelete() {
  if (selectedIds.value.length === 0) return
  if (confirm('確定要批次刪除選取的播客嗎？')) {
    selectedIds.value.forEach(id => podcastStore.deletePodcast(id))
    selectedIds.value = []
    selectAll.value = false
    showToast('已批次刪除')
  }
}

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 2000)
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

const getTopicLabel = (topic: string) => {
  const labels = {
    'research_deep_learning': '深度學習研究',
    'technology_news': '科技新聞',
    'finance_economics': '財經動態'
  }
  return labels[topic as keyof typeof labels] || topic
}

const getLanguageLabel = (language: string) => {
  const labels = {
    'hakka': '純客語',
    'bilingual': '客華雙語'
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
    showToast('已刪除')
  }
}

// 組件掛載時加載播客數據
onMounted(async () => {
  try {
    await podcastStore.fetchPodcasts()
  } catch (error) {
    console.error('Failed to fetch podcasts:', error)
    showToast('加載播客數據失敗')
  }
})
</script>