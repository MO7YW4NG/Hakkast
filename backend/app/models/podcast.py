class PodcastGenerationRequest:
    def __init__(self, topic: str, content: str, tone: str, duration: int):
        self.topic = topic
        self.content = content
        self.tone = tone
        self.duration = duration


class PodcastScript:
    def __init__(self, title: str, hosts: list, estimated_duration_minutes: int, key_points: list, full_dialogue: str):
        self.title = title
        self.hosts = hosts
        self.estimated_duration_minutes = estimated_duration_minutes
        self.key_points = key_points
        self.full_dialogue = full_dialogue


class Article:
    def __init__(self, title: str, content: str, summary: str, source: str, published_at: str, url: str):
        self.title = title
        self.content = content
        self.summary = summary
        self.source = source
        self.published_at = published_at
        self.url = url