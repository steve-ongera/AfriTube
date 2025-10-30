"""
Video Streaming Platform (AfriTube/EarnStream) - Django Models
Features: Free & Premium Videos, Live Streaming, Monetization, Social Features
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid


# ============================================================================
# USER MANAGEMENT
# ============================================================================

class User(AbstractUser):
    """Extended user model for platform"""
    USER_TYPE_CHOICES = [
        ('viewer', 'Viewer'),
        ('creator', 'Creator'),
        ('admin', 'Admin'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='viewer')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Social Auth
    google_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    
    # Creator specific
    is_creator = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    channel_name = models.CharField(max_length=200, blank=True)
    
    # Wallet & Earnings
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Info
    mpesa_number = models.CharField(max_length=15, blank=True)
    paypal_email = models.EmailField(blank=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True)
    
    # Statistics
    total_views = models.BigIntegerField(default=0)
    total_followers = models.IntegerField(default=0)
    total_following = models.IntegerField(default=0)
    
    # Settings
    allow_messages_from_followers = models.BooleanField(default=True)
    show_email_publicly = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    
    # Timestamps
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['user_type', 'is_creator']),
            models.Index(fields=['is_verified']),
        ]
    
    def get_profile_picture_url(self):
        """
        Returns the URL of the profile picture if uploaded,
        otherwise returns a default avatar URL.
        """
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        # Fallback avatar with username initials
        return f"https://ui-avatars.com/api/?name={self.username}"
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Follow(models.Model):
    """User following system"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# ============================================================================
# VIDEO CATEGORIES & TAGS
# ============================================================================

class Category(models.Model):
    """Video categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    thumbnail = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Video tags for better discovery"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'tags'
        ordering = ['-usage_count']
    
    def __str__(self):
        return self.name


# ============================================================================
# VIDEO MANAGEMENT
# ============================================================================

class Video(models.Model):
    """Main video model"""
    VIDEO_TYPE_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('pay_per_view', 'Pay Per View'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('published', 'Published'),
        ('unlisted', 'Unlisted'),
        ('private', 'Private'),
        ('removed', 'Removed'),
    ]
    
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('1440p', '1440p 2K'),
        ('2160p', '2160p 4K'),
    ]
    
    # Identification
    video_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=5000)
    
    # Creator
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    
    # Media Files
    video_file = models.FileField(
        upload_to='videos/%Y/%m/%d/',
        validators=[FileExtensionValidator(['mp4', 'mov', 'avi', 'mkv'])]
    )
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/')
    preview_gif = models.FileField(upload_to='previews/%Y/%m/%d/', null=True, blank=True)
    
    # Video Info
    duration = models.DurationField()  # in seconds
    file_size = models.BigIntegerField()  # in bytes
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='720p')
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    tags = models.ManyToManyField(Tag, related_name='videos', blank=True)
    
    # Monetization
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Settings
    allow_comments = models.BooleanField(default=True)
    allow_likes = models.BooleanField(default=True)
    allow_downloads = models.BooleanField(default=False)
    is_age_restricted = models.BooleanField(default=False)
    requires_login = models.BooleanField(default=False)
    
    # Statistics
    view_count = models.BigIntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    # Earnings
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    revenue_per_thousand_views = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'videos'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['video_id']),
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['video_type', 'status']),
            models.Index(fields=['-view_count']),
            models.Index(fields=['-published_at']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.creator.username}"


class VideoQuality(models.Model):
    """Multiple quality versions of same video"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='quality_versions')
    quality = models.CharField(max_length=10, choices=Video.QUALITY_CHOICES)
    video_file = models.FileField(upload_to='videos/qualities/%Y/%m/%d/')
    file_size = models.BigIntegerField()
    bitrate = models.IntegerField()  # kbps
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'video_qualities'
        unique_together = ['video', 'quality']
    
    def __str__(self):
        return f"{self.video.title} - {self.quality}"


# ============================================================================
# LIVE STREAMING
# ============================================================================

class LiveStream(models.Model):
    """Live streaming sessions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    STREAM_TYPE_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('private', 'Private'),
    ]
    
    # Identification
    stream_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    
    # Creator
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_streams')
    
    # Stream Details
    thumbnail = models.ImageField(upload_to='streams/thumbnails/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    stream_type = models.CharField(max_length=20, choices=STREAM_TYPE_CHOICES, default='free')
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Stream Info
    stream_key = models.CharField(max_length=200, unique=True)
    stream_url = models.URLField(blank=True)
    rtmp_url = models.URLField(blank=True)
    hls_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Schedule
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Settings
    allow_chat = models.BooleanField(default=True)
    allow_reactions = models.BooleanField(default=True)
    max_viewers = models.IntegerField(null=True, blank=True)  # null = unlimited
    
    # Statistics
    peak_viewers = models.IntegerField(default=0)
    current_viewers = models.IntegerField(default=0)
    total_viewers = models.IntegerField(default=0)
    chat_messages = models.IntegerField(default=0)
    reactions_count = models.IntegerField(default=0)
    
    # Monetization
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Recording
    is_recorded = models.BooleanField(default=True)
    recording_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'live_streams'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['status', '-scheduled_start']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.creator.username}"


class LiveStreamTicket(models.Model):
    """Tickets for premium live streams"""
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_tickets')
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=200)
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'live_stream_tickets'
        unique_together = ['stream', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.stream.title}"


class LiveStreamViewer(models.Model):
    """Track live stream viewers"""
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_views')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    watch_duration = models.DurationField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'live_stream_viewers'
        indexes = [
            models.Index(fields=['stream', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} watching {self.stream.title}"


class LiveStreamChat(models.Model):
    """Live stream chat messages"""
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='chats')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_messages')
    message = models.TextField(max_length=500)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'live_stream_chat'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


# ============================================================================
# ONE-TO-ONE VIDEO CALLS
# ============================================================================

class VideoCall(models.Model):
    """One-to-one video calls (premium feature)"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
    ]
    
    call_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator_calls')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewer_calls')
    
    # Call Details
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    duration_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Schedule
    scheduled_time = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Video Conference Details
    room_id = models.CharField(max_length=200, blank=True)
    join_url_creator = models.URLField(blank=True)
    join_url_viewer = models.URLField(blank=True)
    
    # Payment
    payment_status = models.CharField(max_length=20, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True)
    
    # Recording
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'video_calls'
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['viewer', 'status']),
        ]
    
    def __str__(self):
        return f"Call: {self.creator.username} <-> {self.viewer.username}"


# ============================================================================
# VIDEO ENGAGEMENT
# ============================================================================

class VideoView(models.Model):
    """Track video views for monetization"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='video_views')
    
    # View Details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    country = models.CharField(max_length=100, blank=True)
    
    # Watch Metrics
    watch_duration = models.DurationField()
    completion_percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Monetization
    is_monetized = models.BooleanField(default=False)
    earnings_generated = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Timestamps
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'video_views'
        indexes = [
            models.Index(fields=['video', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"View: {self.video.title} - {self.viewed_at}"


class VideoLike(models.Model):
    """Video likes/dislikes"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_videos')
    is_like = models.BooleanField(default=True)  # True=like, False=dislike
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'video_likes'
        unique_together = ['video', 'user']
        indexes = [
            models.Index(fields=['video', 'is_like']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {'liked' if self.is_like else 'disliked'} {self.video.title}"


class Comment(models.Model):
    """Video comments"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField(max_length=1000)
    like_count = models.IntegerField(default=0)
    
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} on {self.video.title}"


class CommentLike(models.Model):
    """Comment likes"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_likes'
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"{self.user.username} liked comment"


# ============================================================================
# PURCHASES & SUBSCRIPTIONS
# ============================================================================

class VideoPurchase(models.Model):
    """Track premium video purchases"""
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('paypal', 'PayPal'),
        ('stripe', 'Credit/Debit Card'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='purchases')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_videos')
    
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=200, unique=True)
    
    # M-Pesa specific
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    mpesa_phone = models.CharField(max_length=15, blank=True)
    
    # Status
    payment_status = models.CharField(max_length=20, default='completed')
    
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'video_purchases'
        unique_together = ['video', 'user']
        indexes = [
            models.Index(fields=['user', '-purchased_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} purchased {self.video.title}"


class Subscription(models.Model):
    """Creator subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    
    plan_name = models.CharField(max_length=100)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    auto_renew = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'subscriptions'
        unique_together = ['subscriber', 'creator']
    
    def __str__(self):
        return f"{self.subscriber.username} -> {self.creator.username}"


# ============================================================================
# MESSAGING SYSTEM
# ============================================================================

class Conversation(models.Model):
    """DM conversations between users"""
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_p1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_p2')
    
    last_message = models.TextField(max_length=200, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['participant1', 'participant2']),
        ]
    
    def __str__(self):
        return f"Chat: {self.participant1.username} <-> {self.participant2.username}"


class Message(models.Model):
    """Direct messages"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    content = models.TextField(max_length=2000)
    attachment = models.FileField(upload_to='messages/attachments/', null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_receiver = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username}"


# ============================================================================
# DOWNLOADS
# ============================================================================

class VideoDownload(models.Model):
    """Track video downloads"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    
    download_token = models.UUIDField(default=uuid.uuid4, unique=True)
    download_url = models.URLField()
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'video_downloads'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['download_token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} downloaded {self.video.title}"


# ============================================================================
# MONETIZATION & PAYMENTS
# ============================================================================

class EarningsRecord(models.Model):
    """Track creator earnings"""
    EARNINGS_TYPE_CHOICES = [
        ('video_view', 'Video View'),
        ('video_purchase', 'Video Purchase'),
        ('live_stream', 'Live Stream'),
        ('video_call', 'Video Call'),
        ('subscription', 'Subscription'),
        ('bonus', 'Bonus'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    earnings_type = models.CharField(max_length=20, choices=EARNINGS_TYPE_CHOICES)
    
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    currency = models.CharField(max_length=3, default='USD')
    
    # Reference
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, blank=True)
    live_stream = models.ForeignKey(LiveStream, on_delete=models.SET_NULL, null=True, blank=True)
    video_call = models.ForeignKey(VideoCall, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.CharField(max_length=200)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'earnings_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', '-created_at']),
            models.Index(fields=['earnings_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.creator.username} earned ${self.amount} from {self.earnings_type}"


class PayoutRequest(models.Model):
    """Creator payout requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    payout_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_requests')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Payment Details
    mpesa_number = models.CharField(max_length=15, blank=True)
    paypal_email = models.EmailField(blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    transaction_id = models.CharField(max_length=200, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payouts')
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payout_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['status', '-requested_at']),
        ]
    
    def __str__(self):
        return f"Payout {self.payout_id}: ${self.amount} to {self.creator.username}"


# ============================================================================
# PLAYLISTS & WATCH LATER
# ============================================================================

class Playlist(models.Model):
    """User playlists"""
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('unlisted', 'Unlisted'),
        ('private', 'Private'),
    ]
    
    playlist_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    thumbnail = models.ImageField(upload_to='playlists/', null=True, blank=True)
    
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    
    video_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'privacy']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.user.username}"


class PlaylistVideo(models.Model):
    """Videos in playlists"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='videos')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='in_playlists')
    position = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'playlist_videos'
        unique_together = ['playlist', 'video']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.video.title} in {self.playlist.title}"


class WatchLater(models.Model):
    """Watch later list"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_later')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watch_later_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watch_later'
        unique_together = ['user', 'video']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


class WatchHistory(models.Model):
    """User watch history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='in_history')
    
    last_position = models.DurationField(default=timedelta(seconds=0))
    watch_count = models.IntegerField(default=1)
    
    last_watched = models.DateTimeField(auto_now=True)
    first_watched = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watch_history'
        unique_together = ['user', 'video']
        ordering = ['-last_watched']
        indexes = [
            models.Index(fields=['user', '-last_watched']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('video_upload', 'New Video Upload'),
        ('live_stream', 'Live Stream Starting'),
        ('comment', 'New Comment'),
        ('comment_reply', 'Comment Reply'),
        ('like', 'Video Liked'),
        ('follow', 'New Follower'),
        ('message', 'New Message'),
        ('purchase', 'Video Purchase'),
        ('subscription', 'New Subscriber'),
        ('payout', 'Payout Update'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    
    # Related Objects
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
    live_stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    
    # Action URL
    action_url = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"


# ============================================================================
# REPORTING & MODERATION
# ============================================================================

class Report(models.Model):
    """Content reporting system"""
    REPORT_TYPE_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('copyright', 'Copyright Violation'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('misinformation', 'Misinformation'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('dismissed', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    # Reported Content
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='reports_against')
    live_stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    
    description = models.TextField(max_length=1000)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Review
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    review_notes = models.TextField(blank=True)
    action_taken = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['report_type', 'status']),
        ]
    
    def __str__(self):
        return f"Report: {self.report_type} by {self.reporter.username}"


# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

class VideoAnalytics(models.Model):
    """Daily video analytics"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    views = models.IntegerField(default=0)
    unique_viewers = models.IntegerField(default=0)
    watch_time_minutes = models.BigIntegerField(default=0)
    average_watch_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    earnings = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Traffic Sources
    direct_views = models.IntegerField(default=0)
    search_views = models.IntegerField(default=0)
    suggested_views = models.IntegerField(default=0)
    external_views = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'video_analytics'
        unique_together = ['video', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['video', '-date']),
        ]
    
    def __str__(self):
        return f"{self.video.title} - {self.date}"


class CreatorAnalytics(models.Model):
    """Daily creator analytics"""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    total_views = models.IntegerField(default=0)
    total_watch_time_minutes = models.BigIntegerField(default=0)
    new_followers = models.IntegerField(default=0)
    total_followers = models.IntegerField(default=0)
    
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    videos_published = models.IntegerField(default=0)
    live_streams = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'creator_analytics'
        unique_together = ['creator', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['creator', '-date']),
        ]
    
    def __str__(self):
        return f"{self.creator.username} - {self.date}"


# ============================================================================
# SYSTEM SETTINGS & CONFIGURATION
# ============================================================================

class SystemSettings(models.Model):
    """Platform-wide settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=500, blank=True)
    is_public = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name_plural = 'system settings'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class MonetizationRate(models.Model):
    """Dynamic monetization rates"""
    RATE_TYPE_CHOICES = [
        ('base_cpm', 'Base CPM (per 1000 views)'),
        ('engagement_bonus', 'Engagement Bonus'),
        ('premium_rate', 'Premium Content Rate'),
        ('platform_fee', 'Platform Fee Percentage'),
    ]
    
    rate_type = models.CharField(max_length=30, choices=RATE_TYPE_CHOICES, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=4)
    currency = models.CharField(max_length=3, default='USD')
    
    description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'monetization_rates'
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.rate_type}: {self.value}"


# ============================================================================
# CONTENT RECOMMENDATION
# ============================================================================

class UserPreference(models.Model):
    """Track user preferences for recommendations"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Favorite Categories
    favorite_categories = models.ManyToManyField(Category, related_name='favorited_by', blank=True)
    
    # Preferred creators
    preferred_creators = models.ManyToManyField(User, related_name='preferred_by', blank=True)
    
    # Settings
    auto_play = models.BooleanField(default=True)
    video_quality_preference = models.CharField(max_length=10, choices=Video.QUALITY_CHOICES, default='720p')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class VideoRecommendation(models.Model):
    """AI-generated video recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='recommended_to')
    
    score = models.DecimalField(max_digits=5, decimal_places=4)  # 0-1 relevance score
    reason = models.CharField(max_length=200)  # "Based on your watch history", "Trending in your region"
    
    is_shown = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    shown_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'video_recommendations'
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', '-score']),
            models.Index(fields=['video', 'is_clicked']),
        ]
    
    def __str__(self):
        return f"Recommend {self.video.title} to {self.user.username}"


# ============================================================================
# PREMIUM FEATURES & BADGES
# ============================================================================

class Badge(models.Model):
    """Creator badges and achievements"""
    BADGE_TYPE_CHOICES = [
        ('verified', 'Verified Creator'),
        ('milestone', 'Milestone Achievement'),
        ('quality', 'Quality Content'),
        ('trending', 'Trending Creator'),
        ('top_earner', 'Top Earner'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPE_CHOICES)
    description = models.TextField(max_length=500)
    icon = models.ImageField(upload_to='badges/')
    
    # Requirements
    min_followers = models.IntegerField(default=0)
    min_videos = models.IntegerField(default=0)
    min_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'badges'
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Badges earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='earned_by')
    
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_badges'
        unique_together = ['user', 'badge']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"