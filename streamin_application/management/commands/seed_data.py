"""
AfriTube Data Seeding Script
Run with: python manage.py seed_data

Place this file in: streamin_application/management/commands/seed_data.py
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from streamin_application.models import *

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample data for AfriTube platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create',
        )
        parser.add_argument(
            '--videos',
            type=int,
            default=200,
            help='Number of videos to create',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Seed in order of dependencies
        self.seed_categories()
        self.seed_tags()
        self.seed_badges()
        self.seed_system_settings()
        self.seed_monetization_rates()
        self.seed_users(options['users'])
        self.seed_follows()
        self.seed_videos(options['videos'])
        self.seed_video_qualities()
        self.seed_live_streams()
        self.seed_video_calls()
        self.seed_engagement()
        self.seed_purchases()
        self.seed_subscriptions()
        self.seed_playlists()
        self.seed_watch_history()
        self.seed_messages()
        self.seed_notifications()
        self.seed_reports()
        self.seed_analytics()
        self.seed_recommendations()
        self.seed_earnings()
        self.seed_payout_requests()
        
        self.stdout.write(self.style.SUCCESS('✅ Data seeding completed successfully!'))
        self.print_summary()

    def clear_data(self):
        """Clear all existing data"""
        models_to_clear = [
            VideoRecommendation, UserPreference, CreatorAnalytics, VideoAnalytics,
            Report, Notification, Message, Conversation, WatchHistory, WatchLater,
            PlaylistVideo, Playlist, PayoutRequest, EarningsRecord, Subscription,
            VideoPurchase, CommentLike, Comment, VideoLike, VideoView,
            VideoDownload, VideoCall, LiveStreamChat, LiveStreamViewer,
            LiveStreamTicket, LiveStream, VideoQuality, Video, UserBadge,
            Follow, Tag, Category, Badge, MonetizationRate, SystemSettings,
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'Deleted {count} {model.__name__} records')
        
        # Clear users except superusers
        User.objects.filter(is_superuser=False).delete()

    def seed_categories(self):
        """Seed video categories"""
        categories_data = [
            {'name': 'Music', 'icon': '🎵', 'description': 'Music videos and performances'},
            {'name': 'Comedy', 'icon': '😂', 'description': 'Funny videos and sketches'},
            {'name': 'Education', 'icon': '📚', 'description': 'Educational and tutorial content'},
            {'name': 'Gaming', 'icon': '🎮', 'description': 'Gaming videos and streams'},
            {'name': 'Sports', 'icon': '⚽', 'description': 'Sports highlights and analysis'},
            {'name': 'News', 'icon': '📰', 'description': 'News and current affairs'},
            {'name': 'Entertainment', 'icon': '🎬', 'description': 'Movies, TV shows, and entertainment'},
            {'name': 'Technology', 'icon': '💻', 'description': 'Tech reviews and tutorials'},
            {'name': 'Lifestyle', 'icon': '✨', 'description': 'Lifestyle and vlogs'},
            {'name': 'Cooking', 'icon': '🍳', 'description': 'Cooking and food videos'},
            {'name': 'Travel', 'icon': '✈️', 'description': 'Travel vlogs and guides'},
            {'name': 'Fashion', 'icon': '👗', 'description': 'Fashion and beauty content'},
            {'name': 'Fitness', 'icon': '💪', 'description': 'Workout and fitness videos'},
            {'name': 'Business', 'icon': '💼', 'description': 'Business and entrepreneurship'},
            {'name': 'Arts & Crafts', 'icon': '🎨', 'description': 'Art tutorials and DIY projects'},
        ]
        
        for idx, cat_data in enumerate(categories_data):
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'is_active': True,
                    'display_order': idx
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories_data)} categories'))

    def seed_tags(self):
        """Seed video tags"""
        tags_data = [
            'viral', 'trending', 'funny', 'tutorial', 'review', 'vlog', 'challenge',
            'reaction', 'unboxing', 'prank', 'diy', 'howto', 'tips', 'tricks',
            'live', 'gaming', 'music', 'dance', 'comedy', 'drama', 'action',
            'adventure', 'documentary', 'short', 'series', 'episode', 'season',
            'behind-the-scenes', 'bloopers', 'interview', 'podcast', 'news',
            'sports', 'highlights', 'analysis', 'commentary', 'motivation',
            'inspiration', 'education', 'learning', 'cooking', 'recipe',
            'travel', 'destination', 'culture', 'lifestyle', 'fashion',
            'beauty', 'makeup', 'fitness', 'workout', 'health', 'wellness'
        ]
        
        for tag_name in tags_data:
            Tag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'slug': slugify(tag_name),
                    'usage_count': random.randint(10, 1000)
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(tags_data)} tags'))

    def seed_badges(self):
        """Seed creator badges"""
        badges_data = [
            {
                'name': 'Verified Creator',
                'badge_type': 'verified',
                'description': 'Official verified creator badge',
                'min_followers': 1000,
                'min_videos': 10,
                'min_earnings': Decimal('100.00')
            },
            {
                'name': '10K Subscribers',
                'badge_type': 'milestone',
                'description': 'Reached 10,000 subscribers',
                'min_followers': 10000,
                'min_videos': 0,
                'min_earnings': Decimal('0.00')
            },
            {
                'name': '100K Subscribers',
                'badge_type': 'milestone',
                'description': 'Reached 100,000 subscribers',
                'min_followers': 100000,
                'min_videos': 0,
                'min_earnings': Decimal('0.00')
            },
            {
                'name': 'Quality Content Creator',
                'badge_type': 'quality',
                'description': 'Consistently high-quality content',
                'min_followers': 500,
                'min_videos': 50,
                'min_earnings': Decimal('500.00')
            },
            {
                'name': 'Trending Creator',
                'badge_type': 'trending',
                'description': 'Currently trending creator',
                'min_followers': 5000,
                'min_videos': 20,
                'min_earnings': Decimal('200.00')
            },
            {
                'name': 'Top Earner',
                'badge_type': 'top_earner',
                'description': 'Top earning creator',
                'min_followers': 1000,
                'min_videos': 30,
                'min_earnings': Decimal('5000.00')
            },
        ]
        
        for badge_data in badges_data:
            Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(badges_data)} badges'))

    def seed_system_settings(self):
        """Seed system settings"""
        settings_data = [
            {'key': 'platform_name', 'value': 'AfriTube', 'description': 'Platform name', 'is_public': True},
            {'key': 'base_cpm_rate', 'value': '1.00', 'description': 'Base CPM rate in USD', 'is_public': False},
            {'key': 'platform_fee_percentage', 'value': '20', 'description': 'Platform fee percentage', 'is_public': False},
            {'key': 'min_payout_amount', 'value': '50.00', 'description': 'Minimum payout amount', 'is_public': True},
            {'key': 'max_video_size_mb', 'value': '2048', 'description': 'Max video size in MB', 'is_public': True},
            {'key': 'allowed_video_formats', 'value': 'mp4,mov,avi,mkv', 'description': 'Allowed video formats', 'is_public': True},
            {'key': 'enable_downloads', 'value': 'true', 'description': 'Enable video downloads', 'is_public': True},
            {'key': 'enable_live_streaming', 'value': 'true', 'description': 'Enable live streaming', 'is_public': True},
            {'key': 'support_email', 'value': 'support@afritube.com', 'description': 'Support email', 'is_public': True},
        ]
        
        for setting_data in settings_data:
            SystemSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(settings_data)} system settings'))

    def seed_monetization_rates(self):
        """Seed monetization rates"""
        rates_data = [
            {
                'rate_type': 'base_cpm',
                'value': Decimal('1.0000'),
                'currency': 'USD',
                'description': 'Base rate per 1000 views',
                'effective_from': timezone.now() - timedelta(days=90)
            },
            {
                'rate_type': 'engagement_bonus',
                'value': Decimal('0.5000'),
                'currency': 'USD',
                'description': 'Bonus for high engagement',
                'effective_from': timezone.now() - timedelta(days=90)
            },
            {
                'rate_type': 'premium_rate',
                'value': Decimal('2.0000'),
                'currency': 'USD',
                'description': 'Premium content multiplier',
                'effective_from': timezone.now() - timedelta(days=90)
            },
            {
                'rate_type': 'platform_fee',
                'value': Decimal('20.0000'),
                'currency': 'USD',
                'description': 'Platform fee percentage',
                'effective_from': timezone.now() - timedelta(days=90)
            },
        ]
        
        for rate_data in rates_data:
            MonetizationRate.objects.get_or_create(
                rate_type=rate_data['rate_type'],
                defaults=rate_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(rates_data)} monetization rates'))

    def seed_users(self, count):
        """Seed users"""
        countries = ['Kenya', 'Nigeria', 'South Africa', 'Ghana', 'Tanzania', 'Uganda', 'Rwanda', 'Ethiopia']
        
        users_created = 0
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@afritube.com',
                password='admin123',
                user_type='admin',
                is_creator=True,
                is_verified=True
            )
            users_created += 1
        
        # Create regular users and creators
        for i in range(count):
            is_creator = random.choice([True, False, False])  # 33% creators
            user_type = 'creator' if is_creator else 'viewer'
            
            username = f'user_{i+1}_{random.randint(1000, 9999)}'
            
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='password123',
                user_type=user_type,
                is_creator=is_creator,
                is_verified=random.choice([True, False]) if is_creator else False,
                first_name=random.choice(['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'James', 'Lucy']),
                last_name=random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']),
                phone_number=f'+254{random.randint(700000000, 799999999)}',
                bio=f'Content creator and enthusiast from Africa' if is_creator else 'Video enthusiast',
                country=random.choice(countries),
                channel_name=f'{username.replace("_", " ").title()} Channel' if is_creator else '',
                wallet_balance=Decimal(random.uniform(0, 1000)) if is_creator else Decimal('0.00'),
                total_earnings=Decimal(random.uniform(0, 5000)) if is_creator else Decimal('0.00'),
                total_views=random.randint(0, 100000) if is_creator else 0,
                total_followers=random.randint(10, 50000) if is_creator else 0,
                total_following=random.randint(5, 500),
                mpesa_number=f'+254{random.randint(700000000, 799999999)}' if is_creator else '',
            )
            users_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {users_created} users'))

    def seed_follows(self):
        """Seed follow relationships"""
        users = list(User.objects.all())
        creators = list(User.objects.filter(is_creator=True))
        
        follows_created = 0
        for user in users[:30]:  # First 30 users follow some creators
            num_follows = random.randint(3, 15)
            creators_to_follow = random.sample(creators, min(num_follows, len(creators)))
            
            for creator in creators_to_follow:
                if user != creator:
                    Follow.objects.get_or_create(
                        follower=user,
                        following=creator
                    )
                    follows_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {follows_created} follow relationships'))

    def seed_videos(self, count):
        """Seed videos"""
        creators = list(User.objects.filter(is_creator=True))
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        
        if not creators:
            self.stdout.write(self.style.WARNING('No creators found, skipping videos'))
            return
        
        video_titles = [
            'Amazing Tutorial on {}',
            'Top 10 {} Tips',
            'How to Master {}',
            '{} Challenge Accepted',
            'Ultimate {} Guide',
            '{} in 2025: What You Need to Know',
            'My Journey with {}',
            '{} Review and Unboxing',
            'The Truth About {}',
            '{} Secrets Revealed'
        ]
        
        topics = [
            'Programming', 'Cooking', 'Gaming', 'Travel', 'Fitness',
            'Music Production', 'Photography', 'Business', 'Fashion', 'Tech'
        ]
        
        videos_created = 0
        for i in range(count):
            creator = random.choice(creators)
            category = random.choice(categories)
            
            title_template = random.choice(video_titles)
            topic = random.choice(topics)
            title = title_template.format(topic)
            
            video_type = random.choices(
                ['free', 'premium', 'pay_per_view'],
                weights=[70, 20, 10]
            )[0]
            
            price = Decimal('0.00')
            if video_type == 'premium':
                price = Decimal(random.uniform(2.99, 9.99))
            elif video_type == 'pay_per_view':
                price = Decimal(random.uniform(0.99, 4.99))
            
            video = Video.objects.create(
                title=title,
                slug=slugify(title) + f'-{uuid.uuid4().hex[:8]}',
                description=f'An amazing video about {topic.lower()}. ' + 
                           f'Learn everything you need to know about {topic.lower()} in this comprehensive guide. ' * 3,
                creator=creator,
                video_file=f'videos/sample_{i+1}.mp4',
                thumbnail=f'thumbnails/thumb_{i+1}.jpg',
                duration=timedelta(seconds=random.randint(180, 3600)),
                file_size=random.randint(50000000, 2000000000),
                quality=random.choice(['720p', '1080p', '1440p']),
                category=category,
                video_type=video_type,
                price=price,
                status=random.choice(['published', 'published', 'published', 'draft', 'unlisted']),
                allow_comments=True,
                allow_likes=True,
                allow_downloads=random.choice([True, False]),
                is_age_restricted=random.choice([False, False, False, True]),
                view_count=random.randint(100, 100000),
                like_count=random.randint(10, 10000),
                dislike_count=random.randint(0, 500),
                comment_count=random.randint(5, 1000),
                earnings=Decimal(random.uniform(5, 500)),
                published_at=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            
            # Add random tags
            video_tags = random.sample(tags, random.randint(3, 8))
            video.tags.set(video_tags)
            
            videos_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {videos_created} videos'))

    def seed_video_qualities(self):
        """Seed video quality versions"""
        videos = Video.objects.filter(status='published')[:50]  # First 50 videos
        qualities = ['360p', '480p', '720p', '1080p']
        
        qualities_created = 0
        for video in videos:
            for quality in qualities:
                VideoQuality.objects.get_or_create(
                    video=video,
                    quality=quality,
                    defaults={
                        'video_file': f'videos/qualities/{video.id}_{quality}.mp4',
                        'file_size': random.randint(30000000, 1000000000),
                        'bitrate': random.randint(1000, 8000),
                        'is_default': quality == '720p'
                    }
                )
                qualities_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {qualities_created} video quality versions'))

    def seed_live_streams(self):
        """Seed live streams"""
        creators = list(User.objects.filter(is_creator=True)[:20])
        categories = list(Category.objects.all())
        
        streams_created = 0
        for i in range(30):
            creator = random.choice(creators)
            category = random.choice(categories)
            
            scheduled_start = timezone.now() + timedelta(days=random.randint(-30, 30))
            
            stream = LiveStream.objects.create(
                title=f'Live Stream: {random.choice(["Gaming Session", "Q&A", "Tutorial", "Behind the Scenes", "Special Event"])}',
                description='Join me for an exciting live stream!',
                creator=creator,
                thumbnail=f'streams/thumbnails/stream_{i+1}.jpg',
                category=category,
                stream_type=random.choice(['free', 'premium', 'private']),
                ticket_price=Decimal(random.uniform(5, 50)) if random.choice([True, False]) else Decimal('0.00'),
                stream_key=f'stream_key_{uuid.uuid4().hex}',
                stream_url=f'https://stream.afritube.com/live/{uuid.uuid4().hex}',
                status=random.choice(['scheduled', 'live', 'ended']),
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_start + timedelta(hours=2),
                allow_chat=True,
                allow_reactions=True,
                peak_viewers=random.randint(10, 5000),
                current_viewers=random.randint(0, 1000),
                total_viewers=random.randint(50, 10000),
                earnings=Decimal(random.uniform(10, 1000))
            )
            streams_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {streams_created} live streams'))

    def seed_video_calls(self):
        """Seed video calls"""
        creators = list(User.objects.filter(is_creator=True)[:10])
        viewers = list(User.objects.filter(is_creator=False)[:20])
        
        calls_created = 0
        for i in range(20):
            creator = random.choice(creators)
            viewer = random.choice(viewers)
            
            scheduled_time = timezone.now() + timedelta(days=random.randint(-7, 30))
            
            VideoCall.objects.create(
                creator=creator,
                viewer=viewer,
                title=f'1-on-1 Call with {creator.username}',
                description='Personal video consultation',
                duration_minutes=random.choice([15, 30, 60]),
                price=Decimal(random.uniform(20, 100)),
                scheduled_time=scheduled_time,
                status=random.choice(['scheduled', 'completed', 'cancelled']),
                payment_status='completed',
                transaction_id=f'txn_{uuid.uuid4().hex[:16]}'
            )
            calls_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {calls_created} video calls'))

    def seed_engagement(self):
        """Seed video engagement (views, likes, comments)"""
        videos = list(Video.objects.filter(status='published'))
        users = list(User.objects.all())
        
        # Video Views
        views_created = 0
        for video in videos[:100]:
            num_views = random.randint(5, 50)
            for _ in range(num_views):
                user = random.choice(users) if random.choice([True, False]) else None
                VideoView.objects.create(
                    video=video,
                    user=user,
                    ip_address=f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    user_agent='Mozilla/5.0',
                    country=random.choice(['Kenya', 'Nigeria', 'South Africa', 'Ghana']),
                    watch_duration=timedelta(seconds=random.randint(30, int(video.duration.total_seconds()))),
                    completion_percentage=random.randint(10, 100),
                    is_monetized=True,
                    earnings_generated=Decimal(random.uniform(0.001, 0.01))
                )
                views_created += 1
        
        # Video Likes
        likes_created = 0
        for video in videos[:100]:
            num_likes = random.randint(2, 30)
            users_sample = random.sample(users, min(num_likes, len(users)))
            for user in users_sample:
                VideoLike.objects.get_or_create(
                    video=video,
                    user=user,
                    defaults={'is_like': random.choice([True, True, True, False])}
                )
                likes_created += 1
        
        # Comments
        comments_created = 0
        comment_texts = [
            'Great video! Thanks for sharing.',
            'This is amazing content!',
            'Very informative, learned a lot.',
            'Can you make more videos like this?',
            'Subscribed!',
            'First!',
            'Love your content ❤️',
            'This helped me so much!',
            'Best tutorial ever!',
            'More please!',
        ]
        
        for video in videos[:80]:
            num_comments = random.randint(1, 15)
            for _ in range(num_comments):
                user = random.choice(users)
                Comment.objects.create(
                    video=video,
                    user=user,
                    content=random.choice(comment_texts),
                    like_count=random.randint(0, 100)
                )
                comments_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {views_created} views, {likes_created} likes, {comments_created} comments'
        ))

    def seed_purchases(self):
        """Seed video purchases"""
        premium_videos = list(Video.objects.filter(video_type__in=['premium', 'pay_per_view']))
        users = list(User.objects.all())
        
        purchases_created = 0
        for video in premium_videos[:30]:
            num_purchases = random.randint(1, 20)
            users_sample = random.sample(users, min(num_purchases, len(users)))
            
            for user in users_sample:
                VideoPurchase.objects.get_or_create(
                    video=video,
                    user=user,
                    defaults={
                        'price_paid': video.price,
                        'payment_method': random.choice(['mpesa', 'paypal', 'stripe']),
                        'transaction_id': f'txn_{uuid.uuid4().hex[:16]}',
                        'payment_status': 'completed'
                    }
                )
                purchases_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {purchases_created} video purchases'))

    def seed_subscriptions(self):
        """Seed creator subscriptions"""
        creators = list(User.objects.filter(is_creator=True)[:20])
        users = list(User.objects.all())
        
        subscriptions_created = 0
        for creator in creators:
            num_subs = random.randint(5, 50)
            users_sample = random.sample(users, min(num_subs, len(users)))
            
            for user in users_sample:
                if user != creator:
                    Subscription.objects.get_or_create(
                        subscriber=user,
                        creator=creator,
                        defaults={
                            'plan_name': 'Monthly Subscription',
                            'monthly_price': Decimal(random.uniform(4.99, 19.99)),
                            'end_date': timezone.now() + timedelta(days=30),
                            'status': random.choice(['active', 'active', 'active', 'cancelled']),
                            'auto_renew': random.choice([True, False])
                        }
                    )
                    subscriptions_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {subscriptions_created} subscriptions'))

    def seed_playlists(self):
        """Seed playlists"""
        users = list(User.objects.all()[:30])
        videos = list(Video.objects.filter(status='published'))
        
        playlists_created = 0
        playlist_videos_created = 0
        
        for user in users:
            num_playlists = random.randint(1, 5)
            
            for i in range(num_playlists):
                playlist = Playlist.objects.create(
                    user=user,
                    title=f'{user.username}\'s Playlist #{i+1}',
                    description='My favorite videos',
                    privacy=random.choice(['public', 'private', 'unlisted']),
                    video_count=0,
                    view_count=random.randint(0, 1000)
                )
                playlists_created += 1
                
                # Add videos to playlist
                num_videos = random.randint(3, 15)
                playlist_videos = random.sample(videos, min(num_videos, len(videos)))
                
                for position, video in enumerate(playlist_videos):
                    PlaylistVideo.objects.create(
                        playlist=playlist,
                        video=video,
                        position=position
                    )
                    playlist_videos_created += 1
                
                playlist.video_count = len(playlist_videos)
                playlist.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {playlists_created} playlists with {playlist_videos_created} videos'
        ))

    def seed_watch_history(self):
        """Seed watch history"""
        users = list(User.objects.all()[:30])
        videos = list(Video.objects.filter(status='published'))
        
        history_created = 0
        for user in users:
            num_videos = random.randint(10, 50)
            user_videos = random.sample(videos, min(num_videos, len(videos)))
            
            for video in user_videos:
                WatchHistory.objects.get_or_create(
                    user=user,
                    video=video,
                    defaults={
                        'last_position': timedelta(seconds=random.randint(0, int(video.duration.total_seconds()))),
                        'watch_count': random.randint(1, 5)
                    }
                )
                history_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {history_created} watch history records'))

    def seed_messages(self):
        """Seed direct messages"""
        users = list(User.objects.all()[:20])
        
        conversations_created = 0
        messages_created = 0
        
        # Create conversations
        for i in range(30):
            user1, user2 = random.sample(users, 2)
            
            conversation, created = Conversation.objects.get_or_create(
                participant1=user1,
                participant2=user2,
                defaults={
                    'last_message': 'Hey, how are you?',
                    'last_message_at': timezone.now()
                }
            )
            
            if created:
                conversations_created += 1
                
                # Add messages to conversation
                num_messages = random.randint(3, 15)
                
                for j in range(num_messages):
                    sender = random.choice([user1, user2])
                    Message.objects.create(
                        conversation=conversation,
                        sender=sender,
                        content=random.choice([
                            'Hey! How are you doing?',
                            'Great video! Keep it up!',
                            'Thanks for the support!',
                            'When is your next stream?',
                            'Can we collaborate?',
                            'Love your content!',
                            'Check out my latest video!',
                            'Thanks! Appreciate it!',
                        ]),
                        is_read=random.choice([True, False])
                    )
                    messages_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {conversations_created} conversations with {messages_created} messages'
        ))

    def seed_notifications(self):
        """Seed notifications"""
        users = list(User.objects.all()[:30])
        videos = list(Video.objects.filter(status='published')[:50])
        
        notifications_created = 0
        
        notification_templates = [
            ('video_upload', 'New Video', '{} uploaded a new video: {}'),
            ('like', 'New Like', '{} liked your video: {}'),
            ('comment', 'New Comment', '{} commented on your video: {}'),
            ('follow', 'New Follower', '{} started following you'),
            ('subscription', 'New Subscriber', '{} subscribed to your channel'),
        ]
        
        for user in users:
            num_notifications = random.randint(5, 20)
            
            for _ in range(num_notifications):
                notif_type, title_template, message_template = random.choice(notification_templates)
                from_user = random.choice(users)
                video = random.choice(videos) if notif_type in ['video_upload', 'like', 'comment'] else None
                
                if notif_type == 'follow':
                    message = message_template.format(from_user.username)
                elif notif_type in ['subscription']:
                    message = message_template.format(from_user.username)
                else:
                    message = message_template.format(from_user.username, video.title if video else '')
                
                Notification.objects.create(
                    user=user,
                    notification_type=notif_type,
                    title=title_template,
                    message=message,
                    from_user=from_user,
                    video=video,
                    is_read=random.choice([True, False, False])
                )
                notifications_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {notifications_created} notifications'))

    def seed_reports(self):
        """Seed content reports"""
        users = list(User.objects.all()[:20])
        videos = list(Video.objects.filter(status='published')[:50])
        comments = list(Comment.objects.all()[:30])
        
        reports_created = 0
        
        for _ in range(50):
            reporter = random.choice(users)
            report_type = random.choice(['spam', 'inappropriate', 'copyright', 'harassment', 'other'])
            
            # Report either a video or comment
            if random.choice([True, False]):
                video = random.choice(videos)
                Report.objects.create(
                    reporter=reporter,
                    report_type=report_type,
                    video=video,
                    description=f'This video contains {report_type} content.',
                    status=random.choice(['pending', 'reviewed', 'action_taken', 'dismissed'])
                )
            else:
                comment = random.choice(comments)
                Report.objects.create(
                    reporter=reporter,
                    report_type=report_type,
                    comment=comment,
                    description=f'This comment is {report_type}.',
                    status=random.choice(['pending', 'reviewed', 'action_taken', 'dismissed'])
                )
            
            reports_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {reports_created} reports'))

    def seed_analytics(self):
        """Seed analytics data"""
        videos = list(Video.objects.filter(status='published')[:50])
        creators = list(User.objects.filter(is_creator=True)[:20])
        
        video_analytics_created = 0
        creator_analytics_created = 0
        
        # Video Analytics - Last 30 days
        for video in videos:
            for days_ago in range(30):
                date = timezone.now().date() - timedelta(days=days_ago)
                
                VideoAnalytics.objects.get_or_create(
                    video=video,
                    date=date,
                    defaults={
                        'views': random.randint(50, 1000),
                        'unique_viewers': random.randint(30, 800),
                        'watch_time_minutes': random.randint(100, 10000),
                        'average_watch_percentage': Decimal(random.uniform(30, 90)),
                        'likes': random.randint(5, 100),
                        'dislikes': random.randint(0, 10),
                        'comments': random.randint(2, 50),
                        'shares': random.randint(1, 30),
                        'earnings': Decimal(random.uniform(1, 50)),
                        'direct_views': random.randint(10, 300),
                        'search_views': random.randint(20, 400),
                        'suggested_views': random.randint(15, 250),
                        'external_views': random.randint(5, 50),
                    }
                )
                video_analytics_created += 1
        
        # Creator Analytics - Last 30 days
        for creator in creators:
            for days_ago in range(30):
                date = timezone.now().date() - timedelta(days=days_ago)
                
                CreatorAnalytics.objects.get_or_create(
                    creator=creator,
                    date=date,
                    defaults={
                        'total_views': random.randint(500, 5000),
                        'total_watch_time_minutes': random.randint(1000, 50000),
                        'new_followers': random.randint(0, 100),
                        'total_followers': creator.total_followers + random.randint(-50, 50),
                        'earnings': Decimal(random.uniform(10, 200)),
                        'videos_published': random.randint(0, 3),
                        'live_streams': random.randint(0, 2),
                    }
                )
                creator_analytics_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {video_analytics_created} video analytics and {creator_analytics_created} creator analytics'
        ))

    def seed_recommendations(self):
        """Seed video recommendations"""
        users = list(User.objects.all()[:30])
        videos = list(Video.objects.filter(status='published'))
        categories = list(Category.objects.all())
        
        preferences_created = 0
        recommendations_created = 0
        
        # User Preferences
        for user in users:
            preference, created = UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    'auto_play': random.choice([True, False]),
                    'video_quality_preference': random.choice(['720p', '1080p', '480p'])
                }
            )
            
            if created:
                preferences_created += 1
                
                # Add favorite categories
                fav_categories = random.sample(categories, random.randint(2, 5))
                preference.favorite_categories.set(fav_categories)
        
        # Video Recommendations
        for user in users:
            num_recommendations = random.randint(10, 30)
            recommended_videos = random.sample(videos, min(num_recommendations, len(videos)))
            
            reasons = [
                'Based on your watch history',
                'Trending in your region',
                'From creators you follow',
                'Popular in your favorite categories',
                'Recommended for you',
            ]
            
            for video in recommended_videos:
                VideoRecommendation.objects.create(
                    user=user,
                    video=video,
                    score=Decimal(random.uniform(0.5, 1.0)),
                    reason=random.choice(reasons),
                    is_shown=random.choice([True, False]),
                    is_clicked=random.choice([True, False, False, False])
                )
                recommendations_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {preferences_created} preferences and {recommendations_created} recommendations'
        ))

    def seed_earnings(self):
        """Seed earnings records"""
        creators = list(User.objects.filter(is_creator=True))
        videos = list(Video.objects.filter(status='published'))
        live_streams = list(LiveStream.objects.all())
        
        earnings_created = 0
        
        for creator in creators:
            num_earnings = random.randint(20, 100)
            
            for _ in range(num_earnings):
                earnings_type = random.choice([
                    'video_view', 'video_view', 'video_view',  # More common
                    'video_purchase', 'live_stream', 'subscription', 'bonus'
                ])
                
                amount = Decimal('0.0000')
                video = None
                live_stream = None
                description = ''
                
                if earnings_type == 'video_view':
                    video = random.choice(videos) if videos else None
                    amount = Decimal(random.uniform(0.001, 0.01))
                    description = f'Views on {video.title if video else "video"}'
                
                elif earnings_type == 'video_purchase':
                    video = random.choice(videos) if videos else None
                    amount = Decimal(random.uniform(2, 10))
                    description = f'Purchase of {video.title if video else "video"}'
                
                elif earnings_type == 'live_stream':
                    live_stream = random.choice(live_streams) if live_streams else None
                    amount = Decimal(random.uniform(10, 100))
                    description = f'Live stream earnings'
                
                elif earnings_type == 'subscription':
                    amount = Decimal(random.uniform(5, 20))
                    description = 'Monthly subscription'
                
                elif earnings_type == 'bonus':
                    amount = Decimal(random.uniform(5, 50))
                    description = 'Performance bonus'
                
                EarningsRecord.objects.create(
                    creator=creator,
                    earnings_type=earnings_type,
                    amount=amount,
                    currency='USD',
                    video=video,
                    live_stream=live_stream,
                    description=description
                )
                earnings_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {earnings_created} earnings records'))

    def seed_payout_requests(self):
        """Seed payout requests"""
        creators = list(User.objects.filter(is_creator=True, total_earnings__gte=50))
        
        payouts_created = 0
        
        for creator in creators[:20]:  # First 20 eligible creators
            num_payouts = random.randint(1, 5)
            
            for _ in range(num_payouts):
                amount = Decimal(random.uniform(50, min(float(creator.total_earnings), 1000)))
                payment_method = random.choice(['mpesa', 'paypal', 'bank_transfer'])
                
                payout_data = {
                    'creator': creator,
                    'amount': amount,
                    'payment_method': payment_method,
                    'status': random.choice(['pending', 'processing', 'completed', 'completed']),
                    'transaction_id': f'txn_{uuid.uuid4().hex[:16]}'
                }
                
                if payment_method == 'mpesa':
                    payout_data['mpesa_number'] = creator.mpesa_number
                elif payment_method == 'paypal':
                    payout_data['paypal_email'] = creator.paypal_email or f'{creator.username}@example.com'
                
                PayoutRequest.objects.create(**payout_data)
                payouts_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {payouts_created} payout requests'))

    def seed_watch_later(self):
        """Seed watch later list"""
        users = list(User.objects.all()[:30])
        videos = list(Video.objects.filter(status='published'))
        
        watch_later_created = 0
        
        for user in users:
            num_videos = random.randint(3, 15)
            user_videos = random.sample(videos, min(num_videos, len(videos)))
            
            for video in user_videos:
                WatchLater.objects.get_or_create(
                    user=user,
                    video=video
                )
                watch_later_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {watch_later_created} watch later items'))

    def seed_user_badges(self):
        """Assign badges to users"""
        creators = list(User.objects.filter(is_creator=True))
        badges = list(Badge.objects.all())
        
        badges_assigned = 0
        
        for creator in creators:
            # Assign badges based on creator stats
            eligible_badges = []
            
            for badge in badges:
                if (creator.total_followers >= badge.min_followers and
                    creator.videos.count() >= badge.min_videos and
                    creator.total_earnings >= badge.min_earnings):
                    eligible_badges.append(badge)
            
            # Assign some eligible badges
            if eligible_badges:
                badges_to_assign = random.sample(
                    eligible_badges, 
                    min(random.randint(1, 3), len(eligible_badges))
                )
                
                for badge in badges_to_assign:
                    UserBadge.objects.get_or_create(
                        user=creator,
                        badge=badge
                    )
                    badges_assigned += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {badges_assigned} badges to users'))

    def seed_video_downloads(self):
        """Seed video downloads"""
        users = list(User.objects.all()[:20])
        videos = list(Video.objects.filter(status='published', allow_downloads=True)[:50])
        
        downloads_created = 0
        
        for user in users:
            num_downloads = random.randint(1, 10)
            user_videos = random.sample(videos, min(num_downloads, len(videos)))
            
            for video in user_videos:
                VideoDownload.objects.create(
                    video=video,
                    user=user,
                    download_url=f'https://cdn.afritube.com/downloads/{uuid.uuid4().hex}',
                    ip_address=f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    user_agent='Mozilla/5.0',
                    expires_at=timezone.now() + timedelta(hours=24),
                    is_used=random.choice([True, False]),
                    downloaded_at=timezone.now() - timedelta(hours=random.randint(1, 12)) if random.choice([True, False]) else None
                )
                downloads_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {downloads_created} video downloads'))

    def print_summary(self):
        """Print summary of seeded data"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DATABASE SEEDING SUMMARY'))
        self.stdout.write('='*60)
        
        summary_data = [
            ('Users', User.objects.count()),
            ('Categories', Category.objects.count()),
            ('Tags', Tag.objects.count()),
            ('Videos', Video.objects.count()),
            ('Live Streams', LiveStream.objects.count()),
            ('Video Calls', VideoCall.objects.count()),
            ('Video Views', VideoView.objects.count()),
            ('Comments', Comment.objects.count()),
            ('Likes', VideoLike.objects.count()),
            ('Follows', Follow.objects.count()),
            ('Purchases', VideoPurchase.objects.count()),
            ('Subscriptions', Subscription.objects.count()),
            ('Playlists', Playlist.objects.count()),
            ('Messages', Message.objects.count()),
            ('Notifications', Notification.objects.count()),
            ('Reports', Report.objects.count()),
            ('Earnings Records', EarningsRecord.objects.count()),
            ('Payout Requests', PayoutRequest.objects.count()),
            ('Video Recommendations', VideoRecommendation.objects.count()),
            ('Badges', Badge.objects.count()),
            ('User Badges', UserBadge.objects.count()),
        ]
        
        for label, count in summary_data:
            self.stdout.write(f'{label:.<40} {count:>10}')
        
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('✅ All data seeded successfully!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('  • Access admin at: http://localhost:8000/admin/')
        self.stdout.write('  • Login with: admin / admin123')
        self.stdout.write('  • Test the platform with seeded data')
        self.stdout.write('='*60 + '\n')