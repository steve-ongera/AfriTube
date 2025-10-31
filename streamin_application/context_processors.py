"""
Context Processors for AfriTube
Provides global data to all templates
"""

from django.db.models import Count
from .models import Category, User, Notification


def categories_processor(request):
    """
    Provide all active categories to templates
    """
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    return {
        'global_categories': categories,
    }


def user_data_processor(request):
    """
    Provide user-specific data to templates
    """
    context = {
        'unread_notifications_count': 0,
        'user_subscriptions': [],
        'is_creator': False,
    }
    
    if request.user.is_authenticated:
        # Unread notifications count
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # User subscriptions (creators they follow)
        from .models import Follow
        subscriptions = Follow.objects.filter(
            follower=request.user
        ).select_related('following').order_by('-created_at')[:10]
        
        context['user_subscriptions'] = [
            {
                'id': sub.following.id,
                'username': sub.following.username,
                'channel_name': sub.following.channel_name or sub.following.username,
                'profile_picture': sub.following.get_profile_picture_url(),
                'is_verified': sub.following.is_verified,
            }
            for sub in subscriptions
        ]
        
        context['is_creator'] = request.user.is_creator
    
    return context


def site_settings_processor(request):
    """
    Provide site-wide settings
    """
    return {
        'site_name': 'AfriTube',
        'site_tagline': 'Watch, Share & Earn',
        'enable_monetization': True,
        'enable_live_streams': True,
    }