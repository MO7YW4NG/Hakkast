<template>
  <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200" v-motion="{ initial: { opacity: 0, y: 20 }, enter: { opacity: 1, y: 0 }, leave: { opacity: 0, y: 20 } }">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
          <span class="text-xl">🌐</span>
        </div>
      </div>
      
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-blue-900">智能內容爬取</h3>
          <span 
            :class="[
              'px-2 py-1 text-xs rounded-full font-medium',
              isEnabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            ]"
          >
            {{ isEnabled ? '已啟用' : '未啟用' }}
          </span>
        </div>
        
        <p class="text-sm text-blue-800 mb-3">
          自動搜集最新相關內容，提升播客時效性和豐富度
        </p>
        
        <div v-if="isEnabled && crawlerInfo" class="space-y-2">
          <div class="text-xs text-blue-700">
            <span class="font-medium">支援主題：</span>
            <span>{{ crawlerInfo.totalTopics }}個</span>
            <span class="mx-2">•</span>
            <span class="font-medium">資料源：</span>
            <span>{{ crawlerInfo.totalSources }}個</span>
          </div>
          
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="topic in displayTopics" 
              :key="topic"
              class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
            >
              {{ getTopicLabel(topic) }}
            </span>
            <span 
              v-if="crawlerInfo.topics && Object.keys(crawlerInfo.topics).length > 6"
              class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
            >
              +{{ Object.keys(crawlerInfo.topics).length - 6 }}個主題
            </span>
          </div>
        </div>
        
        <div v-if="!isEnabled" class="text-xs text-blue-700">
          主題包含動態關鍵字時自動啟用
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface CrawlerStats {
  totalTopics: number
  totalSources: number
  topics: Record<string, any>
}

interface Props {
  topic?: string
}

const props = defineProps<Props>()

const crawlerInfo = ref<CrawlerStats | null>(null)

const isEnabled = computed(() => {
  if (!props.topic) return false
  
  const dynamicKeywords = [
    'news', 'latest', 'recent', 'current', 'update', 'research', 
    'gaming', 'technology', 'science', 'politics', 'economics',
    '新聞', '最新', '研究', '遊戲', '科技', '健康', '環境', '財經'
  ]
  
  const topicLower = props.topic.toLowerCase()
  return dynamicKeywords.some(keyword => topicLower.includes(keyword))
})

const displayTopics = computed(() => {
  if (!crawlerInfo.value?.topics) return []
  return Object.keys(crawlerInfo.value.topics).slice(0, 6)
})

const topicLabels: Record<string, string> = {
  'gaming_news': '遊戲新聞',
  'research_deep_learning': '深度學習',
  'technology_news': '科技新聞',
  'health_wellness': '健康養生',
  'climate_environment': '氣候環境',
  'finance_economics': '財經動態'
}

const getTopicLabel = (topic: string) => {
  return topicLabels[topic] || topic.replace('_', ' ')
}

const fetchCrawlerStats = async () => {
  try {
    const response = await fetch('/api/crawler/stats')
    if (response.ok) {
      crawlerInfo.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch crawler stats:', error)
  }
}

onMounted(() => {
  fetchCrawlerStats()
})
</script>