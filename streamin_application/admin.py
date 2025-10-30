"""
AfriTube Admin Configuration
Comprehensive admin interface for platform management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from .models import *


# ============================================================================
# CUSTOM ADMIN ACTIONS
# ============================================================================

@admin.action(description='Approve selected items')
def approve_items(modeladmin, request, queryset):
    queryset.update(status='published')

@admin.action(description='Mark as verified')
def verify_users(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description='Ban selected users')
def ban_users(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.action(description='Process payouts')
def process_payouts(modeladmin, request, queryset):
    queryset.update(status='processing')


# ============================================================================
# INLINE ADMIN CLASSES
# ============================================================================

class VideoQualityInline(admin.TabularInline):
    model = VideoQuality
    extra = 1
    fields = ['quality', 'video_file', 'file_size', 'bitrate', 'is_default']
    readonly_fields = ['file_size']


class PlaylistVideoInline(admin.TabularInline):
    model = PlaylistVideo
    extra = 1
    fields = ['video', 'position']
    autocomplete_fields = ['video']


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0
    fields = ['badge', 'earned_at']
    readonly_fields = ['earned_at']


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'user_type', 'is_creator', 'is_verified',
        'total_followers', 'wallet_balance', 'total_earnings', 'date_joined'
    ]
    list_filter = [
        'user_type', 'is_creator', 'is_verified', 'is_active', 
        'is_staff', 'date_joined', 'country'
    ]
    search_fields = ['username', 'email', 'phone_number', 'channel_name']
    readonly_fields = [
        'date_joined', 'last_login', 'last_active', 'total_views',
        'total_followers', 'total_following', 'wallet_balance', 'total_earnings'
    ]
    
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'bio', 'country')
        }),
        ('User Type & Status', {
            'fields': ('user_type', 'is_creator', 'is_verified', 'channel_name')
        }),
        ('Social Auth', {
            'fields': ('google_id',),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('mpesa_number', 'paypal_email', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_views', 'total_followers', 'total_following', 'wallet_balance', 'total_earnings'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': (
                'allow_messages_from_followers', 'show_email_publicly', 
                'email_notifications'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'last_active', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [verify_users, ban_users]
    inlines = [UserBadgeInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            followers_count=Count('followers', distinct=True)
        )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['follower', 'following']


# ============================================================================
# CATEGORIES & TAGS
# ============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'display_order', 'video_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'display_order']
    
    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Total Videos'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'usage_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count']
    ordering = ['-usage_count']


# ============================================================================
# VIDEO MANAGEMENT
# ============================================================================

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'creator_link', 'category', 'video_type', 'status',
        'view_count', 'like_count', 'earnings_display', 'published_at'
    ]
    list_filter = [
        'status', 'video_type', 'category', 'quality', 
        'is_age_restricted', 'allow_comments', 'published_at'
    ]
    search_fields = ['title', 'description', 'creator__username', 'video_id']
    readonly_fields = [
        'video_id', 'view_count', 'like_count', 'dislike_count',
        'comment_count', 'download_count', 'share_count', 'earnings',
        'created_at', 'updated_at', 'video_preview', 'thumbnail_preview'
    ]
    autocomplete_fields = ['creator', 'category']
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video_id', 'title', 'slug', 'description', 'creator')
        }),
        ('Media Files', {
            'fields': ('video_file', 'video_preview', 'thumbnail', 'thumbnail_preview', 'preview_gif')
        }),
        ('Video Details', {
            'fields': ('duration', 'file_size', 'quality', 'category', 'tags')
        }),
        ('Monetization', {
            'fields': ('video_type', 'price', 'earnings', 'revenue_per_thousand_views')
        }),
        ('Status & Settings', {
            'fields': (
                'status', 'allow_comments', 'allow_likes', 
                'allow_downloads', 'is_age_restricted', 'requires_login'
            )
        }),
        ('Statistics', {
            'fields': (
                'view_count', 'like_count', 'dislike_count', 
                'comment_count', 'download_count', 'share_count'
            ),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [approve_items, 'feature_videos', 'remove_videos']
    inlines = [VideoQualityInline]
    
    def creator_link(self, obj):
        url = reverse('admin:app_user_change', args=[obj.creator.id])
        return format_html('<a href="{}">{}</a>', url, obj.creator.username)
    creator_link.short_description = 'Creator'
    
    def earnings_display(self, obj):
        return f"${obj.earnings:.2f}"
    earnings_display.short_description = 'Earnings'
    earnings_display.admin_order_field = 'earnings'
    
    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="320" height="240" controls>'
                '<source src="{}" type="video/mp4">'
                '</video>',
                obj.video_file.url
            )
        return "No video"
    video_preview.short_description = 'Video Preview'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="150" />', obj.thumbnail.url)
        return "No thumbnail"
    thumbnail_preview.short_description = 'Thumbnail'
    
    @admin.action(description='Feature selected videos')
    def feature_videos(self, request, queryset):
        # Custom logic to feature videos
        queryset.update(status='published')
    
    @admin.action(description='Remove selected videos')
    def remove_videos(self, request, queryset):
        queryset.update(status='removed')


@admin.register(VideoQuality)
class VideoQualityAdmin(admin.ModelAdmin):
    list_display = ['video', 'quality', 'file_size', 'bitrate', 'is_default']
    list_filter = ['quality', 'is_default']
    search_fields = ['video__title']
    autocomplete_fields = ['video']


# ============================================================================
# LIVE STREAMING
# ============================================================================

@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'creator', 'status', 'stream_type',
        'current_viewers', 'peak_viewers', 'scheduled_start', 'earnings_display'
    ]
    list_filter = ['status', 'stream_type', 'allow_chat', 'scheduled_start']
    search_fields = ['title', 'creator__username', 'stream_id']
    readonly_fields = [
        'stream_id', 'stream_key', 'current_viewers', 'peak_viewers',
        'total_viewers', 'chat_messages', 'reactions_count', 'earnings',
        'actual_start', 'actual_end', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['creator', 'category']
    date_hierarchy = 'scheduled_start'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('stream_id', 'title', 'description', 'creator', 'category')
        }),
        ('Stream Configuration', {
            'fields': (
                'thumbnail', 'stream_type', 'ticket_price',
                'stream_key', 'stream_url', 'rtmp_url', 'hls_url'
            )
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
        }),
        ('Status & Settings', {
            'fields': ('status', 'allow_chat', 'allow_reactions', 'max_viewers')
        }),
        ('Statistics', {
            'fields': (
                'current_viewers', 'peak_viewers', 'total_viewers',
                'chat_messages', 'reactions_count', 'earnings'
            ),
            'classes': ('collapse',)
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url'),
            'classes': ('collapse',)
        }),
    )
    
    def earnings_display(self, obj):
        return f"${obj.earnings:.2f}"
    earnings_display.short_description = 'Earnings'


@admin.register(LiveStreamTicket)
class LiveStreamTicketAdmin(admin.ModelAdmin):
    list_display = ['stream', 'user', 'price_paid', 'payment_method', 'purchased_at']
    list_filter = ['payment_method', 'purchased_at']
    search_fields = ['stream__title', 'user__username', 'transaction_id']
    readonly_fields = ['purchased_at']
    autocomplete_fields = ['stream', 'user']


@admin.register(LiveStreamViewer)
class LiveStreamViewerAdmin(admin.ModelAdmin):
    list_display = ['stream', 'user', 'is_active', 'joined_at', 'watch_duration']
    list_filter = ['is_active', 'joined_at']
    search_fields = ['stream__title', 'user__username']
    readonly_fields = ['joined_at', 'left_at', 'watch_duration']
    autocomplete_fields = ['stream', 'user']


@admin.register(LiveStreamChat)
class LiveStreamChatAdmin(admin.ModelAdmin):
    list_display = ['stream', 'user', 'message_preview', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['stream__title', 'user__username', 'message']
    readonly_fields = ['created_at']
    autocomplete_fields = ['stream', 'user']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


# ============================================================================
# VIDEO CALLS
# ============================================================================

@admin.register(VideoCall)
class VideoCallAdmin(admin.ModelAdmin):
    list_display = [
        'call_id', 'creator', 'viewer', 'status',
        'duration_minutes', 'price', 'scheduled_time', 'payment_status'
    ]
    list_filter = ['status', 'payment_status', 'scheduled_time']
    search_fields = ['creator__username', 'viewer__username', 'call_id']
    readonly_fields = [
        'call_id', 'started_at', 'ended_at', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['creator', 'viewer']
    date_hierarchy = 'scheduled_time'
    
    fieldsets = (
        ('Call Information', {
            'fields': ('call_id', 'creator', 'viewer', 'title', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('duration_minutes', 'price')
        }),
        ('Schedule', {
            'fields': ('scheduled_time', 'started_at', 'ended_at')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'transaction_id')
        }),
        ('Video Conference', {
            'fields': ('room_id', 'join_url_creator', 'join_url_viewer'),
            'classes': ('collapse',)
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# ENGAGEMENT
# ============================================================================

@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = [
        'video', 'user', 'watch_duration', 'completion_percentage',
        'is_monetized', 'earnings_generated', 'viewed_at'
    ]
    list_filter = ['is_monetized', 'viewed_at', 'country']
    search_fields = ['video__title', 'user__username', 'ip_address']
    readonly_fields = ['viewed_at']
    autocomplete_fields = ['video', 'user']
    date_hierarchy = 'viewed_at'


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    list_display = ['video', 'user', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at']
    search_fields = ['video__title', 'user__username']
    readonly_fields = ['created_at']
    autocomplete_fields = ['video', 'user']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'video', 'user', 'content_preview', 'like_count',
        'is_pinned', 'is_deleted', 'created_at'
    ]
    list_filter = ['is_pinned', 'is_deleted', 'created_at']
    search_fields = ['video__title', 'user__username', 'content']
    readonly_fields = ['like_count', 'created_at', 'updated_at']
    autocomplete_fields = ['video', 'user', 'parent']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


# ============================================================================
# PURCHASES & MONETIZATION
# ============================================================================

@admin.register(VideoPurchase)
class VideoPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'video', 'user', 'price_paid', 'payment_method',
        'payment_status', 'purchased_at'
    ]
    list_filter = ['payment_method', 'payment_status', 'purchased_at']
    search_fields = ['video__title', 'user__username', 'transaction_id']
    readonly_fields = ['purchased_at']
    autocomplete_fields = ['video', 'user']
    date_hierarchy = 'purchased_at'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'subscriber', 'creator', 'plan_name', 'monthly_price',
        'status', 'start_date', 'end_date', 'auto_renew'
    ]
    list_filter = ['status', 'auto_renew', 'start_date']
    search_fields = ['subscriber__username', 'creator__username', 'plan_name']
    readonly_fields = ['start_date']
    autocomplete_fields = ['subscriber', 'creator']
    date_hierarchy = 'start_date'


@admin.register(EarningsRecord)
class EarningsRecordAdmin(admin.ModelAdmin):
    list_display = [
        'creator', 'earnings_type', 'amount_display', 'currency',
        'description', 'created_at'
    ]
    list_filter = ['earnings_type', 'currency', 'created_at']
    search_fields = ['creator__username', 'description']
    readonly_fields = ['created_at']
    autocomplete_fields = ['creator', 'video', 'live_stream', 'video_call']
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        return f"${obj.amount:.4f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = [
        'payout_id', 'creator', 'amount', 'payment_method',
        'status', 'requested_at', 'processed_at'
    ]
    list_filter = ['status', 'payment_method', 'requested_at']
    search_fields = ['creator__username', 'payout_id', 'transaction_id']
    readonly_fields = ['payout_id', 'requested_at', 'processed_at']
    autocomplete_fields = ['creator', 'processed_by']
    date_hierarchy = 'requested_at'
    actions = [process_payouts]
    
    fieldsets = (
        ('Payout Information', {
            'fields': ('payout_id', 'creator', 'amount', 'payment_method')
        }),
        ('Payment Details', {
            'fields': ('mpesa_number', 'paypal_email', 'bank_account')
        }),
        ('Processing', {
            'fields': ('status', 'transaction_id', 'processed_by', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'processed_at')
        }),
    )


# ============================================================================
# MESSAGING
# ============================================================================

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'participant1', 'participant2', 'last_message_preview',
        'last_message_at', 'created_at'
    ]
    search_fields = ['participant1__username', 'participant2__username']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['participant1', 'participant2']
    
    def last_message_preview(self, obj):
        return obj.last_message[:30] + '...' if obj.last_message and len(obj.last_message) > 30 else obj.last_message
    last_message_preview.short_description = 'Last Message'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'sender', 'conversation', 'content_preview',
        'is_read', 'created_at'
    ]
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['created_at', 'read_at']
    autocomplete_fields = ['conversation', 'sender']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


# ============================================================================
# PLAYLISTS
# ============================================================================

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'privacy', 'video_count',
        'view_count', 'created_at'
    ]
    list_filter = ['privacy', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['playlist_id', 'video_count', 'view_count', 'created_at', 'updated_at']
    autocomplete_fields = ['user']
    inlines = [PlaylistVideoInline]


@admin.register(WatchLater)
class WatchLaterAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['added_at']
    autocomplete_fields = ['user', 'video']


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'video', 'watch_count', 'last_position',
        'last_watched'
    ]
    list_filter = ['last_watched']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['first_watched', 'last_watched']
    autocomplete_fields = ['user', 'video']


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'title', 'is_read',
        'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    autocomplete_fields = ['user', 'from_user', 'video', 'live_stream', 'comment']
    date_hierarchy = 'created_at'


# ============================================================================
# REPORTS & MODERATION
# ============================================================================

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'reporter', 'report_type', 'status', 'created_at',
        'reviewed_by', 'reviewed_at'
    ]
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['created_at', 'reviewed_at']
    autocomplete_fields = [
        'reporter', 'video', 'comment', 'user',
        'live_stream', 'reviewed_by'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'report_type', 'description')
        }),
        ('Reported Content', {
            'fields': ('video', 'comment', 'user', 'live_stream')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'action_taken')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'reviewed_at')
        }),
    )


# ============================================================================
# ANALYTICS
# ============================================================================

@admin.register(VideoAnalytics)
class VideoAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'video', 'date', 'views', 'unique_viewers',
        'watch_time_minutes', 'earnings'
    ]
    list_filter = ['date']
    search_fields = ['video__title']
    readonly_fields = ['date']
    autocomplete_fields = ['video']
    date_hierarchy = 'date'


@admin.register(CreatorAnalytics)
class CreatorAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'creator', 'date', 'total_views', 'new_followers',
        'earnings', 'videos_published'
    ]
    list_filter = ['date']
    search_fields = ['creator__username']
    readonly_fields = ['date']
    autocomplete_fields = ['creator']
    date_hierarchy = 'date'


# ============================================================================
# SYSTEM SETTINGS
# ============================================================================

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_public', 'updated_at', 'updated_by']
    list_filter = ['is_public', 'updated_at']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['updated_at']
    autocomplete_fields = ['updated_by']
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'


@admin.register(MonetizationRate)
class MonetizationRateAdmin(admin.ModelAdmin):
    list_display = [
        'rate_type', 'value', 'currency', 'is_active',
        'effective_from', 'effective_until'
    ]
    list_filter = ['rate_type', 'currency', 'is_active', 'effective_from']
    search_fields = ['rate_type', 'description']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'video_quality_preference', 'auto_play', 'updated_at'
    ]
    search_fields = ['user__username']
    readonly_fields = ['updated_at']
    autocomplete_fields = ['user']
    filter_horizontal = ['favorite_categories', 'preferred_creators']


@admin.register(VideoRecommendation)
class VideoRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'video', 'score', 'reason',
        'is_shown', 'is_clicked', 'created_at'
    ]
    list_filter = ['is_shown', 'is_clicked', 'created_at']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['created_at', 'shown_at', 'clicked_at']
    autocomplete_fields = ['user', 'video']


# ============================================================================
# BADGES
# ============================================================================

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'badge_type', 'min_followers', 'min_videos',
        'min_earnings', 'is_active'
    ]
    list_filter = ['badge_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = []


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge', 'earned_at']
    search_fields = ['user__username', 'badge__name']
    readonly_fields = ['earned_at']
    autocomplete_fields = ['user', 'badge']


# ============================================================================
# DOWNLOADS
# ============================================================================

@admin.register(VideoDownload)
class VideoDownloadAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'video', 'is_used', 'expires_at',
        'downloaded_at', 'created_at'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__username', 'video__title', 'download_token']
    readonly_fields = ['download_token', 'created_at', 'downloaded_at']
    autocomplete_fields = ['user', 'video']


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "AfriTube Administration"
admin.site.site_title = "AfriTube Admin Portal"
admin.site.index_title = "Welcome to AfriTube Administration"