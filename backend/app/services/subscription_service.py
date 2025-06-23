import uuid
import smtplib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import logging

from ..models.subscription import (
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    PodcastEpisode, PodcastFeed, EmailTemplate
)
from ..core.config import settings
from .ai_service import AIService
from .podcast_service import PodcastService

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.ai_service = AIService()
        self.podcast_service = PodcastService()
        # In a real implementation, you would use a database
        self._subscriptions: Dict[str, Subscription] = {}
        
    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new podcast subscription"""
        subscription_id = str(uuid.uuid4())
        rss_token = str(uuid.uuid4())
        
        subscription = Subscription(
            id=subscription_id,
            email=subscription_data.email,
            frequency=subscription_data.frequency,
            topics=subscription_data.topics,
            language=subscription_data.language,
            tone=subscription_data.tone,
            preferences=subscription_data.preferences,
            created_at=datetime.utcnow(),
            rss_token=rss_token
        )
        
        self._subscriptions[subscription_id] = subscription
        
        # Send welcome email
        await self._send_welcome_email(subscription)
        
        logger.info(f"Created subscription {subscription_id} for {subscription_data.email}")
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self._subscriptions.get(subscription_id)
    
    async def get_subscriptions_by_email(self, email: str) -> List[Subscription]:
        """Get all subscriptions for an email"""
        return [
            sub for sub in self._subscriptions.values() 
            if sub.email == email
        ]
    
    async def update_subscription(
        self, 
        subscription_id: str, 
        update_data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """Update an existing subscription"""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(subscription, field, value)
        
        logger.info(f"Updated subscription {subscription_id}")
        return subscription
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription"""
        if subscription_id in self._subscriptions:
            subscription = self._subscriptions[subscription_id]
            del self._subscriptions[subscription_id]
            
            # Send unsubscribe confirmation email
            await self._send_unsubscribe_email(subscription)
            
            logger.info(f"Deleted subscription {subscription_id}")
            return True
        return False
    
    async def toggle_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Toggle subscription active status"""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.is_active = not subscription.is_active
            logger.info(f"Toggled subscription {subscription_id} to {'active' if subscription.is_active else 'inactive'}")
        return subscription
    
    async def generate_and_send_podcasts(self):
        """Generate and send podcasts for all active subscriptions"""
        now = datetime.utcnow()
        
        for subscription in self._subscriptions.values():
            if not subscription.is_active:
                continue
                
            # Check if it's time to send
            if not self._should_send_now(subscription, now):
                continue
            
            try:
                # Generate podcast content
                podcast_content = await self._generate_podcast_for_subscription(subscription)
                
                # Send email with podcast
                await self._send_podcast_email(subscription, podcast_content)
                
                # Update last sent time
                subscription.last_sent = now
                
                logger.info(f"Sent podcast to subscription {subscription.id}")
                
            except Exception as e:
                logger.error(f"Failed to send podcast to subscription {subscription.id}: {e}")
    
    def _should_send_now(self, subscription: Subscription, now: datetime) -> bool:
        """Check if it's time to send a podcast"""
        if not subscription.last_sent:
            return True
        
        if subscription.frequency == "daily":
            # Send daily at specified time
            time_diff = now - subscription.last_sent
            return time_diff.days >= 1
        
        elif subscription.frequency == "weekly":
            # Send weekly on specified days
            time_diff = now - subscription.last_sent
            if time_diff.days >= 7:
                return True
            
            # Check if today is a delivery day
            delivery_days = subscription.preferences.delivery_days or [1]  # Default to Monday
            return now.weekday() in delivery_days
        
        return False
    
    async def _generate_podcast_for_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """Generate personalized podcast content for a subscription"""
        # Create a podcast generation request based on subscription preferences
        from ..models.podcast import PodcastGenerationRequest
        
        # Select a random topic from user's interests
        import random
        selected_topic = random.choice(subscription.topics)
        
        request = PodcastGenerationRequest(
            topic=f"關於{selected_topic}的最新內容",
            duration=subscription.preferences.max_duration,
            tone=subscription.tone,
            language=subscription.language,
            include_music=False
        )
        
        # Generate the podcast
        result = await self.ai_service.generate_hakka_podcast_content(request)
        
        return {
            "title": f"{selected_topic}播客 - {datetime.now().strftime('%Y-%m-%d')}",
            "content": result,
            "topic": selected_topic,
            "subscription": subscription
        }
    
    async def _send_welcome_email(self, subscription: Subscription):
        """Send welcome email to new subscriber"""
        subject = "歡迎訂閱 Hakkast 客語播客！"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #0E2148, #483AA0); padding: 30px; text-align: center; color: white;">
                <h1 style="margin: 0; font-size: 28px;">🎙️ 歡迎來到 Hakkast！</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">您的個人化客語播客之旅開始了</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #0E2148; margin-bottom: 20px;">訂閱詳情</h2>
                <ul style="color: #555; line-height: 1.6;">
                    <li><strong>頻率：</strong>{'每日' if subscription.frequency == 'daily' else '每週'}</li>
                    <li><strong>主題：</strong>{', '.join(subscription.topics)}</li>
                    <li><strong>語言：</strong>{subscription.language}</li>
                    <li><strong>風格：</strong>{subscription.tone}</li>
                    <li><strong>配送時間：</strong>{subscription.preferences.delivery_time}</li>
                </ul>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #0E2148; margin-top: 0;">📡 您的專屬 RSS 連結</h3>
                    <p style="margin: 10px 0; color: #555;">您可以在任何播客應用程式中添加此連結：</p>
                    <code style="background: #e9ecef; padding: 10px; border-radius: 5px; display: block; word-break: break-all;">
                        {settings.BASE_URL}/api/rss/{subscription.id}?token={subscription.rss_token}
                    </code>
                </div>
                
                <p style="color: #555; margin-top: 30px;">
                    感謝您選擇 Hakkast！我們將為您精心製作個人化的客語播客內容。
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #888; font-size: 12px;">
                <p>如果您不想再收到這些郵件，可以 <a href="{settings.BASE_URL}/unsubscribe/{subscription.id}" style="color: #483AA0;">取消訂閱</a></p>
            </div>
        </div>
        """
        
        text_content = f"""
        歡迎訂閱 Hakkast 客語播客！
        
        您的訂閱詳情：
        - 頻率：{'每日' if subscription.frequency == 'daily' else '每週'}
        - 主題：{', '.join(subscription.topics)}
        - 語言：{subscription.language}
        - 風格：{subscription.tone}
        
        RSS 連結：{settings.BASE_URL}/api/rss/{subscription.id}?token={subscription.rss_token}
        
        取消訂閱：{settings.BASE_URL}/unsubscribe/{subscription.id}
        """
        
        await self._send_email(
            to_email=subscription.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def _send_podcast_email(self, subscription: Subscription, podcast_content: Dict[str, Any]):
        """Send podcast email to subscriber"""
        content = podcast_content["content"]
        title = podcast_content["title"]
        
        subject = f"🎙️ 今日客語播客：{title}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #0E2148, #483AA0); padding: 30px; text-align: center; color: white;">
                <h1 style="margin: 0; font-size: 24px;">🎙️ {title}</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #0E2148; margin-top: 0;">🎵 音訊播客</h3>
                    <audio controls style="width: 100%;">
                        <source src="{content.get('audio_url', '')}" type="audio/mpeg">
                        您的瀏覽器不支援音訊播放。
                    </audio>
                </div>
                
                {'<div style="margin: 20px 0;"><h3 style="color: #0E2148;">📝 客語內容</h3><p style="line-height: 1.6; color: #555;">' + content.get('hakka_content', '') + '</p></div>' if subscription.preferences.include_transcript else ''}
                
                {'<div style="margin: 20px 0;"><h3 style="color: #0E2148;">🔤 羅馬拼音</h3><p style="line-height: 1.6; color: #555; font-family: monospace;">' + content.get('romanization', '') + '</p></div>' if subscription.preferences.include_romanization and content.get('romanization') else ''}
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #0E2148;">📄 中文原稿</h3>
                    <p style="line-height: 1.6; color: #555;">{content.get('chinese_content', '')}</p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #888; font-size: 12px;">
                <p>
                    <a href="{settings.BASE_URL}/subscription/{subscription.id}" style="color: #483AA0; text-decoration: none;">管理訂閱</a> | 
                    <a href="{settings.BASE_URL}/unsubscribe/{subscription.id}" style="color: #483AA0; text-decoration: none;">取消訂閱</a>
                </p>
            </div>
        </div>
        """
        
        text_content = f"""
        {title}
        {datetime.now().strftime('%Y年%m月%d日')}
        
        客語內容：
        {content.get('hakka_content', '')}
        
        中文原稿：
        {content.get('chinese_content', '')}
        
        音訊連結：{content.get('audio_url', '')}
        
        管理訂閱：{settings.BASE_URL}/subscription/{subscription.id}
        取消訂閱：{settings.BASE_URL}/unsubscribe/{subscription.id}
        """
        
        await self._send_email(
            to_email=subscription.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def _send_unsubscribe_email(self, subscription: Subscription):
        """Send unsubscribe confirmation email"""
        subject = "Hakkast 訂閱已取消"
        
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; text-align: center; padding: 30px;">
            <h2 style="color: #0E2148;">😢 很遺憾看到您離開</h2>
            <p style="color: #555; line-height: 1.6;">您的 Hakkast 客語播客訂閱已成功取消。</p>
            <p style="color: #555; line-height: 1.6;">如果您改變主意，隨時歡迎您回來訂閱！</p>
            <a href="{}" style="display: inline-block; background: #483AA0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-top: 20px;">重新訂閱</a>
        </div>
        """.format(settings.BASE_URL)
        
        text_content = """
        很遺憾看到您離開
        
        您的 Hakkast 客語播客訂閱已成功取消。
        如果您改變主意，隨時歡迎您回來訂閱！
        
        重新訂閱：{}
        """.format(settings.BASE_URL)
        
        await self._send_email(
            to_email=subscription.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str):
        """Send email using SMTP"""
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MimeText(text_content, 'plain', 'utf-8')
            html_part = MimeText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
    
    async def generate_rss_feed(self, subscription_id: str, token: str) -> Optional[str]:
        """Generate RSS feed for a subscription"""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription or subscription.rss_token != token:
            return None
        
        # Generate RSS XML
        episodes = await self._get_recent_episodes_for_subscription(subscription)
        
        rss_xml = self._generate_rss_xml(subscription, episodes)
        return rss_xml
    
    async def _get_recent_episodes_for_subscription(self, subscription: Subscription) -> List[PodcastEpisode]:
        """Get recent episodes for a subscription"""
        # In a real implementation, you would fetch from database
        # For now, return empty list
        return []
    
    def _generate_rss_xml(self, subscription: Subscription, episodes: List[PodcastEpisode]) -> str:
        """Generate RSS XML for podcast feed"""
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        # Create RSS structure
        rss = ET.Element("rss", version="2.0")
        rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
        
        channel = ET.SubElement(rss, "channel")
        
        # Channel info
        ET.SubElement(channel, "title").text = f"Hakkast 個人播客 - {subscription.email}"
        ET.SubElement(channel, "description").text = f"為 {subscription.email} 個人化的客語播客內容"
        ET.SubElement(channel, "language").text = "zh-TW"
        ET.SubElement(channel, "copyright").text = "© 2024 Hakkast"
        ET.SubElement(channel, "link").text = f"{settings.BASE_URL}"
        
        # iTunes specific tags
        ET.SubElement(channel, "itunes:author").text = "Hakkast AI"
        ET.SubElement(channel, "itunes:category", text="Education")
        ET.SubElement(channel, "itunes:explicit").text = "false"
        
        # Add episodes
        for episode in episodes:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = episode.title
            ET.SubElement(item, "description").text = episode.description
            ET.SubElement(item, "pubDate").text = episode.published_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
            ET.SubElement(item, "guid", isPermaLink="false").text = episode.id
            
            if episode.audio_url:
                enclosure = ET.SubElement(item, "enclosure")
                enclosure.set("url", episode.audio_url)
                enclosure.set("type", "audio/mpeg")
                enclosure.set("length", str(episode.duration))
        
        # Pretty print XML
        rough_string = ET.tostring(rss, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')