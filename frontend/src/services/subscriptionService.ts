import type { Subscription, SubscriptionRequest } from '../types/subscription'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export class SubscriptionService {
  private static instance: SubscriptionService
  
  static getInstance(): SubscriptionService {
    if (!SubscriptionService.instance) {
      SubscriptionService.instance = new SubscriptionService()
    }
    return SubscriptionService.instance
  }

  async createSubscription(subscriptionData: SubscriptionRequest): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/subscription/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: subscriptionData.email,
        frequency: subscriptionData.frequency,
        topic: subscriptionData.topic,
        language: subscriptionData.language,
        tone: subscriptionData.tone,
        preferences: {
          delivery_time: subscriptionData.preferences.deliveryTime,
          delivery_days: subscriptionData.preferences.deliveryDays,
          max_duration: subscriptionData.preferences.maxDuration,
          include_transcript: subscriptionData.preferences.includeTranscript,
          include_romanization: subscriptionData.preferences.includeRomanization,
          notification_email: subscriptionData.preferences.notificationEmail
        }
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create subscription')
    }

    const data = await response.json()
    return this.mapSubscriptionFromAPI(data)
  }

  async getSubscription(subscriptionId: string): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/subscription/${subscriptionId}`)
    
    if (!response.ok) {
      throw new Error('Subscription not found')
    }

    const data = await response.json()
    return this.mapSubscriptionFromAPI(data)
  }

  async getSubscriptionsByEmail(email: string): Promise<Subscription[]> {
    const response = await fetch(`${API_BASE_URL}/subscription/email/${encodeURIComponent(email)}`)
    
    if (!response.ok) {
      throw new Error('Failed to fetch subscriptions')
    }

    const data = await response.json()
    return data.map((sub: any) => this.mapSubscriptionFromAPI(sub))
  }

  async updateSubscription(subscriptionId: string, updateData: Partial<SubscriptionRequest>): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/subscription/${subscriptionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        frequency: updateData.frequency,
        topic: updateData.topic,
        language: updateData.language,
        tone: updateData.tone,
        preferences: updateData.preferences ? {
          delivery_time: updateData.preferences.deliveryTime,
          delivery_days: updateData.preferences.deliveryDays,
          max_duration: updateData.preferences.maxDuration,
          include_transcript: updateData.preferences.includeTranscript,
          include_romanization: updateData.preferences.includeRomanization,
          notification_email: updateData.preferences.notificationEmail
        } : undefined
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update subscription')
    }

    const data = await response.json()
    return this.mapSubscriptionFromAPI(data)
  }

  async toggleSubscription(subscriptionId: string): Promise<Subscription> {
    const response = await fetch(`${API_BASE_URL}/subscription/${subscriptionId}/toggle`, {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error('Failed to toggle subscription')
    }

    const data = await response.json()
    return this.mapSubscriptionFromAPI(data)
  }

  async deleteSubscription(subscriptionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/subscription/${subscriptionId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      throw new Error('Failed to delete subscription')
    }
  }

  getRSSUrl(subscriptionId: string, token: string): string {
    return `${API_BASE_URL}/subscription/rss/${subscriptionId}?token=${token}`
  }

  getUnsubscribeUrl(subscriptionId: string): string {
    return `${API_BASE_URL}/subscription/unsubscribe/${subscriptionId}`
  }

  private mapSubscriptionFromAPI(apiData: any): Subscription {
    return {
      id: apiData.id,
      email: apiData.email,
      frequency: apiData.frequency,
      topic: apiData.topic,
      language: apiData.language,
      tone: apiData.tone,
      isActive: apiData.is_active,
      createdAt: apiData.created_at,
      lastSent: apiData.last_sent,
      preferences: {
        deliveryTime: apiData.preferences.delivery_time,
        deliveryDays: apiData.preferences.delivery_days,
        maxDuration: apiData.preferences.max_duration,
        includeTranscript: apiData.preferences.include_transcript,
        includeRomanization: apiData.preferences.include_romanization,
        notificationEmail: apiData.preferences.notification_email
      }
    }
  }
}

export const subscriptionService = SubscriptionService.getInstance()