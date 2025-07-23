<template>
  <div class="min-h-screen">
    <!-- Hero Section -->
    <section class="relative hero-pattern py-32 lg:py-42 overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-white/50 to-white/30"></div>
      
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid lg:grid-cols-2 gap-12 items-center">
          <!-- Left Content -->
          <motion.div :initial="{ opacity: 0, x: -60 }" :animate="{ opacity: 1, x: 0 }" :transition="{ duration: 0.8 }" class="text-center lg:text-left">
            <div class="inline-flex items-center space-x-2 bg-hakkast-gold/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6">
              <span class="w-2 h-2 bg-hakkast-gold rounded-full animate-pulse"></span>
              <span class="text-sm font-medium text-hakkast-navy">AI驅動的客語創新</span>
            </div>
            <div class="flex justify-center lg:justify-start my-4 mb-8">
              <img src="/logo.png" alt="Hakkast Logo" class="w-82 max-w-lg object-contain rounded-xl" />
            </div>
            <p class="text-xl text-gray-600 mb-8 leading-relaxed max-w-lg mx-auto lg:mx-0">
              運用先進AI技術，一鍵生成個人化客語Podcast。<br />
              <span class="text-hakkast-purple font-medium">傳承文化，連結世代，創造無限可能。</span>
            </p>
            
            <div class="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <router-link to="/generate" class="btn btn-primary text-lg">
                <span class="mr-2">✨</span>
                立即開始創作
              </router-link>
              <button class="btn btn-secondary text-lg" @click="scrollToFeatures">
                <span class="mr-2">📖</span>
                了解更多
              </button>
            </div>
            
            <div class="mt-8 flex items-center justify-center lg:justify-start space-x-6 text-sm text-gray-500">
              <div class="flex items-center space-x-2">
                <div class="w-8 h-8 bg-hakkast-gradient rounded-lg flex items-center justify-center">
                  <span class="text-white text-xs">AI</span>
                </div>
                <span>智慧生成</span>
              </div>
              <div class="flex items-center space-x-2">
                <div class="w-8 h-8 bg-hakkast-gold rounded-lg flex items-center justify-center">
                  <span class="text-hakkast-navy text-xs">🎵</span>
                </div>
                <span>真實語音</span>
              </div>
              <div class="flex items-center space-x-2">
                <div class="w-8 h-8 bg-hakkast-purple rounded-lg flex items-center justify-center">
                  <span class="text-white text-xs">客</span>
                </div>
                <span>文化傳承</span>
              </div>
            </div>
          </motion.div>
          
          <!-- Right Visual -->
          <motion.div :initial="{ opacity: 0, y: 60 }" :animate="{ opacity: 1, y: 0 }" :transition="{ duration: 0.8, delay: 0.2 }" class="relative animate-float">
            <div class="relative">
              <!-- Main card -->
              <motion.div :initial="{ scale: 0.8, opacity: 0 }" :animate="{ scale: 1, opacity: 1 }" :transition="{ duration: 0.7, delay: 0.4 }" class="card-gradient p-8 transform rotate-3 hover:rotate-0 transition-transform duration-500">
                <div class="flex items-center space-x-3 mb-6">
                  <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <span class="text-2xl">🎙️</span>
                  </div>
                  <div>
                    <h3 class="text-xl font-semibold text-white">客家美食文化</h3>
                    <p class="text-white/80 text-sm">AI Podcast • 15分鐘</p>
                  </div>
                </div>
                
                <div class="space-y-3 mb-6">
                  <div class="h-2 bg-white/20 rounded-full overflow-hidden">
                    <div class="h-full bg-hakkast-gold w-2/3 rounded-full animate-pulse"></div>
                  </div>
                  <div class="flex justify-between text-white/80 text-xs">
                    <span>正在生成...</span>
                    <span>67%</span>
                  </div>
                </div>
                
                <div class="flex space-x-2">
                  <button class="btn btn-gold btn-sm">播放</button>
                  <button class="btn btn-ghost btn-sm">下載</button>
                </div>
              </motion.div>
              
              <!-- Floating elements -->
              <motion.div :initial="{ opacity: 0, y: -30 }" :animate="{ opacity: 1, y: 0 }" :transition="{ duration: 0.7, delay: 0.7 }" class="absolute -top-4 -right-4 w-16 h-16 bg-hakkast-gold rounded-2xl shadow-lg flex items-center justify-center animate-pulse-slow">
                <span class="text-2xl">📻</span>
              </motion.div>
              <motion.div :initial="{ opacity: 0, y: 30 }" :animate="{ opacity: 1, y: 0 }" :transition="{ duration: 0.7, delay: 0.9 }" class="absolute -bottom-4 -left-4 w-12 h-12 bg-white rounded-xl shadow-lg flex items-center justify-center animate-float" style="animation-delay: 1s;">
                <span class="text-xl">🏮</span>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-display font-bold text-hakkast-navy mb-4">
            為什麼選擇 <span class="text-gradient">Hakkast</span>？
          </h2>
          <p class="text-xl text-gray-600 max-w-3xl mx-auto">
            結合最新AI技術與客家文化精髓，提供前所未有的Podcast創作體驗
          </p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8 mb-16">
          <div class="group">
            <div class="card p-8 text-center group-hover:scale-105 transition-transform duration-300">
              <div class="w-16 h-16 bg-hakkast-gradient rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                <span class="text-3xl">🧠</span>
              </div>
              <h3 class="text-xl font-semibold text-hakkast-navy mb-3">三步AI流程</h3>
              <p class="text-gray-600 mb-4">
                中文生成 → 客語翻譯 → 語音合成，確保內容品質與文化準確性
              </p>
              <div class="space-y-2 text-sm text-gray-500">
                <div class="flex items-center justify-center space-x-2">
                  <span class="w-2 h-2 bg-hakkast-purple rounded-full"></span>
                  <span>Gemini AI 內容生成</span>
                </div>
                <div class="flex items-center justify-center space-x-2">
                  <span class="w-2 h-2 bg-hakkast-lavender rounded-full"></span>
                  <span>專業客語翻譯</span>
                </div>
                <div class="flex items-center justify-center space-x-2">
                  <span class="w-2 h-2 bg-hakkast-gold rounded-full"></span>
                  <span>自然語音合成</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Feature 2 -->
          <div class="group">
            <div class="card p-8 text-center group-hover:scale-105 transition-transform duration-300">
              <div class="w-16 h-16 bg-hakkast-gradient rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                <span class="text-3xl">🎨</span>
              </div>
              <h3 class="text-xl font-semibold text-hakkast-navy mb-3">客製化體驗</h3>
              <p class="text-gray-600 mb-4">
                多種主題選擇、語調風格、時長設定，打造專屬於您的Podcast內容
              </p>
              <div class="flex justify-center space-x-2 mb-4">
                <span class="px-3 py-1 bg-hakkast-purple/10 text-hakkast-purple rounded-full text-xs">學術研究</span>
                <span class="px-3 py-1 bg-hakkast-lavender/10 text-hakkast-lavender rounded-full text-xs">時事討論</span>
              </div>
              <div class="flex justify-center space-x-2">
                <span class="px-3 py-1 bg-hakkast-gold/10 text-hakkast-navy rounded-full text-xs">文化傳承</span>
                <span class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">生活分享</span>
              </div>
            </div>
          </div>
          
          <!-- Feature 3 -->
          <div class="group">
            <div class="card p-8 text-center group-hover:scale-105 transition-transform duration-300">
              <div class="w-16 h-16 bg-hakkast-gradient rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                <span class="text-3xl">🔊</span>
              </div>
              <h3 class="text-xl font-semibold text-hakkast-navy mb-3">多語言支援</h3>
              <p class="text-gray-600 mb-4">
                支援純客語、客華混合、雙語模式，滿足不同使用者需求
              </p>
              <div class="space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">客語內容</span>
                  <span class="text-hakkast-purple font-medium">100%</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">羅馬拼音</span>
                  <span class="text-hakkast-lavender font-medium">支援</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">語音品質</span>
                  <span class="text-hakkast-gold font-medium">專業級</span>
                </div>
              </div>
            </div>
          </div>

        </div>
        
        <!-- CTA Section -->
        <motion.div :initial="{ opacity: 0, scale: 0.95 }" :animate="{ opacity: 1, scale: 1 }" :transition="{ duration: 0.7, delay: 0.5 }" class="text-center">
          <div class="card-gradient p-12 max-w-4xl mx-auto">
            <h3 class="text-3xl font-display font-bold text-white mb-4">
              準備開始您的客語Podcast之旅嗎？
            </h3>
            <p class="text-xl text-white/90 mb-8">
              只需幾分鐘，就能創造出專業品質的客語Podcast
            </p>
            <router-link to="/generate" class="btn btn-gold text-lg">
              <span class="mr-2">🚀</span>
              立即體驗 Hakkast
            </router-link>
          </div>
        </motion.div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="py-16 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div class="text-center">
            <div class="text-3xl font-bold text-hakkast-navy mb-2">AI</div>
            <div class="text-sm text-gray-600">驅動技術</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-hakkast-purple mb-2">3步</div>
            <div class="text-sm text-gray-600">生成流程</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-hakkast-lavender mb-2">多種</div>
            <div class="text-sm text-gray-600">語言模式</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-hakkast-gold mb-2">客家</div>
            <div class="text-sm text-gray-600">文化傳承</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Subscription CTA Section -->
    <section class="py-20 card-gradient">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="mb-8">
          <div class="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <span class="text-4xl">📧</span>
          </div>
          <h2 class="text-4xl font-display font-bold text-white mb-4">
            訂閱個人化客語Podcast
          </h2>
          <p class="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            每日或每週收到為您量身打造的客語播客內容，透過電子郵件配送或 RSS 訂閱
          </p>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-10">
          <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
            <div class="text-3xl mb-4">📅</div>
            <h3 class="text-xl font-semibold text-white mb-2">每日Podcast</h3>
            <p class="text-white/80 text-sm">每天早上收到新鮮的客語內容，讓您的一天從客家文化開始</p>
          </div>
          <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
            <div class="text-3xl mb-4">📆</div>
            <h3 class="text-xl font-semibold text-white mb-2">每週精選</h3>
            <p class="text-white/80 text-sm">每週收到精心策劃的主題Podcast，深度探索客家文化各面向</p>
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex flex-wrap justify-center items-center gap-4 text-white/80 text-sm">
            <div class="flex items-center space-x-2">
              <span>📧</span>
              <span>電子郵件配送</span>
            </div>
            <div class="flex items-center space-x-2">
              <span>📡</span>
              <span>RSS 訂閱支援</span>
            </div>
            <div class="flex items-center space-x-2">
              <span>🎯</span>
              <span>個人化主題</span>
            </div>
            <div class="flex items-center space-x-2">
              <span>🔤</span>
              <span>羅馬拼音選擇</span>
            </div>
          </div>
          
          <div class="pt-4">
            <router-link to="/subscription" class="btn btn-gold text-lg">
              <span class="mr-2">🎙️</span>
              開始訂閱
            </router-link>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { motion } from 'motion-v'
const scrollToFeatures = () => {
  const element = document.getElementById('features')
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>