<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-display font-bold text-gray-900">訂閱管理</h1>
        <p class="text-gray-600 mt-1">管理您的播客訂閱設定</p>
      </div>
      <div class="flex space-x-3">
        <button @click="showSubscriptionForm = true" class="btn btn-primary">
          <span class="mr-2">➕</span>新增訂閱
        </button>
      </div>
    </div>

    <!-- Active Subscriptions -->
    <div v-if="subscriptions.length > 0" class="space-y-4">
      <h2 class="text-xl font-semibold text-gray-900">目前訂閱</h2>
      
      <div class="grid gap-4">
        <div
          v-for="subscription in subscriptions"
          :key="subscription.id"
          class="card p-6"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-3">
                <div class="w-12 h-12 bg-hakkast-purple/10 rounded-xl flex items-center justify-center">
                  <span class="text-xl">{{ subscription.frequency === 'daily' ? '📅' : '📆' }}</span>
                </div>
                <div>
                  <div class="font-semibold text-gray-900">
                    {{ subscription.frequency === 'daily' ? '每日播客' : '每週播客' }}
                  </div>
                  <div class="text-sm text-gray-500">{{ subscription.email }}</div>
                </div>
                <div
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    subscription.isActive
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  ]"
                >
                  {{ subscription.isActive ? '啟用中' : '已暫停' }}
                </div>
              </div>
              
              <div class="space-y-2">
                <div class="flex items-center space-x-4 text-sm text-gray-600">
                  <span><span class="font-medium">主題：</span>{{ getTopicLabels(subscription.topics) }}</span>
                  <span><span class="font-medium">語言：</span>{{ getLanguageLabel(subscription.language) }}</span>
                  <span><span class="font-medium">風格：</span>{{ getToneLabel(subscription.tone) }}</span>
                </div>
                
                <div class="flex items-center space-x-4 text-sm text-gray-600">
                  <span><span class="font-medium">配送時間：</span>{{ subscription.preferences.deliveryTime }}</span>
                  <span><span class="font-medium">長度：</span>{{ subscription.preferences.maxDuration }}分鐘</span>
                  <span v-if="subscription.lastSent">
                    <span class="font-medium">上次配送：</span>{{ formatDate(subscription.lastSent) }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="flex items-center space-x-2">
              <button
                @click="toggleSubscription(subscription)"
                :class="[
                  'btn btn-sm',
                  subscription.isActive ? 'btn-secondary' : 'btn-primary'
                ]"
              >
                {{ subscription.isActive ? '暫停' : '啟用' }}
              </button>
              <button
                @click="editSubscription(subscription)"
                class="btn btn-ghost btn-sm"
              >
                編輯
              </button>
              <button
                @click="copyRSSUrl(subscription)"
                class="btn btn-ghost btn-sm"
                title="複製RSS連結"
              >
                📡
              </button>
              <button
                @click="deleteSubscription(subscription)"
                class="btn btn-ghost btn-sm text-red-600 hover:text-red-700"
              >
                🗑️
              </button>
            </div>
          </div>
          
          <!-- RSS Feed Info -->
          <div class="mt-4 pt-4 border-t border-gray-100">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-600">
                <span class="font-medium">RSS訂閱源：</span>
                <code class="text-xs bg-gray-100 px-2 py-1 rounded ml-2">
                  {{ getRSSUrl(subscription.id) }}
                </code>
              </div>
              <button
                @click="copyRSSUrl(subscription)"
                class="text-sm text-hakkast-purple hover:text-hakkast-purple/80"
              >
                複製連結
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <span class="text-4xl text-gray-400">📧</span>
      </div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">尚未有任何訂閱</h3>
      <p class="text-gray-600 mb-6">開始訂閱個人化的客語播客內容</p>
      <button @click="showSubscriptionForm = true" class="btn btn-primary">
        <span class="mr-2">🎙️</span>開始訂閱
      </button>
    </div>

    <!-- Subscription Form Modal -->
    <div
      v-if="showSubscriptionForm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-semibold">{{ editingSubscription ? '編輯訂閱' : '新增訂閱' }}</h2>
          <button
            @click="closeSubscriptionForm"
            class="p-2 hover:bg-gray-100 rounded-lg"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <SubscriptionForm
          :initial-data="editingSubscription"
          :on-subscribe="handleSubscriptionSubmit"
        />
      </div>
    </div>

    <!-- Success Toast -->
    <div
      v-if="showSuccessToast"
      class="fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2"
    >
      <span>✅</span>
      <span>{{ successMessage }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import SubscriptionForm from './SubscriptionForm.vue'
import { subscriptionService } from '../services/subscriptionService'
import type { Subscription, SubscriptionRequest } from '../types/subscription'

const subscriptions = ref<Subscription[]>([])
const showSubscriptionForm = ref(false)
const editingSubscription = ref<Subscription | null>(null)
const showSuccessToast = ref(false)
const successMessage = ref('')

const availableTopics = [
  { value: 'culture', label: '客家文化' },
  { value: 'history', label: '歷史故事' },
  { value: 'food', label: '客家美食' },
  { value: 'music', label: '客家音樂' },
  { value: 'language', label: '語言學習' },
  { value: 'festival', label: '節慶習俗' },
  { value: 'nature', label: '自然環境' },
  { value: 'technology', label: '科技創新' }
]

const getTopicLabels = (topics: string[]) => {
  return topics
    .map(topic => availableTopics.find(t => t.value === topic)?.label || topic)
    .join('、')
}

const getLanguageLabel = (language: string) => {
  const labels = {
    'hakka': '純客語',
    'mixed': '客華混合',
    'bilingual': '雙語模式'
  }
  return labels[language as keyof typeof labels] || language
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

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getRSSUrl = (subscriptionId: string) => {
  return `${window.location.origin}/api/rss/${subscriptionId}`
}

const copyRSSUrl = async (subscription: Subscription) => {
  try {
    await navigator.clipboard.writeText(getRSSUrl(subscription.id))
    showToast('RSS連結已複製到剪貼簿')
  } catch (error) {
    console.error('Failed to copy RSS URL:', error)
  }
}

const showToast = (message: string) => {
  successMessage.value = message
  showSuccessToast.value = true
  setTimeout(() => {
    showSuccessToast.value = false
  }, 3000)
}

const toggleSubscription = async (subscription: Subscription) => {
  try {
    const updatedSubscription = await subscriptionService.toggleSubscription(subscription.id)
    const index = subscriptions.value.findIndex(s => s.id === subscription.id)
    if (index > -1) {
      subscriptions.value[index] = updatedSubscription
    }
    showToast(updatedSubscription.isActive ? '訂閱已啟用' : '訂閱已暫停')
  } catch (error) {
    console.error('Failed to toggle subscription:', error)
    showToast('操作失敗，請稍後再試')
  }
}

const editSubscription = (subscription: Subscription) => {
  editingSubscription.value = subscription
  showSubscriptionForm.value = true
}

const deleteSubscription = async (subscription: Subscription) => {
  if (confirm('確定要取消此訂閱嗎？')) {
    try {
      await subscriptionService.deleteSubscription(subscription.id)
      const index = subscriptions.value.findIndex(s => s.id === subscription.id)
      if (index > -1) {
        subscriptions.value.splice(index, 1)
      }
      showToast('訂閱已取消')
    } catch (error) {
      console.error('Failed to delete subscription:', error)
      showToast('取消失敗，請稍後再試')
    }
  }
}

const handleSubscriptionSubmit = async (subscriptionData: SubscriptionRequest) => {
  try {
    if (editingSubscription.value) {
      // Update existing subscription
      const updatedSubscription = await subscriptionService.updateSubscription(
        editingSubscription.value.id, 
        subscriptionData
      )
      const index = subscriptions.value.findIndex(s => s.id === editingSubscription.value!.id)
      if (index > -1) {
        subscriptions.value[index] = updatedSubscription
      }
      showToast('訂閱設定已更新')
    } else {
      // Create new subscription
      const newSubscription = await subscriptionService.createSubscription(subscriptionData)
      subscriptions.value.push(newSubscription)
      showToast('訂閱已成功建立')
    }
    closeSubscriptionForm()
  } catch (error) {
    console.error('Failed to save subscription:', error)
    showToast('操作失敗，請稍後再試')
  }
}

const closeSubscriptionForm = () => {
  showSubscriptionForm.value = false
  editingSubscription.value = null
}

onMounted(async () => {
  // In a real implementation, you would get the user's email from authentication
  // For now, we'll load all subscriptions or use a demo email
  try {
    // You could implement user authentication and get email from there
    // const userEmail = await getCurrentUserEmail()
    // subscriptions.value = await subscriptionService.getSubscriptionsByEmail(userEmail)
    
    // For demo purposes, start with empty subscriptions
    subscriptions.value = []
  } catch (error) {
    console.error('Failed to load subscriptions:', error)
    subscriptions.value = []
  }
})
</script>