<template>
  <div class="min-h-screen py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-12">
        <div class="inline-flex items-center space-x-2 bg-hakkast-gold/10 rounded-full px-4 py-2 mb-4">
          <span class="text-2xl">✨</span>
          <span class="text-sm font-medium text-hakkast-navy">AI播客創作工作室</span>
        </div>
        <h1 class="text-4xl lg:text-5xl font-display font-bold text-hakkast-navy mb-4">
          打造您的專屬<span class="text-gradient">客語播客</span>
        </h1>
        <p class="text-xl text-gray-600 max-w-2xl mx-auto">
          透過三步AI流程，將您的想法轉化為專業的客語播客內容
        </p>
      </div>

      <div class="grid lg:grid-cols-2 gap-12 items-start">
        <!-- Form Section -->
        <div class="space-y-8">
          <form @submit.prevent="generatePodcast" class="space-y-6">
            <!-- Topic Input -->
            <div class="card p-6">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-10 h-10 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                  <span class="text-white text-lg">💡</span>
                </div>
                <div>
                  <h3 class="font-semibold text-hakkast-navy">播客主題</h3>
                  <p class="text-sm text-gray-500">選擇您想要探討的話題</p>
                </div>
              </div>
              <input
                id="topic"
                v-model="form.topic"
                type="text"
                placeholder="例如：客家美食文化、遊戲最新消息、深度學習研究、科技新聞..."
                class="input input-large"
                required
              />
              <CrawlerStatus :topic="form.topic" />
            </div>

            <!-- Tone Selection -->
            <div class="card p-6">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-10 h-10 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                  <span class="text-white text-lg">🎭</span>
                </div>
                <div>
                  <h3 class="font-semibold text-hakkast-navy">語調風格</h3>
                  <p class="text-sm text-gray-500">選擇播客的呈現方式</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <label 
                  v-for="option in toneOptions" 
                  :key="option.value"
                  class="flex items-center p-4 border-2 rounded-xl cursor-pointer transition-all duration-200"
                  :class="form.tone === option.value ? 'border-hakkast-purple bg-hakkast-purple/5' : 'border-gray-200 hover:border-hakkast-purple/30'"
                >
                  <input 
                    type="radio" 
                    v-model="form.tone" 
                    :value="option.value"
                    class="sr-only"
                  />
                  <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-1">
                      <span class="text-lg">{{ option.emoji }}</span>
                      <span class="font-medium text-gray-900">{{ option.label }}</span>
                    </div>
                    <p class="text-sm text-gray-500">{{ option.description }}</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Duration & Language -->
            <div class="grid md:grid-cols-2 gap-6">
              <div class="card p-6">
                <div class="flex items-center space-x-3 mb-4">
                  <div class="w-10 h-10 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                    <span class="text-white text-lg">⏱️</span>
                  </div>
                  <div>
                    <h3 class="font-semibold text-hakkast-navy">播客時長</h3>
                    <p class="text-sm text-gray-500">選擇適合的長度</p>
                  </div>
                </div>
                <select v-model="form.duration" class="input">
                  <option :value="5">5分鐘 - 簡短介紹</option>
                  <option :value="10">10分鐘 - 標準長度</option>
                  <option :value="15">15分鐘 - 詳細討論</option>
                  <option :value="20">20分鐘 - 深度探討</option>
                  <option :value="30">30分鐘 - 完整分析</option>
                </select>
              </div>

              <div class="card p-6">
                <div class="flex items-center space-x-3 mb-4">
                  <div class="w-10 h-10 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                    <span class="text-white text-lg">🌐</span>
                  </div>
                  <div>
                    <h3 class="font-semibold text-hakkast-navy">語言組合</h3>
                    <p class="text-sm text-gray-500">選擇語言模式</p>
                  </div>
                </div>
                <select v-model="form.language" class="input">
                  <option value="hakka">純客語</option>
                  <option value="mixed">客華混合</option>
                  <option value="bilingual">雙語模式</option>
                </select>
              </div>
            </div>

            <!-- Personal Interests -->
            <div class="card p-6">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-10 h-10 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                  <span class="text-white text-lg">❤️</span>
                </div>
                <div>
                  <h3 class="font-semibold text-hakkast-navy">個人興趣 <span class="text-gray-400 font-normal">(選填)</span></h3>
                  <p class="text-sm text-gray-500">讓AI更了解您的喜好，創造個人化內容</p>
                </div>
              </div>
              <textarea
                v-model="form.interests"
                rows="4"
                placeholder="分享您對客家文化的興趣點，例如：喜歡傳統音樂、對古建築有研究、熱愛客家料理..."
                class="input resize-none"
              ></textarea>
            </div>

            <!-- Generate Button -->
            <button
              type="submit"
              :disabled="isGenerating || !form.topic"
              class="w-full btn btn-primary text-xl py-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="!isGenerating" class="flex items-center justify-center space-x-2">
                <span>🚀</span>
                <span>開始生成播客</span>
              </span>
              <span v-else class="flex items-center justify-center space-x-2">
                <span class="loading-dots">正在創作中</span>
              </span>
            </button>
          </form>
        </div>

        <!-- Preview/Result Section -->
        <div class="space-y-6">
          <!-- Process Steps -->
          <div v-if="!generatedPodcast" class="card p-6">
            <h3 class="text-xl font-semibold text-hakkast-navy mb-6">AI創作流程</h3>
            <div class="space-y-4">
              <div v-for="(step, index) in processSteps" :key="index" class="flex items-center space-x-4">
                <div class="w-10 h-10 rounded-full flex items-center justify-center" 
                     :class="step.completed ? 'bg-hakkast-gradient text-white' : 'bg-gray-100 text-gray-400'">
                  <span>{{ index + 1 }}</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-medium" :class="step.completed ? 'text-hakkast-navy' : 'text-gray-400'">
                    {{ step.title }}
                  </h4>
                  <p class="text-sm text-gray-500">{{ step.description }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Generated Content -->
          <div v-if="generatedPodcast" class="space-y-6 animate-slide-up">
            <!-- Audio Player Card -->
            <div class="card-gradient p-6 text-white">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <span class="text-2xl">🎙️</span>
                </div>
                <div>
                  <h3 class="text-xl font-semibold">{{ generatedPodcast.title }}</h3>
                  <p class="text-white/80">AI播客 • {{ generatedPodcast.duration || form.duration }}分鐘</p>
                </div>
              </div>
              
              <div v-if="generatedPodcast.audioUrl" class="mb-4">
                <audio controls class="w-full">
                  <source :src="generatedPodcast.audioUrl" type="audio/wav">
                  您的瀏覽器不支援音頻播放。
                </audio>
              </div>
              
              <div class="flex space-x-3">
                <button class="btn btn-gold">
                  <span class="mr-2">💾</span>
                  儲存至庫存
                </button>
                <button class="btn btn-ghost">
                  <span class="mr-2">📤</span>
                  分享
                </button>
              </div>
            </div>

            <!-- Content Tabs -->
            <div class="card overflow-hidden">
              <div class="border-b border-gray-200">
                <nav class="flex space-x-8 px-6">
                  <button
                    v-for="tab in contentTabs"
                    :key="tab.id"
                    @click="activeTab = tab.id"
                    :class="[
                      'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                      activeTab === tab.id
                        ? 'border-hakkast-purple text-hakkast-purple'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    ]"
                  >
                    <span class="mr-2">{{ tab.emoji }}</span>
                    {{ tab.label }}
                  </button>
                </nav>
              </div>
              
              <div class="p-6">
                <div v-if="activeTab === 'hakka'" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 leading-relaxed">{{ generatedPodcast.hakkaContent }}</div>
                </div>
                <div v-if="activeTab === 'chinese'" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 leading-relaxed">{{ generatedPodcast.chineseContent }}</div>
                </div>
                <div v-if="activeTab === 'romanization' && generatedPodcast.romanization" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 font-mono leading-relaxed">{{ generatedPodcast.romanization }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { usePodcastStore } from '../stores/podcast'
import CrawlerStatus from '../components/CrawlerStatus.vue'

const podcastStore = usePodcastStore()

const isGenerating = ref(false)
const generatedPodcast = ref(null)
const activeTab = ref('hakka')

const form = reactive({
  topic: '',
  tone: 'casual',
  duration: 10,
  language: 'mixed',
  interests: ''
})

const toneOptions = [
  {
    value: 'casual',
    label: '輕鬆對話',
    description: '友善親切的聊天風格',
    emoji: '😊'
  },
  {
    value: 'educational',
    label: '教育知識',
    description: '專業詳細的說明方式',
    emoji: '📚'
  },
  {
    value: 'storytelling',
    label: '故事敘述',
    description: '生動有趣的故事講述',
    emoji: '📖'
  },
  {
    value: 'interview',
    label: '訪談對話',
    description: '問答式深入討論',
    emoji: '🎤'
  }
]

const contentTabs = [
  { id: 'hakka', label: '客語內容', emoji: '🏮' },
  { id: 'chinese', label: '中文原稿', emoji: '📝' },
  { id: 'romanization', label: '羅馬拼音', emoji: '🔤' }
]

const processSteps = ref([
  {
    title: '內容爬取',
    description: '搜集最新相關資訊 (如適用)',
    completed: false,
    optional: true
  },
  {
    title: 'AI內容生成',
    description: '使用Gemini AI產生中文播客腳本',
    completed: false
  },
  {
    title: '客語翻譯',
    description: '專業API將中文翻譯為客語',
    completed: false
  },
  {
    title: '語音合成',
    description: '生成高品質客語語音檔案',
    completed: false
  }
])

const generatePodcast = async () => {
  isGenerating.value = true
  activeTab.value = 'hakka'
  
  // Reset process steps
  processSteps.value.forEach(step => step.completed = false)
  
  try {
    // Simulate step progress
    processSteps.value[0].completed = true // Content crawling
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    processSteps.value[1].completed = true // AI content generation
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    processSteps.value[2].completed = true // Hakka translation
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    processSteps.value[3].completed = true // TTS synthesis
    
    const result = await podcastStore.generatePodcast(form)
    generatedPodcast.value = result
  } catch (error) {
    console.error('Failed to generate podcast:', error)
    // Reset steps on error
    processSteps.value.forEach(step => step.completed = false)
  } finally {
    isGenerating.value = false
  }
}
</script>