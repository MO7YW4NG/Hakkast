<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Enhanced Navigation -->
    <nav class="bg-white/80 backdrop-blur-lg shadow-xl border-b border-gray-200/20 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
          <!-- Brand Logo -->
           <router-link to="/">
            <div class="flex items-center space-x-3">
              <img src="/favicon.ico" alt="Hakkast Logo" class="w-10 h-10 rounded-xl object-contain" />
              <div>
                <h1 class="text-2xl font-display font-bold text-gradient">
                  Hakkast
                </h1>
                <p class="text-xs text-gray-500 font-medium">AI客語Podcast</p>
              </div>
            </div>
          </router-link>
          <!-- Navigation Links -->
          <div class="hidden md:flex space-x-2">
            <router-link 
              to="/" 
              class="nav-link"
              :class="{ 'nav-link-active': $route.path === '/' }"
            >
              <span class="text-lg mr-2">🏠</span>
              首頁
            </router-link>
            <router-link 
              to="/generate" 
              class="nav-link"
              :class="{ 'nav-link-active': $route.path === '/generate' }"
            >
              <span class="text-lg mr-2">✨</span>
              生成Podcast
            </router-link>
            <router-link 
              to="/library" 
              class="nav-link"
              :class="{ 'nav-link-active': $route.path === '/library' }"
            >
              <span class="text-lg mr-2">📚</span>
              我的收藏
            </router-link>
            <router-link 
              to="/subscription" 
              class="nav-link"
              :class="{ 'nav-link-active': $route.path === '/subscription' }"
            >
              <span class="text-lg mr-2">📧</span>
              訂閱服務
            </router-link>
          </div>
          <!-- Mobile Menu Button -->
          <div class="md:hidden">
            <button 
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="p-2 rounded-lg text-hakkast-navy hover:bg-gray-100 transition-colors"
              aria-label="開啟選單"
            >
            <svg class="w-5 h-5 rounded-xl object-contain text-gray-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            </button>
          </div>
        </div>
      </div>
      <!-- Mobile Menu -->
      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-200/20 bg-white/95 backdrop-blur-lg">
        <div class="px-4 py-4 space-y-2">
          <router-link 
            to="/" 
            class="mobile-nav-link"
            @click="mobileMenuOpen = false"
          >
            <span class="text-lg mr-3">🏠</span>
            首頁
          </router-link>
          <router-link 
            to="/generate" 
            class="mobile-nav-link"
            @click="mobileMenuOpen = false"
          >
            <span class="text-lg mr-3">✨</span>
            生成Podcast
          </router-link>
          <router-link 
            to="/library" 
            class="mobile-nav-link"
            @click="mobileMenuOpen = false"
          >
            <span class="text-lg mr-3">📚</span>
            我的庫存
          </router-link>
          <router-link 
            to="/subscription" 
            class="mobile-nav-link"
            @click="mobileMenuOpen = false"
          >
            <span class="text-lg mr-3">📧</span>
            訂閱服務
          </router-link>
        </div>
      </div>
    </nav>
    <!-- Main Content with Enhanced Transitions -->
    <main class="relative">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <!-- Footer -->
    <footer class="bg-hakkast-navy text-white py-12 mt-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid md:grid-cols-3 gap-8">
          <div>
            <div class="flex items-center space-x-3 mb-4">
              <img src="/favicon.ico" alt="Hakkast Icon" class="w-8 h-8 bg-white rounded-lg object-contain flex items-center justify-center" />
              <h3 class="text-xl font-display font-bold">Hakkast</h3>
            </div>
            <p class="text-gray-300 text-sm leading-relaxed">
              你的個人化客語Podcast，傳承客家文化，連結世代情感。
            </p>
          </div>
          <div>
            <h4 class="font-semibold mb-4 text-hakkast-gold">功能特色</h4>
            <ul class="space-y-2 text-sm text-gray-300">
              <li>• AI智慧內容生成</li>
              <li>• 真實客語翻譯</li>
              <li>• 高品質語音合成</li>
              <li>• 多語言支援</li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-4 text-hakkast-gold">技術支援</h4>
            <ul class="space-y-2 text-sm text-gray-300">
              <li>• Gemini AI</li>
              <li>• Hakka AI APIs</li>
              <li>• Vue.js + FastAPI</li>
              <li>• Docker 容器化</li>
            </ul>
          </div>
        </div>
        <div class="border-t border-hakkast-purple/30 mt-8 pt-8 text-center">
          <p class="text-gray-400 text-sm">
            © 2025 Hakkast. 致力於客家文化的數位傳承與創新。
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const mobileMenuOpen = ref(false)
</script>

<style scoped>
.nav-link {
  @apply px-4 py-2 rounded-xl font-medium text-hakkast-navy hover:bg-hakkast-purple hover:text-white transition-all duration-300 flex items-center;
}

.nav-link-active {
  @apply bg-hakkast-gradient text-white shadow-lg;
}

.mobile-nav-link {
  @apply flex items-center w-full px-4 py-3 rounded-xl font-medium text-hakkast-navy hover:bg-hakkast-purple hover:text-white transition-all duration-300;
}

/* Page transitions */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease-out;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>