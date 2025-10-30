"""
AfriTube Views - Homepage and Video Listing
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from .models import *


def index(request):
    """
    Homepage view - Display videos with recommendations
    Similar to YouTube homepage
    """
    # Get filter parameters
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'trending')  # trending, latest, popular
    
    # Base queryset - only published videos
    videos = Video.objects.filter(
        status='published'
    ).select_related(
        'creator', 'category'
    ).prefetch_related('tags')
    
    # Filter by category
    if category_slug:
        videos = videos.filter(category__slug=category_slug)
    
    # Search functionality
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(creator__username__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Sorting
    if sort_by == 'trending':
        # Trending: Recent videos with high engagement
        week_ago = timezone.now() - timedelta(days=7)
        videos = videos.filter(published_at__gte=week_ago).order_by(
            '-view_count', '-like_count', '-published_at'
        )
    elif sort_by == 'latest':
        videos = videos.order_by('-published_at')
    elif sort_by == 'popular':
        videos = videos.order_by('-view_count', '-like_count')
    else:
        # Default: Mixed algorithm
        videos = videos.order_by('-published_at')
    
    # Get user-specific recommendations if logged in
    if request.user.is_authenticated:
        recommended_videos_qs = VideoRecommendation.objects.filter(
            user=request.user,
            is_shown=False
        ).select_related('video__creator', 'video__category').order_by('-score')[:10]
        
        # Extract IDs
        recommended_ids = [rec.pk for rec in recommended_videos_qs]
        
        # Update using filter
        VideoRecommendation.objects.filter(pk__in=recommended_ids).update(
            is_shown=True,
            shown_at=timezone.now()
        )
        
        recommended_videos = recommended_videos_qs  # pass to template

    
    # Pagination
    paginator = Paginator(videos, 24)  # 24 videos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = Category.objects.filter(is_active=True).order_by('display_order')
    
    # Get live streams
    live_streams = LiveStream.objects.filter(
        status='live'
    ).select_related('creator', 'category').order_by('-current_viewers')[:5]
    
    # Get trending tags
    trending_tags = Tag.objects.order_by('-usage_count')[:10]
    
    # Shorts (if you have short videos)
    shorts = Video.objects.filter(
        status='published',
        duration__lte=timedelta(seconds=60)
    ).order_by('-published_at')[:10]
    
    # Get user subscriptions if logged in
    subscribed_channels = []
    if request.user.is_authenticated:
        subscribed_channels = Follow.objects.filter(
            follower=request.user
        ).select_related('following')[:10]
    
    context = {
        'videos': page_obj,
        'recommended_videos': recommended_videos,
        'categories': categories,
        'live_streams': live_streams,
        'shorts': shorts,
        'trending_tags': trending_tags,
        'subscribed_channels': subscribed_channels,
        'active_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'index.html', context)


from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import LiveStream, LiveStreamViewer, LiveStreamChat

def stream_detail(request, stream_id):
    """Live stream detail page"""
    stream = get_object_or_404(
        LiveStream.objects.select_related('creator', 'category'),
        stream_id=stream_id
    )
    
    # Get chat messages
    chat_messages = LiveStreamChat.objects.filter(
        stream=stream,
        is_deleted=False
    ).select_related('user').order_by('created_at')[:100]
    
    # Get active viewers count
    active_viewers = LiveStreamViewer.objects.filter(
        stream=stream,
        is_active=True
    ).count()
    
    # Check if user has access to premium stream
    has_access = True
    if stream.stream_type == 'premium' and request.user.is_authenticated:
        has_access = stream.tickets.filter(user=request.user).exists()
    elif stream.stream_type == 'premium' and not request.user.is_authenticated:
        has_access = False
    
    # Get related streams
    related_streams = LiveStream.objects.filter(
        status__in=['live', 'scheduled'],
        category=stream.category
    ).exclude(stream_id=stream_id).select_related('creator')[:6]
    
    context = {
        'stream': stream,
        'chat_messages': chat_messages,
        'active_viewers': active_viewers,
        'has_access': has_access,
        'related_streams': related_streams,
        'page_title': f'{stream.title} - Live',
    }
    
    return render(request, 'stream_detail.html', context)

@login_required
def join_stream(request, stream_id):
    """Join a live stream (for premium/private streams)"""
    stream = get_object_or_404(LiveStream, stream_id=stream_id)
    
    # Check if user has access
    if stream.stream_type == 'premium':
        has_ticket = stream.tickets.filter(user=request.user).exists()
        if not has_ticket:
            return redirect('stream_purchase', stream_id=stream_id)
    
    # Create or update viewer record
    viewer, created = LiveStreamViewer.objects.get_or_create(
        stream=stream,
        user=request.user,
        defaults={'is_active': True}
    )
    
    if not created:
        viewer.is_active = True
        viewer.save()
    
    return redirect('stream_detail', stream_id=stream_id)

@login_required
def leave_stream(request, stream_id):
    """Leave a live stream"""
    stream = get_object_or_404(LiveStream, stream_id=stream_id)
    
    try:
        viewer = LiveStreamViewer.objects.get(stream=stream, user=request.user)
        viewer.is_active = False
        viewer.left_at = timezone.now()
        viewer.save()
    except LiveStreamViewer.DoesNotExist:
        pass
    
    return redirect('index')

@login_required
def send_chat_message(request, stream_id):
    """Send a chat message in live stream"""
    if request.method == 'POST':
        stream = get_object_or_404(LiveStream, stream_id=stream_id)
        message = request.POST.get('message', '').strip()
        
        if message and len(message) <= 500:
            LiveStreamChat.objects.create(
                stream=stream,
                user=request.user,
                message=message
            )
            
            # Update stream chat message count
            stream.chat_messages += 1
            stream.save()
    
    return redirect('stream_detail', stream_id=stream_id)


def shorts(request):
    """Short videos page (TikTok/YouTube Shorts style)"""
    shorts = Video.objects.filter(
        status='published',
        duration__lte=timedelta(seconds=60)
    ).select_related('creator').order_by('-published_at')
    
    paginator = Paginator(shorts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'shorts': page_obj,
    }
    
    return render(request, 'shorts.html', context)


def trending(request):
    """Trending videos page"""
    # Videos from last 7 days with high engagement
    week_ago = timezone.now() - timedelta(days=7)
    
    videos = Video.objects.filter(
        status='published',
        published_at__gte=week_ago
    ).select_related('creator', 'category').order_by(
        '-view_count', '-like_count', '-comment_count'
    )
    
    paginator = Paginator(videos, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'page_title': 'Trending',
    }
    
    return render(request, 'trending.html', context)


@login_required
def subscriptions(request):
    """User subscriptions feed"""
    # Get channels user follows
    following = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    # Get videos from followed creators
    videos = Video.objects.filter(
        status='published',
        creator_id__in=following
    ).select_related('creator', 'category').order_by('-published_at')
    
    paginator = Paginator(videos, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get subscribed channels
    subscribed_channels = Follow.objects.filter(
        follower=request.user
    ).select_related('following').order_by('-created_at')
    
    context = {
        'videos': page_obj,
        'subscribed_channels': subscribed_channels,
        'page_title': 'Subscriptions',
    }
    
    return render(request, 'subscriptions.html', context)


@login_required
def history(request):
    """User watch history"""
    from .models import WatchHistory
    
    history = WatchHistory.objects.filter(
        user=request.user
    ).select_related('video__creator', 'video__category').order_by('-last_watched')
    
    paginator = Paginator(history, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'history': page_obj,
        'page_title': 'Watch History',
    }
    
    return render(request, 'history.html', context)


@login_required
def watch_later(request):
    """User watch later list"""
    from .models import WatchLater
    
    watch_later_list = WatchLater.objects.filter(
        user=request.user
    ).select_related('video__creator', 'video__category').order_by('-added_at')
    
    paginator = Paginator(watch_later_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'watch_later': page_obj,
        'page_title': 'Watch Later',
    }
    
    return render(request, 'watch_later.html', context)


@login_required
def liked_videos(request):
    """User liked videos"""
    from .models import VideoLike
    
    liked = VideoLike.objects.filter(
        user=request.user,
        is_like=True
    ).select_related('video__creator', 'video__category').order_by('-created_at')
    
    paginator = Paginator(liked, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'liked_videos': page_obj,
        'page_title': 'Liked Videos',
    }
    
    return render(request, 'liked_videos.html', context)


def live_streams_view(request):
    """Live streams page"""
    live_streams = LiveStream.objects.filter(
        status='live'
    ).select_related('creator', 'category').order_by('-current_viewers')
    
    upcoming_streams = LiveStream.objects.filter(
        status='scheduled',
        scheduled_start__gte=timezone.now()
    ).select_related('creator', 'category').order_by('scheduled_start')
    
    context = {
        'live_streams': live_streams,
        'upcoming_streams': upcoming_streams,
        'page_title': 'Live Streams',
    }
    
    return render(request, 'live_streams.html', context)


def category_view(request, slug):
    """Category-specific page"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    videos = Video.objects.filter(
        status='published',
        category=category
    ).select_related('creator').order_by('-published_at')
    
    paginator = Paginator(videos, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'category': category,
        'page_title': category.name,
    }
    
    return render(request, 'category.html', context)


def search(request):
    """Search results page"""
    query = request.GET.get('q', '')
    
    if not query:
        return redirect('index')
    
    # Search videos
    videos = Video.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(creator__username__icontains=query) |
        Q(tags__name__icontains=query),
        status='published'
    ).select_related('creator', 'category').distinct()
    
    # Search channels
    channels = User.objects.filter(
        Q(username__icontains=query) |
        Q(channel_name__icontains=query) |
        Q(bio__icontains=query),
        is_creator=True
    ).order_by('-total_followers')[:10]
    
    paginator = Paginator(videos, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'channels': channels,
        'search_query': query,
        'page_title': f'Search results for "{query}"',
    }
    
    return render(request, 'search.html', context)


@login_required
def stream_purchase(request, stream_id):
    """Purchase access to premium stream"""
    stream = get_object_or_404(LiveStream, stream_id=stream_id)
    
    if stream.stream_type != 'premium':
        return redirect('stream_detail', stream_id=stream_id)
    
    # Check if already purchased
    if stream.tickets.filter(user=request.user).exists():
        return redirect('stream_detail', stream_id=stream_id)
    
    if request.method == 'POST':
        # Process payment here
        # For now, we'll just create a ticket
        LiveStreamTicket.objects.create(
            stream=stream,
            user=request.user,
            price_paid=stream.ticket_price,
            payment_method='manual',  # Replace with actual payment method
            transaction_id=f"TICKET_{uuid.uuid4().hex[:16].upper()}"
        )
        
        return redirect('stream_detail', stream_id=stream_id)
    
    context = {
        'stream': stream,
        'page_title': f'Purchase Access - {stream.title}',
    }
    
    return render(request, 'stream_purchase.html', context)


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from .models import Video, VideoView, VideoLike, Comment, WatchHistory, WatchLater, VideoPurchase

def video_detail(request, video_id):
    """Video detail page with player and comments"""
    video = get_object_or_404(
        Video.objects.select_related('creator', 'category')
                     .prefetch_related('tags', 'quality_versions'),
        video_id=video_id,
        status='published'
    )
    
    # Check if user has access to premium/PPV videos
    has_access = True
    if video.video_type in ['premium', 'pay_per_view'] and request.user.is_authenticated:
        if video.video_type == 'premium':
            # Check if user is subscribed to creator or has purchased
            has_access = request.user.subscriptions.filter(
                creator=video.creator, 
                status='active'
            ).exists()
        elif video.video_type == 'pay_per_view':
            has_access = VideoPurchase.objects.filter(
                video=video,
                user=request.user,
                payment_status='completed'
            ).exists()
    elif video.video_type in ['premium', 'pay_per_view'] and not request.user.is_authenticated:
        has_access = False
    
    # Get video views count
    view_count = VideoView.objects.filter(video=video).count()
    
    # Get comments with replies
    comments = Comment.objects.filter(
        video=video,
        parent__isnull=True,
        is_deleted=False
    ).select_related('user').prefetch_related('replies__user').order_by('-is_pinned', '-created_at')
    
    # Get related videos
    related_videos = Video.objects.filter(
        status='published',
        category=video.category
    ).exclude(video_id=video_id).select_related('creator').order_by('-view_count', '-published_at')[:12]
    
    # Check if user has liked/disliked the video
    user_like = None
    if request.user.is_authenticated:
        try:
            user_like = VideoLike.objects.get(video=video, user=request.user)
        except VideoLike.DoesNotExist:
            pass
    
    # Check if video is in watch later
    in_watch_later = False
    if request.user.is_authenticated:
        in_watch_later = WatchLater.objects.filter(
            video=video, 
            user=request.user
        ).exists()
    
    # Track view (only for authenticated users or unique IPs)
    if has_access:
        track_video_view(request, video)
    
    context = {
        'video': video,
        'view_count': view_count,
        'comments': comments,
        'related_videos': related_videos,
        'has_access': has_access,
        'user_like': user_like,
        'in_watch_later': in_watch_later,
        'page_title': f'{video.title} - AfriTube',
    }
    
    return render(request, 'video_detail.html', context)

def track_video_view(request, video):
    """Track video view for analytics"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Create view record
    VideoView.objects.create(
        video=video,
        user=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=user_agent,
        watch_duration=timezone.timedelta(seconds=0),  # Will be updated via JS
        completion_percentage=0,
        country=get_country_from_ip(ip_address)
    )
    
    # Update video view count
    video.view_count += 1
    video.save()
    
    # Update creator total views
    video.creator.total_views += 1
    video.creator.save()
    
    # Update watch history for authenticated users
    if request.user.is_authenticated:
        WatchHistory.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={'last_watched': timezone.now()}
        )

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_country_from_ip(ip):
    """Get country from IP address (simplified)"""
    # In production, use a service like GeoIP2
    return ''

@login_required
def like_video(request, video_id):
    """Like or dislike a video"""
    if request.method == 'POST':
        video = get_object_or_404(Video, video_id=video_id)
        action = request.POST.get('action')  # 'like' or 'dislike'
        
        # Remove existing like/dislike
        VideoLike.objects.filter(video=video, user=request.user).delete()
        
        if action in ['like', 'dislike']:
            VideoLike.objects.create(
                video=video,
                user=request.user,
                is_like=(action == 'like')
            )
            
            # Update video like/dislike counts
            video.like_count = VideoLike.objects.filter(video=video, is_like=True).count()
            video.dislike_count = VideoLike.objects.filter(video=video, is_like=False).count()
            video.save()
        
        return JsonResponse({
            'success': True,
            'like_count': video.like_count,
            'dislike_count': video.dislike_count
        })
    
    return JsonResponse({'success': False})

@login_required
def add_comment(request, video_id):
    """Add a comment to a video"""
    if request.method == 'POST':
        video = get_object_or_404(Video, video_id=video_id)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if content and len(content) <= 1000:
            parent = None
            if parent_id:
                try:
                    parent = Comment.objects.get(id=parent_id, video=video)
                except Comment.DoesNotExist:
                    pass
            
            comment = Comment.objects.create(
                video=video,
                user=request.user,
                parent=parent,
                content=content
            )
            
            # Update video comment count
            video.comment_count = Comment.objects.filter(video=video, is_deleted=False).count()
            video.save()
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'user_name': comment.user.username,
                'user_avatar': comment.user.get_profile_picture_url(),
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y'),
                'is_pinned': comment.is_pinned
            })
    
    return JsonResponse({'success': False})

@login_required
def toggle_watch_later(request, video_id):
    """Add/remove video from watch later"""
    if request.method == 'POST':
        video = get_object_or_404(Video, video_id=video_id)
        action = request.POST.get('action')  # 'add' or 'remove'
        
        if action == 'add':
            WatchLater.objects.get_or_create(user=request.user, video=video)
            added = True
        else:
            WatchLater.objects.filter(user=request.user, video=video).delete()
            added = False
        
        return JsonResponse({'success': True, 'added': added})
    
    return JsonResponse({'success': False})

@login_required
def purchase_video(request, video_id):
    """Purchase access to premium/PPV video"""
    video = get_object_or_404(Video, video_id=video_id)
    
    if video.video_type not in ['premium', 'pay_per_view']:
        return redirect('video_detail', video_id=video_id)
    
    # Check if already purchased
    if VideoPurchase.objects.filter(video=video, user=request.user).exists():
        return redirect('video_detail', video_id=video_id)
    
    if request.method == 'POST':
        # Process payment here
        # For now, we'll just create a purchase record
        VideoPurchase.objects.create(
            video=video,
            user=request.user,
            price_paid=video.price,
            payment_method='manual',  # Replace with actual payment method
            transaction_id=f"PURCHASE_{uuid.uuid4().hex[:16].upper()}"
        )
        
        return redirect('video_detail', video_id=video_id)
    
    context = {
        'video': video,
        'page_title': f'Purchase - {video.title}',
    }
    
    return render(request, 'video_purchase.html', context)


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import uuid
import os
from wsgiref.util import FileWrapper
import mimetypes

@login_required
def download_video(request, video_id):
    """Download video file with authentication and tracking"""
    video = get_object_or_404(
        Video.objects.select_related('creator'),
        video_id=video_id,
        status='published'
    )
    
    # Check if video allows downloads
    if not video.allow_downloads:
        raise PermissionDenied("This video does not allow downloads")
    
    # Check access for premium/PPV videos
    has_access = True
    if video.video_type in ['premium', 'pay_per_view']:
        if video.video_type == 'premium':
            has_access = request.user.subscriptions.filter(
                creator=video.creator, 
                status='active'
            ).exists()
        elif video.video_type == 'pay_per_view':
            has_access = VideoPurchase.objects.filter(
                video=video,
                user=request.user,
                payment_status='completed'
            ).exists()
        
        if not has_access:
            return redirect('purchase_video', video_id=video_id)
    
    # Generate download token
    download_token = str(uuid.uuid4())
    
    # Create download record
    download = VideoDownload.objects.create(
        video=video,
        user=request.user,
        download_token=download_token,
        download_url=video.video_file.url,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + timezone.timedelta(hours=24)
    )
    
    # Update download count
    video.download_count += 1
    video.save()
    
    # Redirect to download page with token
    return redirect('download_page', download_token=download_token)

def download_page(request, download_token):
    """Download page with actual file download"""
    download = get_object_or_404(
        VideoDownload.objects.select_related('video', 'video__creator'),
        download_token=download_token
    )
    
    # Check if download is valid and not expired
    if download.is_used:
        return render(request, 'download_error.html', {
            'error': 'This download link has already been used.',
            'video': download.video
        })
    
    if download.expires_at < timezone.now():
        return render(request, 'download_error.html', {
            'error': 'This download link has expired.',
            'video': download.video
        })
    
    # Check if user owns the download
    if request.user != download.user:
        raise PermissionDenied("You don't have permission to access this download")
    
    context = {
        'download': download,
        'video': download.video,
        'page_title': f'Download - {download.video.title}',
    }
    
    return render(request, 'download_video.html', context)

@login_required
def initiate_download(request, download_token):
    """Initiate actual file download"""
    download = get_object_or_404(
        VideoDownload,
        download_token=download_token,
        user=request.user
    )
    
    # Validate download
    if download.is_used:
        return JsonResponse({'success': False, 'error': 'Download link already used'})
    
    if download.expires_at < timezone.now():
        return JsonResponse({'success': False, 'error': 'Download link expired'})
    
    try:
        video_file = download.video.video_file
        file_path = video_file.path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return JsonResponse({'success': False, 'error': 'Video file not found'})
        
        # Mark download as used
        download.is_used = True
        download.downloaded_at = timezone.now()
        download.save()
        
        # Prepare file for download
        file_size = os.path.getsize(file_path)
        filename = f"{download.video.title.replace(' ', '_')}_{download.video.video_id}.mp4"
        
        # Create response with file
        response = HttpResponse(FileWrapper(open(file_path, 'rb')), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = file_size
        response['X-Accel-Redirect'] = f'/protected/{video_file.name}'  # For nginx
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def user_downloads(request):
    """User's download history"""
    downloads = VideoDownload.objects.filter(
        user=request.user
    ).select_related('video', 'video__creator').order_by('-created_at')
    
    paginator = Paginator(downloads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'downloads': page_obj,
        'page_title': 'My Downloads',
    }
    
    return render(request, 'user_downloads.html', context)

@login_required
def generate_new_download_link(request, video_id):
    """Generate new download link for a video"""
    video = get_object_or_404(Video, video_id=video_id, status='published')
    
    if not video.allow_downloads:
        return JsonResponse({'success': False, 'error': 'Video does not allow downloads'})
    
    # Check access
    has_access = True
    if video.video_type in ['premium', 'pay_per_view']:
        if video.video_type == 'premium':
            has_access = request.user.subscriptions.filter(
                creator=video.creator, 
                status='active'
            ).exists()
        elif video.video_type == 'pay_per_view':
            has_access = VideoPurchase.objects.filter(
                video=video,
                user=request.user,
                payment_status='completed'
            ).exists()
    
    if not has_access:
        return JsonResponse({'success': False, 'error': 'No access to this video'})
    
    # Generate new download token
    download_token = str(uuid.uuid4())
    
    download = VideoDownload.objects.create(
        video=video,
        user=request.user,
        download_token=download_token,
        download_url=video.video_file.url,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + timezone.timedelta(hours=24)
    )
    
    new_url = request.build_absolute_uri(f'/download/{download_token}/')
    
    return JsonResponse({
        'success': True,
        'download_url': new_url,
        'expires_at': download.expires_at.isoformat()
    })

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator

def channel(request, username):
    """Channel page for creators"""
    creator = get_object_or_404(
        User.objects.select_related('userpreference'),
        username=username,
        is_creator=True
    )
    
    # Get filter parameters
    content_type = request.GET.get('content', 'videos')  # videos, shorts, live, playlists
    sort_by = request.GET.get('sort', 'latest')
    search_query = request.GET.get('q', '')
    
    # Check if user is following this channel
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=creator
        ).exists()
    
    # Base videos queryset
    videos = Video.objects.filter(
        creator=creator,
        status='published'
    ).select_related('category').prefetch_related('tags')
    
    # Apply search filter
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    if sort_by == 'popular':
        videos = videos.order_by('-view_count', '-published_at')
    elif sort_by == 'oldest':
        videos = videos.order_by('published_at')
    else:  # latest
        videos = videos.order_by('-published_at')
    
    # Get different content types
    shorts = Video.objects.filter(
        creator=creator,
        status='published',
        duration__lte=timedelta(seconds=60)
    ).order_by('-published_at')[:20]
    
    live_streams = LiveStream.objects.filter(
        creator=creator,
        status__in=['live', 'scheduled']
    ).order_by('-scheduled_start')[:10]
    
    playlists = Playlist.objects.filter(
        user=creator,
        privacy='public'
    ).order_by('-created_at')
    
    # Get channel analytics
    total_views = videos.aggregate(total_views=Sum('view_count'))['total_views'] or 0
    total_videos = videos.count()
    total_likes = videos.aggregate(total_likes=Sum('like_count'))['total_likes'] or 0
    
    # Get channel join date (first video publish date or account creation)
    join_date = videos.aggregate(first_publish=Min('published_at'))['first_publish'] or creator.date_joined
    
    # Pagination for videos
    paginator = Paginator(videos, 24)
    page_number = request.GET.get('page')
    videos_page = paginator.get_page(page_number)
    
    # Get featured video (most viewed recent video)
    featured_video = videos.order_by('-view_count', '-published_at').first()
    
    context = {
        'creator': creator,
        'videos': videos_page,
        'shorts': shorts,
        'live_streams': live_streams,
        'playlists': playlists,
        'is_following': is_following,
        'content_type': content_type,
        'sort_by': sort_by,
        'search_query': search_query,
        'total_views': total_views,
        'total_videos': total_videos,
        'total_likes': total_likes,
        'join_date': join_date,
        'featured_video': featured_video,
        'page_title': f'{creator.channel_name or creator.username} - AfriTube',
    }
    
    return render(request, 'channel.html', context)

@login_required
def follow_channel(request, username):
    """Follow or unfollow a channel"""
    if request.method == 'POST':
        creator = get_object_or_404(User, username=username, is_creator=True)
        action = request.POST.get('action')  # 'follow' or 'unfollow'
        
        if action == 'follow':
            Follow.objects.get_or_create(follower=request.user, following=creator)
            # Update follower count
            creator.total_followers = Follow.objects.filter(following=creator).count()
            creator.save()
            followed = True
        else:
            Follow.objects.filter(follower=request.user, following=creator).delete()
            # Update follower count
            creator.total_followers = Follow.objects.filter(following=creator).count()
            creator.save()
            followed = False
        
        return JsonResponse({
            'success': True,
            'followed': followed,
            'follower_count': creator.total_followers
        })
    
    return JsonResponse({'success': False})

def channel_videos(request, username):
    """Channel videos page (alternative endpoint)"""
    return channel(request, username)

def channel_about(request, username):
    """Channel about page"""
    creator = get_object_or_404(User, username=username, is_creator=True)
    
    # Get channel statistics
    videos = Video.objects.filter(creator=creator, status='published')
    total_views = videos.aggregate(total_views=Sum('view_count'))['total_views'] or 0
    total_videos = videos.count()
    
    # Get join date
    join_date = videos.aggregate(first_publish=Min('published_at'))['first_publish'] or creator.date_joined
    
    # Get channel countries (top 5 from views)
    top_countries = VideoView.objects.filter(
        video__creator=creator
    ).values('country').annotate(
        views=Count('id')
    ).order_by('-views')[:5]
    
    context = {
        'creator': creator,
        'total_views': total_views,
        'total_videos': total_videos,
        'join_date': join_date,
        'top_countries': top_countries,
        'page_title': f'About {creator.channel_name or creator.username} - AfriTube',
    }
    
    return render(request, 'channel_about.html', context)

@login_required
def channel_edit(request, username):
    """Edit channel settings (creator only)"""
    if request.user.username != username or not request.user.is_creator:
        return redirect('channel', username=username)
    
    creator = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        # Update channel information
        channel_name = request.POST.get('channel_name', '').strip()
        bio = request.POST.get('bio', '').strip()
        country = request.POST.get('country', '')
        
        if channel_name:
            creator.channel_name = channel_name
        creator.bio = bio
        creator.country = country
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            creator.profile_picture = request.FILES['profile_picture']
        
        creator.save()
        
        return redirect('channel', username=username)
    
    context = {
        'creator': creator,
        'page_title': f'Channel Settings - {creator.channel_name or creator.username}',
    }
    
    return render(request, 'channel_edit.html', context)