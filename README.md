#  AfriTube - African Video Streaming & Monetization Platform

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Development-orange.svg)]()

> **AfriTube** (EarnStream) is a next-generation video streaming platform designed for African creators to share content, engage audiences, and earn money through multiple monetization channels.

##  Features

###  Content Creation & Management
- **Free & Premium Videos** - Upload public or paid content
- **Live Streaming** - Go live with real-time chat and reactions
- **Video Calls** - One-to-one premium video sessions with fans
- **Multiple Video Qualities** - 360p to 4K (2160p) support
- **Categories & Tags** - Organize content for easy discovery
- **Playlists** - Create and manage video collections

###  Monetization System
- **Pay-Per-View** - Charge for premium content
- **Creator Subscriptions** - Monthly subscriber revenue
- **Ad Revenue** - Earn from video views (CPM model)
- **Live Stream Tickets** - Paid access to exclusive streams
- **Video Call Bookings** - Premium one-on-one sessions
- **Multiple Payouts** - M-Pesa, PayPal, Bank Transfer

###  Social Features
- **Follow System** - Build audience connections
- **Comments & Replies** - Threaded discussions
- **Direct Messaging** - DM between followers
- **Live Chat** - Real-time stream interactions
- **Like/Dislike** - Video engagement
- **Share & Download** - Content distribution (when enabled)

###  Analytics & Insights
- **Creator Dashboard** - Track views, earnings, audience growth
- **Video Analytics** - Performance metrics per video
- **Traffic Sources** - See where viewers come from
- **Engagement Metrics** - Likes, comments, watch time
- **Revenue Reports** - Detailed earnings breakdown

###  Security & Moderation
- **Content Reporting** - Flag inappropriate content
- **User Verification** - Verified creator badges
- **Download Protection** - Secure, tokenized downloads
- **Age Restrictions** - Content rating system
- **Privacy Controls** - Public/Unlisted/Private videos

###  Smart Recommendations
- **AI-Powered Discovery** - Personalized video suggestions
- **Trending Algorithm** - Surface popular content
- **Category Preferences** - Customized content feeds
- **Watch History** - Resume where you left off

##  Tech Stack

### Backend
- **Django 4.2+** - Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching & session management
- **Celery** - Background task processing
- **Django REST Framework** - API endpoints

### Frontend (Recommended)
- **React.js / Next.js** - Modern UI framework
- **Tailwind CSS** - Utility-first styling
- **WebSockets** - Real-time features

### Media & Storage
- **AWS S3 / Google Cloud Storage** - Video storage
- **CloudFlare Stream / Mux** - Video CDN & streaming
- **FFmpeg** - Video processing & transcoding

### Payments
- **Safaricom Daraja API** - M-Pesa integration
- **Stripe** - Card payments
- **PayPal** - International payments

### Authentication
- **Django Allauth** - Social auth (Google, Facebook)
- **JWT** - API authentication

##  Prerequisites

Before you begin, ensure you have:

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend)
- FFmpeg (for video processing)
- AWS/GCP account (for storage)
- M-Pesa Developer Account
- Stripe Account
 
## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/afritube.git
cd afritube
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `.env` file:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/afritube

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=afritube-media
AWS_S3_REGION_NAME=us-east-1

# M-Pesa Configuration
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your-passkey
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback/

# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# PayPal
PAYPAL_CLIENT_ID=your-client-id
PAYPAL_SECRET=your-secret
PAYPAL_MODE=sandbox  # or 'live'

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret

# Video Streaming
CLOUDFLARE_STREAM_TOKEN=your-token
# or
MUX_TOKEN_ID=your-mux-id
MUX_TOKEN_SECRET=your-mux-secret

# Platform Settings
BASE_CPM_RATE=1.00  # $1 per 1000 views
PLATFORM_FEE_PERCENTAGE=20  # 20% platform fee
MIN_PAYOUT_AMOUNT=50.00  # Minimum $50 for payout
```

### 5. Database Setup

```bash
# Create database
createdb afritube

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (categories, settings)
python manage.py loaddata initial_data.json
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Start Development Server

```bash
# Start Django
python manage.py runserver

# In another terminal, start Celery worker
celery -A afritube worker -l info

# Start Celery beat (for scheduled tasks)
celery -A afritube beat -l info

# Start Redis (if not already running)
redis-server
```

Visit: `http://localhost:8000`

##  Project Structure

```
afritube/
├── accounts/              # User management, auth
├── videos/                # Video upload, management
├── streaming/             # Live streaming features
├── monetization/          # Payments, earnings, payouts
├── social/                # Comments, follows, messages
├── analytics/             # Statistics, insights
├── recommendations/       # AI recommendation engine
├── notifications/         # Real-time notifications
├── moderation/            # Reporting, content review
├── api/                   # REST API endpoints
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploads (temporary)
├── templates/             # HTML templates
├── afritube/              # Main project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
└── docker-compose.yml
```

##  Configuration

### Video Processing Settings

```python
# settings.py
VIDEO_UPLOAD_MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv']
VIDEO_QUALITIES = ['360p', '480p', '720p', '1080p', '1440p', '2160p']
DEFAULT_VIDEO_QUALITY = '720p'
```

### Monetization Configuration

```python
# Earnings per 1000 views
BASE_CPM_RATE = Decimal('1.00')

# Engagement bonuses
LIKE_BONUS = Decimal('0.001')
COMMENT_BONUS = Decimal('0.002')
SHARE_BONUS = Decimal('0.005')

# Platform fees
PLATFORM_FEE_PERCENTAGE = 20  # 20%
MIN_PAYOUT_AMOUNT = Decimal('50.00')
```

##  Usage Examples

### Upload Video (API)

```python
import requests

url = "http://localhost:8000/api/videos/upload/"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

files = {
    'video_file': open('my_video.mp4', 'rb'),
    'thumbnail': open('thumbnail.jpg', 'rb')
}

data = {
    'title': 'My Awesome Video',
    'description': 'Video description here',
    'category': 1,
    'video_type': 'free',  # or 'premium', 'pay_per_view'
    'price': 0,
    'tags': 'comedy,entertainment,viral'
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### Start Live Stream

```python
url = "http://localhost:8000/api/streams/create/"
data = {
    'title': 'Live Gaming Session',
    'description': 'Playing FIFA 24',
    'category': 5,
    'stream_type': 'free',
    'scheduled_start': '2025-10-31T18:00:00Z'
}

response = requests.post(url, headers=headers, json=data)
stream = response.json()

# Get stream key
stream_key = stream['stream_key']
rtmp_url = stream['rtmp_url']
```

### M-Pesa STK Push (Payment)

```python
from monetization.services import MpesaService

mpesa = MpesaService()
result = mpesa.stk_push(
    phone_number='254712345678',
    amount=500,
    account_reference='VIDEO_123',
    description='Premium Video Purchase'
)
```

##  Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test videos

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Open htmlcov/index.html
```

##  Deployment

### Using Docker

```bash
# Build and run
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL certificate (HTTPS)
- [ ] Configure production database
- [ ] Set up CDN for static files
- [ ] Configure email backend
- [ ] Set up monitoring (Sentry)
- [ ] Enable logging
- [ ] Set up automated backups
- [ ] Configure firewall rules
- [ ] Set up load balancer
- [ ] Enable CORS properly
- [ ] Configure CSP headers

### Recommended Hosting

- **Backend**: DigitalOcean, AWS EC2, Heroku
- **Database**: AWS RDS, DigitalOcean Managed PostgreSQL
- **Storage**: AWS S3, Google Cloud Storage
- **CDN**: CloudFlare, AWS CloudFront
- **Video**: CloudFlare Stream, Mux, AWS MediaConvert

##  Performance Optimization

### Database Optimization

```python
# Use select_related for foreign keys
videos = Video.objects.select_related('creator', 'category').all()

# Use prefetch_related for many-to-many
videos = Video.objects.prefetch_related('tags', 'likes').all()

# Database indexes (already in models)
# Add custom indexes as needed
```

### Caching Strategy

```python
from django.core.cache import cache

# Cache video metadata
def get_video(video_id):
    cache_key = f'video_{video_id}'
    video = cache.get(cache_key)
    
    if not video:
        video = Video.objects.get(id=video_id)
        cache.set(cache_key, video, timeout=3600)
    
    return video
```

##  Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write docstrings for all functions/classes
- Add unit tests for new features
- Update documentation

##  API Documentation

API documentation is available at:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

### Key Endpoints

```
# Authentication
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/google/
POST   /api/auth/refresh/

# Videos
GET    /api/videos/
POST   /api/videos/upload/
GET    /api/videos/{id}/
PUT    /api/videos/{id}/
DELETE /api/videos/{id}/
POST   /api/videos/{id}/like/
POST   /api/videos/{id}/comment/

# Live Streams
GET    /api/streams/
POST   /api/streams/create/
GET    /api/streams/{id}/
POST   /api/streams/{id}/start/
POST   /api/streams/{id}/end/
POST   /api/streams/{id}/chat/

# Monetization
GET    /api/earnings/
POST   /api/payout/request/
POST   /api/payments/mpesa/
POST   /api/payments/stripe/

# User Profile
GET    /api/users/{username}/
POST   /api/users/follow/{username}/
GET    /api/users/{username}/videos/
GET    /api/users/{username}/analytics/
```

##  Troubleshooting

### Common Issues

**Video upload fails:**
```bash
# Check file size limits
# Increase in settings.py:
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440000  # 2.5GB
```

**M-Pesa integration not working:**
```bash
# Verify credentials in .env
# Check callback URL is accessible
# Review Daraja API documentation
```

**Videos not streaming:**
```bash
# Check CDN configuration
# Verify video processing completed
# Check CloudFlare/Mux settings
```

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [https://docs.afritube.com](https://docs.afritube.com)
- **Email**: steveongera001@gmail.com
- **Discord**: [Join our community](https://discord.gg/afritube)
- **Twitter**: [@AfriTube](https://twitter.com/afritube)

##  Acknowledgments

- Safaricom Daraja API for M-Pesa integration
- Django community for the amazing framework
- All contributors and supporters

##  Roadmap

### Phase 1 - MVP (Q1 2025)
- [x] User authentication & profiles
- [x] Video upload & streaming
- [x] Basic monetization
- [ ] M-Pesa integration
- [ ] Mobile app (React Native)

### Phase 2 - Growth (Q2 2025)
- [ ] Live streaming
- [ ] Advanced analytics
- [ ] Creator tools
- [ ] Mobile optimization

### Phase 3 - Scale (Q3 2025)
- [ ] AI recommendations
- [ ] Multi-language support
- [ ] Advanced moderation
- [ ] Partnership program

### Phase 4 - Enterprise (Q4 2025)
- [ ] White-label solution
- [ ] API marketplace
- [ ] Advanced monetization
- [ ] Global expansion

---

**Made with Love By Steve Ongera for African Creators**

*Star ⭐ this repo if you find it useful!*