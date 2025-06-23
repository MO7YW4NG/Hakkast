from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import PlainTextResponse
from typing import List
import logging

from ..models.subscription import (
    Subscription, SubscriptionCreate, SubscriptionUpdate
)
from ..services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["subscription"])

# Dependency to get subscription service
def get_subscription_service() -> SubscriptionService:
    return SubscriptionService()

@router.post("/", response_model=Subscription)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Create a new podcast subscription"""
    try:
        subscription = await service.create_subscription(subscription_data)
        return subscription
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Get subscription by ID"""
    subscription = await service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.get("/email/{email}", response_model=List[Subscription])
async def get_subscriptions_by_email(
    email: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Get all subscriptions for an email"""
    subscriptions = await service.get_subscriptions_by_email(email)
    return subscriptions

@router.put("/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: str,
    update_data: SubscriptionUpdate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Update an existing subscription"""
    subscription = await service.update_subscription(subscription_id, update_data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.post("/{subscription_id}/toggle", response_model=Subscription)
async def toggle_subscription(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Toggle subscription active status"""
    subscription = await service.toggle_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Delete a subscription"""
    success = await service.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Subscription deleted successfully"}

@router.get("/rss/{subscription_id}")
async def get_rss_feed(
    subscription_id: str,
    token: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Get RSS feed for a subscription"""
    rss_xml = await service.generate_rss_feed(subscription_id, token)
    if not rss_xml:
        raise HTTPException(status_code=404, detail="RSS feed not found or invalid token")
    
    return PlainTextResponse(
        content=rss_xml, 
        media_type="application/rss+xml",
        headers={"Content-Disposition": "inline; filename=podcast.xml"}
    )

@router.get("/unsubscribe/{subscription_id}")
async def unsubscribe_page(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Unsubscribe page (web interface)"""
    subscription = await service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # In a real implementation, you would render an HTML template
    # For now, return a simple message
    return {
        "message": "Unsubscribe page",
        "subscription_id": subscription_id,
        "email": subscription.email
    }

@router.post("/unsubscribe/{subscription_id}")
async def confirm_unsubscribe(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Confirm unsubscribe"""
    success = await service.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {"message": "Successfully unsubscribed"}

@router.post("/send-all")
async def send_all_podcasts(
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Manually trigger sending podcasts to all active subscriptions (admin only)"""
    try:
        await service.generate_and_send_podcasts()
        return {"message": "Podcast generation and sending initiated"}
    except Exception as e:
        logger.error(f"Failed to send podcasts: {e}")
        raise HTTPException(status_code=500, detail="Failed to send podcasts")