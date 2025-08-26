import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mockUserService } from '../mock/mockService'

export const useMockUserStore = defineStore('mockUser', () => {
  const user = ref<typeof import('../mock/mockData').mockUser | null>(null)
  const notifications = ref<typeof import('../mock/mockData').mockNotifications>([])
  const systemSettings = ref<typeof import('../mock/mockData').mockSystemSettings | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Fetch user info
  const fetchUser = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const fetchedUser = await mockUserService.getUser()
      user.value = fetchedUser
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Update user info
  const updateUser = async (updateData: Partial<typeof import('../mock/mockData').mockUser>) => {
    isLoading.value = true
    error.value = null
    
    try {
      if (user.value) {
        Object.assign(user.value, updateData)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Fetch notifications
  const fetchNotifications = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const fetchedNotifications = await mockUserService.getNotifications()
      notifications.value = fetchedNotifications
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch notifications'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Mark notification as read
  const markNotificationAsRead = async (notificationId: string) => {
    try {
      await mockUserService.markNotificationAsRead(notificationId)
      
      // Update local state
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.isRead = true
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to mark notification as read'
      throw err
    }
  }

  // Mark all notifications as read
  const markAllNotificationsAsRead = async () => {
    try {
      for (const notification of notifications.value) {
        if (!notification.isRead) {
          await mockUserService.markNotificationAsRead(notification.id)
          notification.isRead = true
        }
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to mark all notifications as read'
      throw err
    }
  }

  // Delete notification
  const deleteNotification = async (notificationId: string) => {
    try {
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index > -1) {
        notifications.value.splice(index, 1)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete notification'
      throw err
    }
  }

  // Get unread notification count
  const getUnreadNotificationCount = () => {
    return notifications.value.filter(n => !n.isRead).length
  }

  // Get notification statistics
  const getNotificationStats = () => {
    const total = notifications.value.length
    const unread = notifications.value.filter(n => !n.isRead).length
    const read = total - unread
    
    // Stats by type
    const typeStats = notifications.value.reduce((acc, notif) => {
      acc[notif.type] = (acc[notif.type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return {
      total,
      unread,
      read,
      typeStats
    }
  }

  // Fetch system settings
  const fetchSystemSettings = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const fetchedSettings = await mockUserService.getSystemSettings()
      systemSettings.value = fetchedSettings
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch system settings'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Update system settings
  const updateSystemSettings = async (settings: Partial<typeof import('../mock/mockData').mockSystemSettings>) => {
    isLoading.value = true
    error.value = null
    
    try {
      if (systemSettings.value) {
        const updatedSettings = await mockUserService.updateSystemSettings(settings)
        systemSettings.value = updatedSettings
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update system settings'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Update TTS settings
  const updateTTSSettings = async (ttsSettings: Partial<typeof import('../mock/mockData').mockSystemSettings['tts']>) => {
    if (systemSettings.value) {
      Object.assign(systemSettings.value.tts, ttsSettings)
    }
  }

  // Update language settings
  const updateLanguageSettings = async (languageSettings: Partial<typeof import('../mock/mockData').mockSystemSettings['language']>) => {
    if (systemSettings.value) {
      Object.assign(systemSettings.value.language, languageSettings)
    }
  }

  // Update notification settings
  const updateNotificationSettings = async (notificationSettings: Partial<typeof import('../mock/mockData').mockSystemSettings['notification']>) => {
    if (systemSettings.value) {
      Object.assign(systemSettings.value.notification, notificationSettings)
    }
  }

  // Get user statistics
  const getUserStats = () => {
    if (!user.value) return null
    
    return {
      totalPodcasts: user.value.stats.totalPodcasts,
      totalListeningTime: user.value.stats.totalListeningTime,
      favoriteTopic: user.value.stats.favoriteTopic,
      subscriptionCount: user.value.stats.subscriptionCount,
      averageListeningTime: user.value.stats.totalListeningTime / user.value.stats.totalPodcasts
    }
  }

  // Get user preferences
  const getUserPreferences = () => {
    if (!user.value) return null
    
    return {
      defaultLanguage: user.value.preferences.defaultLanguage,
      defaultTone: user.value.preferences.defaultTone,
      defaultDuration: user.value.preferences.defaultDuration,
      favoriteTopics: user.value.preferences.favoriteTopics
    }
  }

  // Update user preferences
  const updateUserPreferences = async (preferences: Partial<typeof import('../mock/mockData').mockUser.preferences>) => {
    if (user.value) {
      Object.assign(user.value.preferences, preferences)
    }
  }

  // Reset state
  const resetState = () => {
    user.value = null
    notifications.value = []
    systemSettings.value = null
    isLoading.value = false
    error.value = null
  }

  // Simulate login
  const login = async (email: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      await delay(500) // Simulate login delay
      
      // Set user email
      if (user.value) {
        user.value.email = email
      }
      
      // Fetch user-related data
      await Promise.all([
        fetchUser(),
        fetchNotifications(),
        fetchSystemSettings()
      ])
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Simulate logout
  const logout = async () => {
    isLoading.value = true
    
    try {
      await delay(300) // Simulate logout delay
      resetState()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Logout failed'
    } finally {
      isLoading.value = false
    }
  }

  // Helper: delay
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  return {
    user,
    notifications,
    systemSettings,
    isLoading,
    error,
    fetchUser,
    updateUser,
    fetchNotifications,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    deleteNotification,
    getUnreadNotificationCount,
    getNotificationStats,
    fetchSystemSettings,
    updateSystemSettings,
    updateTTSSettings,
    updateLanguageSettings,
    updateNotificationSettings,
    getUserStats,
    getUserPreferences,
    updateUserPreferences,
    login,
    logout,
    resetState
  }
})
