<template>
  <div class="min-h-screen py-12 bg-gradient-to-br from-white to-hakkast-gold/10">
    <!-- Sticky Progress Bar under navbar -->
    <div class="fixed top-20 left-0 right-0 z-40 bg-white/80 backdrop-blur-lg shadow-xl border-b border-gray-200/20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-3">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-base font-semibold text-hakkast-navy flex items-center gap-2">
              <span class="text-xl">⚡</span> AI 創作流程
            </h3>
            <div class="text-xs text-gray-500 bg-gray-100/80 backdrop-blur-sm px-2 py-1 rounded-full">
              {{ processSteps.filter(s => s.completed).length }}/{{ processSteps.length }} 步驟完成
            </div>
          </div>
          <div class="w-full h-2.5 bg-gray-100/60 rounded-full overflow-hidden backdrop-blur-sm">
            <div 
              class="h-full bg-hakkast-gradient transition-all duration-700 ease-out" 
              :style="{ width: getProgressWidth() + '%' }"
            ></div>
          </div>
          <div class="flex justify-between mt-2 text-xs text-gray-500">
            <span class="transition-colors px-1 text-hakkast-purple font-medium">內容爬取</span>
            <span class="transition-colors px-1" :class="processSteps[0].completed ? 'text-hakkast-purple font-medium' : ''">AI內容生成</span>
            <span class="transition-colors px-1" :class="processSteps[1].completed ? 'text-hakkast-purple font-medium' : ''">客語翻譯</span>
            <span class="transition-colors px-1" :class="processSteps[2].completed ? 'text-hakkast-purple font-medium' : ''">語音合成</span>
            <span class="transition-colors px-1" :class="processSteps[3].completed ? 'text-hakkast-purple font-medium' : ''">完成</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add top padding to account for sticky progress bar -->
    <div class="pt-28">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row gap-10">
        <!-- Left: Form -->
        <div class="flex flex-col gap-8 w-full lg:w-1/2">
          <!-- Form Card -->
          <div class="bg-white rounded-2xl shadow-xl p-8">
            <h2 class="text-2xl font-bold text-hakkast-navy mb-6 flex items-center gap-2">
              <span class="text-2xl">✨</span> 生成專屬播客
            </h2>
            <!-- Hot Topics Chips -->
            <div class="mb-4">
              <div class="mb-2 text-sm text-hakkast-navy font-medium">熱門主題</div>
              <div class="flex flex-wrap gap-2">
                <button v-for="topic in hotTopics" :key="topic" type="button" @click="form.topic = topic" class="px-3 py-1 rounded-full bg-hakkast-purple/10 text-hakkast-purple hover:bg-hakkast-purple/20 transition">
                  {{ topic }}
                </button>
              </div>
            </div>
            <form @submit.prevent="generatePodcast" class="space-y-6">
              <!-- Topic -->
              <div>
                <label class="block text-sm font-medium text-hakkast-navy mb-2">播客主題</label>
                <input
                  id="topic"
                  v-model="form.topic"
                  type="text"
                  placeholder="例如：客家美食文化、遊戲最新消息..."
                  class="input input-large"
                  required
                />
                <CrawlerStatus :topic="form.topic" class="mt-2" />
              </div>
              <!-- Tone & Duration -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-hakkast-navy mb-2">語調風格</label>
                  <select v-model="form.tone" class="input">
                    <option v-for="option in toneOptions" :key="option.value" :value="option.value">
                      {{ option.emoji }} {{ option.label }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-hakkast-navy mb-2">播客時長</label>
                  <select v-model="form.duration" class="input">
                    <option :value="5">5分鐘 - 簡短介紹</option>
                    <option :value="10">10分鐘 - 標準長度</option>
                    <option :value="15">15分鐘 - 詳細討論</option>
                    <option :value="20">20分鐘 - 深度探討</option>
                    <option :value="30">30分鐘 - 完整分析</option>
                  </select>
                </div>
              </div>
              <!-- Language -->
              <div>
                <label class="block text-sm font-medium text-hakkast-navy mb-2">語言組合</label>
                <select v-model="form.language" class="input">
                  <option value="hakka">純客語</option>
                  <option value="bilingual">客華雙語</option>
                </select>
              </div>
              <!-- Interests as Chips -->
              <div>
                <label class="block text-sm font-medium text-hakkast-navy mb-2">個人興趣 <span class="text-gray-400 font-normal">(可多選)</span></label>
                <div class="flex flex-wrap gap-2 mb-2">
                  <span v-for="(interest, i) in form.interests" :key="interest" class="px-3 py-1 rounded-full bg-hakkast-gold/10 text-hakkast-navy flex items-center gap-1">
                    {{ interest }}
                    <button type="button" @click="removeInterest(i)" class="ml-1 text-hakkast-purple hover:text-red-500">×</button>
                  </span>
                </div>
                <input
                  v-model="interestInput"
                  @keydown.enter.prevent="addInterest"
                  type="text"
                  placeholder="輸入興趣並按 Enter..."
                  class="input"
                />
              </div>
              <!-- Generate Button -->
              <button
                type="submit"
                :disabled="isGenerating || !form.topic"
                class="w-full btn btn-primary text-xl py-4 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
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
        </div>
        
        <!-- Right: Result/Preview -->
        <div class="flex-1 flex flex-col gap-8 w-full lg:w-1/2 mt-10 lg:mt-0">
          <div v-if="generatedPodcast" class="bg-white rounded-2xl shadow-2xl p-8 animate-slide-up">
            <div class="text-center mb-6">
              <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span class="text-3xl text-green-600">🎉</span>
              </div>
              <h3 class="text-xl font-bold text-hakkast-navy mb-2">播客生成成功！</h3>
              <p class="text-gray-600">您的客語播客已準備就緒</p>
            </div>
            
            <div class="flex items-center gap-4 mb-6">
              <div class="w-14 h-14 bg-hakkast-gradient rounded-xl flex items-center justify-center">
                <span class="text-3xl">🎙️</span>
              </div>
              <div>
                <h3 class="text-2xl font-bold text-hakkast-navy mb-1">{{ generatedPodcast?.title }}</h3>
                <div class="text-gray-500 text-sm">AI播客 • {{ generatedPodcast?.duration || form.duration }}分鐘</div>
              </div>
            </div>
            
            <!-- Podcast Info -->
            <div class="bg-hakkast-purple/5 rounded-xl p-4 mb-6">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="font-medium text-gray-700">語調風格：</span>
                  <span class="text-hakkast-purple">{{ getToneLabel(generatedPodcast.tone) }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700">語言組合：</span>
                  <span class="text-hakkast-purple">{{ getLanguageLabel(generatedPodcast.language) }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700">主題：</span>
                  <span class="text-hakkast-purple">{{ generatedPodcast.topic }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700">時長：</span>
                  <span class="text-hakkast-purple">{{ generatedPodcast.duration }}分鐘</span>
                </div>
              </div>
            </div>
            
            <div v-if="generatedPodcast?.audioUrl" class="mb-6">
              <audio controls class="w-full">
                <source :src="generatedPodcast?.audioUrl" type="audio/wav">
                您的瀏覽器不支援音頻播放。
              </audio>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex flex-col gap-3 mb-6">
              <router-link to="/library" class="btn btn-primary text-center">
                <span class="mr-2">📚</span>
                查看庫存
              </router-link>
              <button @click="generateAnother" class="btn btn-secondary text-center">
                <span class="mr-2">✨</span>
                生成另一個播客
              </button>
            </div>
            <!-- Tabs -->
            <!-- <div class="mt-6">
              <div class="flex space-x-4 border-b border-gray-200 mb-4">
                <button
                  v-for="tab in contentTabs"
                  :key="tab.id"
                  @click="activeTab = tab.id"
                  :class="[
                    'py-2 px-4 font-medium text-sm rounded-t-lg',
                    activeTab === tab.id
                      ? 'bg-hakkast-purple/10 border-b-2 border-hakkast-purple text-hakkast-purple shadow'
                      : 'text-gray-500 hover:text-hakkast-purple'
                  ]"
                >
                  <span class="mr-2">{{ tab.emoji }}</span>{{ tab.label }}
                </button>
              </div> -->
              <!-- <div class="p-2">
                <div v-if="activeTab === 'hakka'" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 leading-relaxed">{{ generatedPodcast?.hakkaContent }}</div>
                </div>
                <div v-if="activeTab === 'chinese'" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 leading-relaxed">{{ generatedPodcast?.chineseContent }}</div>
                </div>
                <div v-if="activeTab === 'romanization' && generatedPodcast?.romanization" class="prose max-w-none">
                  <div class="whitespace-pre-wrap text-gray-700 font-mono leading-relaxed">{{ generatedPodcast?.romanization }}</div>
                </div>
              </div> -->
            <!-- </div> -->
          </div>
          <div v-else class="flex flex-col items-center justify-center h-full min-h-[400px]">
            <div class="w-24 h-24 bg-hakkast-gradient rounded-2xl flex items-center justify-center mb-6 shadow-xl">
              <span class="text-5xl">✨</span>
            </div>
            <h3 class="text-2xl font-bold text-hakkast-navy mb-2">AI播客生成預覽</h3>
            <p class="text-gray-500 mb-4">請填寫左側表單並點擊「開始生成播客」</p>
          </div>
          <!-- Toast -->
          <transition name="fade">
            <div v-if="toastMessage" class="fixed bottom-8 right-8 bg-hakkast-purple text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
              <span>✅</span>
              <span>{{ toastMessage }}</span>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-dots {
  display: inline-block;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { content: ''; }
  40% { content: '.'; }
  60% { content: '..'; }
  80%, 100% { content: '...'; }
}

.animate-slide-up {
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMockPodcastStore } from '../stores/mockPodcastStore'
import { mockTopicConfigs } from '../mock/mockData'
import CrawlerStatus from '../components/CrawlerStatus.vue'
import type { Podcast, PodcastGenerationRequest } from '../types/podcast'

const podcastStore = useMockPodcastStore()

const isGenerating = ref(false)
const generatedPodcast = ref<Podcast | null>(null)
const activeTab = ref('hakka')

const hotTopics = mockTopicConfigs.map(topic => topic.label)

const form = reactive({
  topic: '',
  tone: 'casual',
  duration: 10,
  language: 'hakka',
  interests: [] as string[],
})
const interestInput = ref('')

function addInterest() {
  const val = interestInput.value.trim()
  if (val && !form.interests.includes(val)) {
    form.interests.push(val)
  }
  interestInput.value = ''
}
function removeInterest(idx: number) {
  form.interests.splice(idx, 1)
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
    'bilingual': '客華雙語'
  }
  return labels[language as keyof typeof labels] || language
}

const getProgressWidth = () => {
  const completedCount = processSteps.value.filter(s => s.completed).length
  if (completedCount === 0) return 0
  if (completedCount === 1) return 25
  if (completedCount === 2) return 50
  if (completedCount === 3) return 75
  return 100
}

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

// const contentTabs = [
//   { id: 'hakka', label: '客語內容', emoji: '🏮' },
//   { id: 'chinese', label: '中文原稿', emoji: '📝' },
//   { id: 'romanization', label: '羅馬拼音', emoji: '🔤' }
// ]

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

const toastMessage = ref('')
function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 2000)
}

const generatePodcast = async () => {
  isGenerating.value = true
  activeTab.value = 'hakka'
  toastMessage.value = ''
  // Reset process steps
  processSteps.value.forEach(step => step.completed = false)
  
  try {
    // 使用mock store的生成狀態
    podcastStore.resetGenerationStatus()
    
    const payload = {
      ...form,
      interests: form.interests.join(',')
    }
    
    // Simulate realistic step-by-step progress
    const stepTimeouts = [
      () => new Promise(resolve => setTimeout(() => {
        processSteps.value[0].completed = true
        resolve(true)
      }, 1500)), // Content crawling: 1.5s
      () => new Promise(resolve => setTimeout(() => {
        processSteps.value[1].completed = true
        resolve(true)
      }, 1500)), // AI content generation: 1.5s
      () => new Promise(resolve => setTimeout(() => {
        processSteps.value[2].completed = true
        resolve(true)
      }, 1500)), // Hakka translation: 1.5s
      () => new Promise(resolve => setTimeout(() => {
        processSteps.value[3].completed = true
        resolve(true)
      }, 1000))  // Voice synthesis: 1s
    ]
    
    // Execute steps sequentially
    for (let i = 0; i < stepTimeouts.length; i++) {
      await stepTimeouts[i]()
    }
    
    const result = await podcastStore.generatePodcast(payload as PodcastGenerationRequest)
    generatedPodcast.value = result
    
    // Complete all steps
    processSteps.value.forEach(step => step.completed = true)
    
    showToast('Podcast生成成功！')
    
  } catch (error) {
    console.error('Failed to generate podcast:', error)
    // Reset steps on error
    processSteps.value.forEach(step => step.completed = false)
    showToast('生成失敗，請稍後再試')
  } finally {
    isGenerating.value = false
  }
}

const generateAnother = () => {
  generatedPodcast.value = null
  activeTab.value = 'hakka'
  // Reset form
  form.topic = ''
  form.tone = 'casual'
  form.duration = 10
  form.language = 'hakka'
  form.interests = []
  // Reset process steps
  processSteps.value.forEach(step => step.completed = false)
}

// 初始化數據
onMounted(async () => {
  try {
    await podcastStore.fetchPodcasts()
  } catch (error) {
    console.error('Failed to fetch podcasts:', error)
  }
})
</script>