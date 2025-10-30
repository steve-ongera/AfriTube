from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('shorts/', views.shorts, name='shorts'),
    path('trending/', views.trending, name='trending'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('history/', views.history, name='history'),
    path('watch-later/', views.watch_later, name='watch_later'),
    path('liked-videos/', views.liked_videos, name='liked_videos'),
    path('live/', views.live_streams_view, name='live_streams'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('search/', views.search, name='search'),

    # Live Stream URLs
    path('stream/<uuid:stream_id>/', views.stream_detail, name='stream_detail'),
    path('stream/<uuid:stream_id>/join/', views.join_stream, name='join_stream'),
    path('stream/<uuid:stream_id>/leave/', views.leave_stream, name='leave_stream'),
    path('stream/<uuid:stream_id>/chat/', views.send_chat_message, name='send_chat_message'),
    path('stream/<uuid:stream_id>/purchase/', views.stream_purchase, name='stream_purchase'),

    # Video URLs
    path('video/<uuid:video_id>/', views.video_detail, name='video_detail'),
    path('video/<uuid:video_id>/like/', views.like_video, name='like_video'),
    path('video/<uuid:video_id>/comment/', views.add_comment, name='add_comment'),
    path('video/<uuid:video_id>/watch-later/', views.toggle_watch_later, name='toggle_watch_later'),
    path('video/<uuid:video_id>/purchase/', views.purchase_video, name='purchase_video'),

    # Download URLs
    path('video/<uuid:video_id>/download/', views.download_video, name='download_video'),
    path('download/<uuid:download_token>/', views.download_page, name='download_page'),
    path('download/<uuid:download_token>/initiate/', views.initiate_download, name='initiate_download'),
    path('downloads/', views.user_downloads, name='user_downloads'),
    path('video/<uuid:video_id>/new-download-link/', views.generate_new_download_link, name='generate_new_download_link'),

    # Channel URLs
    path('channel/<str:username>/', views.channel, name='channel'),
    path('channel/<str:username>/videos/', views.channel_videos, name='channel_videos'),
    path('channel/<str:username>/about/', views.channel_about, name='channel_about'),
    path('channel/<str:username>/edit/', views.channel_edit, name='channel_edit'),
    path('channel/<str:username>/follow/', views.follow_channel, name='follow_channel'),
]