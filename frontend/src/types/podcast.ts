export interface Podcast {
  id: string
  title: string
  chineseContent: string
  hakkaContent: string
  romanization?: string
  topic: string
  tone: 'casual' | 'educational' | 'storytelling' | 'interview'
  duration: number
  language: 'hakka' | 'mixed' | 'bilingual'
  interests?: string
  createdAt: string
  audioUrl?: string
  audioDuration?: number
}

export interface PodcastGenerationRequest {
  topic: string
  tone: 'casual' | 'educational' | 'storytelling' | 'interview'
  duration: number
  language: 'hakka' | 'mixed' | 'bilingual'
  interests?: string
}