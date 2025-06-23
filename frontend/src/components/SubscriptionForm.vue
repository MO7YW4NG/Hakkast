<template>
  <div class="card max-w-2xl mx-auto">
    <div class="card-gradient p-8 text-white text-center">
      <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <span class="text-3xl">📧</span>
      </div>
      <h2 class="text-3xl font-display font-bold mb-2">訂閱客語播客</h2>
      <p class="text-white/80 text-lg">每日或每週收到個人化的客語播客內容</p>
    </div>

    <form @submit.prevent="handleSubmit" class="p-8 space-y-6">
      <!-- Email Input -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          <span class="mr-2">✉️</span>電子郵件
        </label>
        <input
          v-model="form.email"
          type="email"
          required
          class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-hakkast-purple focus:border-transparent transition-colors"
          placeholder="your@email.com"
        />
      </div>

      <!-- Frequency Selection -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-3">
          <span class="mr-2">📅</span>訂閱頻率
        </label>
        <div class="grid grid-cols-2 gap-3">
          <button
            type="button"
            @click="form.frequency = 'daily'"
            :class="[
              'p-4 rounded-xl border-2 transition-all text-left',
              form.frequency === 'daily'
                ? 'border-hakkast-purple bg-hakkast-purple/10 text-hakkast-purple'
                : 'border-gray-200 hover:border-gray-300'
            ]"
          >
            <div class="font-semibold">每日播客</div>
            <div class="text-sm text-gray-500">每天早上收到新內容</div>
          </button>
          <button
            type="button"
            @click="form.frequency = 'weekly'"
            :class="[
              'p-4 rounded-xl border-2 transition-all text-left',
              form.frequency === 'weekly'
                ? 'border-hakkast-purple bg-hakkast-purple/10 text-hakkast-purple'
                : 'border-gray-200 hover:border-gray-300'
            ]"
          >
            <div class="font-semibold">每週播客</div>
            <div class="text-sm text-gray-500">每週精選內容合集</div>
          </button>
        </div>
      </div>

      <!-- Topics Selection -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-3">
          <span class="mr-2">🏷️</span>感興趣的主題（可多選）
        </label>
        
        <!-- Traditional Topics -->
        <div class="mb-4">
          <h4 class="text-sm font-medium text-gray-600 mb-2 flex items-center">
            <span class="mr-2">🏮</span>傳統客家主題
          </h4>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="topic in availableTopics.filter(t => t.category === 'traditional')"
              :key="topic.value"
              type="button"
              @click="toggleTopic(topic.value)"
              :class="[
                'p-3 rounded-lg border transition-all text-sm text-left',
                form.topics.includes(topic.value)
                  ? 'border-hakkast-purple bg-hakkast-purple/10 text-hakkast-purple'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <span class="mr-2">{{ topic.emoji }}</span>{{ topic.label }}
            </button>
          </div>
        </div>
        
        <!-- Dynamic Topics with Web Crawling -->
        <div class="mb-4">
          <h4 class="text-sm font-medium text-gray-600 mb-2 flex items-center">
            <span class="mr-2">🌐</span>動態最新內容 
            <span class="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">自動爬取最新資訊</span>
          </h4>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="topic in availableTopics.filter(t => t.category === 'dynamic')"
              :key="topic.value"
              type="button"
              @click="toggleTopic(topic.value)"
              :class="[
                'p-3 rounded-lg border transition-all text-sm text-left relative',
                form.topics.includes(topic.value)
                  ? 'border-hakkast-purple bg-hakkast-purple/10 text-hakkast-purple'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div class="flex items-center justify-between">
                <div>
                  <span class="mr-2">{{ topic.emoji }}</span>{{ topic.label }}
                </div>
                <span 
                  v-if="topic.badge"
                  :class="[
                    'px-2 py-1 text-xs rounded-full',
                    topic.badge === '研究' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-orange-100 text-orange-800'
                  ]"
                >
                  {{ topic.badge }}
                </span>
              </div>
            </button>
          </div>
        </div>
        
        <!-- Info about dynamic content -->
        <div class="bg-blue-50 rounded-lg p-3 text-sm text-blue-800">
          <div class="flex items-start space-x-2">
            <span class="text-base">ℹ️</span>
            <div>
              <div class="font-medium mb-1">智能內容爬取</div>
              <div class="text-blue-700">選擇動態主題時，系統會自動爬取相關網站的最新內容，結合客家文化視角為您創作播客。</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Language & Tone -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">語言模式</label>
          <select
            v-model="form.language"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hakkast-purple focus:border-transparent"
          >
            <option value="hakka">純客語</option>
            <option value="mixed">客華混合</option>
            <option value="bilingual">雙語模式</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">播客風格</label>
          <select
            v-model="form.tone"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hakkast-purple focus:border-transparent"
          >
            <option value="casual">輕鬆對話</option>
            <option value="educational">教育知識</option>
            <option value="storytelling">故事敘述</option>
            <option value="interview">訪談對話</option>
          </select>
        </div>
      </div>

      <!-- Delivery Preferences -->
      <div class="border-t pt-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">配送設定</h3>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">配送時間</label>
              <input
                v-model="form.preferences.deliveryTime"
                type="time"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hakkast-purple focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">播客長度（分鐘）</label>
              <select
                v-model="form.preferences.maxDuration"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-hakkast-purple focus:border-transparent"
              >
                <option :value="5">5分鐘</option>
                <option :value="10">10分鐘</option>
                <option :value="15">15分鐘</option>
                <option :value="30">30分鐘</option>
              </select>
            </div>
          </div>

          <!-- Weekly Days (only show for weekly subscription) -->
          <div v-if="form.frequency === 'weekly'">
            <label class="block text-sm font-medium text-gray-700 mb-2">配送日期</label>
            <div class="flex space-x-2">
              <button
                v-for="(day, index) in weekDays"
                :key="index"
                type="button"
                @click="toggleDeliveryDay(index)"
                :class="[
                  'w-10 h-10 rounded-full text-sm font-medium transition-all',
                  form.preferences.deliveryDays?.includes(index)
                    ? 'bg-hakkast-purple text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                ]"
              >
                {{ day }}
              </button>
            </div>
          </div>

          <!-- Additional Options -->
          <div class="space-y-3">
            <label class="flex items-center">
              <input
                v-model="form.preferences.includeTranscript"
                type="checkbox"
                class="rounded border-gray-300 text-hakkast-purple focus:ring-hakkast-purple"
              />
              <span class="ml-2 text-sm text-gray-700">包含完整文字稿</span>
            </label>
            <label class="flex items-center">
              <input
                v-model="form.preferences.includeRomanization"
                type="checkbox"
                class="rounded border-gray-300 text-hakkast-purple focus:ring-hakkast-purple"
              />
              <span class="ml-2 text-sm text-gray-700">包含羅馬拼音</span>
            </label>
            <label class="flex items-center">
              <input
                v-model="form.preferences.notificationEmail"
                type="checkbox"
                class="rounded border-gray-300 text-hakkast-purple focus:ring-hakkast-purple"
              />
              <span class="ml-2 text-sm text-gray-700">接收郵件通知</span>
            </label>
          </div>
        </div>
      </div>

      <!-- RSS Info -->
      <div class="bg-hakkast-navy/5 rounded-xl p-4">
        <div class="flex items-start space-x-3">
          <span class="text-2xl">📡</span>
          <div>
            <h4 class="font-semibold text-gray-900 mb-1">RSS訂閱</h4>
            <p class="text-sm text-gray-600 mb-2">訂閱後可獲得個人RSS連結，在任何播客應用程式中收聽</p>
            <div class="text-xs text-gray-500">支援 Apple Podcasts、Spotify、Google Podcasts 等</div>
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        :disabled="isLoading || !isFormValid"
        class="w-full btn btn-primary py-4 text-lg"
      >
        <span v-if="isLoading" class="mr-2">⏳</span>
        <span v-else class="mr-2">🎙️</span>
        {{ isLoading ? '訂閱中...' : '開始訂閱' }}
      </button>

      <!-- Terms -->
      <p class="text-xs text-gray-500 text-center">
        訂閱即表示同意我們的
        <a href="#" class="text-hakkast-purple hover:underline">服務條款</a>
        和
        <a href="#" class="text-hakkast-purple hover:underline">隱私政策</a>
      </p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SubscriptionRequest } from '../types/subscription'

interface Props {
  onSubscribe?: (subscription: SubscriptionRequest) => Promise<void>
}

const props = defineProps<Props>()

const isLoading = ref(false)

const form = ref<SubscriptionRequest>({
  email: '',
  frequency: 'daily',
  topics: [],
  language: 'hakka',
  tone: 'casual',
  preferences: {
    deliveryTime: '08:00',
    deliveryDays: [1], // Monday for weekly
    maxDuration: 10,
    includeTranscript: true,
    includeRomanization: false,
    notificationEmail: true
  }
})

const availableTopics = [
  // Traditional Hakka topics
  { value: 'culture', label: '客家文化', emoji: '🏮', category: 'traditional' },
  { value: 'history', label: '歷史故事', emoji: '📚', category: 'traditional' },
  { value: 'food', label: '客家美食', emoji: '🍜', category: 'traditional' },
  { value: 'music', label: '客家音樂', emoji: '🎵', category: 'traditional' },
  { value: 'language', label: '語言學習', emoji: '📖', category: 'traditional' },
  { value: 'festival', label: '節慶習俗', emoji: '🎊', category: 'traditional' },
  { value: 'nature', label: '自然環境', emoji: '🌿', category: 'traditional' },
  
  // Dynamic content topics (with web crawling)
  { value: 'gaming_news', label: '遊戲最新消息', emoji: '🎮', category: 'dynamic', badge: '最新' },
  { value: 'research_deep_learning', label: '深度學習研究', emoji: '🧠', category: 'dynamic', badge: '研究' },
  { value: 'technology_news', label: '科技新聞', emoji: '💻', category: 'dynamic', badge: '最新' },
  { value: 'health_wellness', label: '健康與養生', emoji: '💚', category: 'dynamic', badge: '最新' },
  { value: 'climate_environment', label: '氣候環境', emoji: '🌍', category: 'dynamic', badge: '最新' },
  { value: 'finance_economics', label: '財經動態', emoji: '💰', category: 'dynamic', badge: '最新' }
]

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const isFormValid = computed(() => {
  return form.value.email && 
         form.value.topics.length > 0 && 
         form.value.frequency &&
         form.value.language &&
         form.value.tone
})

const toggleTopic = (topic: string) => {
  const index = form.value.topics.indexOf(topic)
  if (index > -1) {
    form.value.topics.splice(index, 1)
  } else {
    form.value.topics.push(topic)
  }
}

const toggleDeliveryDay = (day: number) => {
  if (!form.value.preferences.deliveryDays) {
    form.value.preferences.deliveryDays = []
  }
  
  const index = form.value.preferences.deliveryDays.indexOf(day)
  if (index > -1) {
    form.value.preferences.deliveryDays.splice(index, 1)
  } else {
    form.value.preferences.deliveryDays.push(day)
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value || isLoading.value) return
  
  isLoading.value = true
  try {
    if (props.onSubscribe) {
      await props.onSubscribe(form.value)
    }
    // Handle success (could emit event or show success message)
  } catch (error) {
    console.error('Subscription failed:', error)
    // Handle error (could emit error event or show error message)
  } finally {
    isLoading.value = false
  }
}
</script>