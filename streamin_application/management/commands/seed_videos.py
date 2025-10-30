import os
import random
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db.models import Q
from streamin_application.models import Video


class Command(BaseCommand):
    help = 'Add or replace video files for existing Video objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-dir',
            type=str,
            default='D:/static/admin/Backup/CAMERA',
            help='Path to directory containing video files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of videos to process'
        )
        parser.add_argument(
            '--replace-existing',
            action='store_true',
            help='Replace existing video files even if they exist'
        )
        parser.add_argument(
            '--check-file-size',
            action='store_true',
            help='Only replace files smaller than a threshold (1MB)'
        )

    def handle(self, *args, **options):
        video_dir = options['video_dir']
        dry_run = options['dry_run']
        limit = options['limit']
        replace_existing = options['replace_existing']
        check_file_size = options['check_file_size']

        # Validate video directory
        if not os.path.exists(video_dir):
            self.stdout.write(
                self.style.ERROR(f'Video directory does not exist: {video_dir}')
            )
            return

        # Get all video files from directory
        video_files = self.get_video_files(video_dir)
        
        if not video_files:
            self.stdout.write(
                self.style.ERROR('No video files found in the specified directory')
            )
            return

        # Find videos that need video files
        videos_query = Video.objects.all()
        
        if not replace_existing:
            if check_file_size:
                # Only get videos with small or potentially placeholder files
                videos_query = videos_query.filter(
                    Q(video_file__isnull=True) | 
                    Q(video_file='') |
                    Q(file_size__lt=1048576)  # Less than 1MB (likely placeholder)
                )
            else:
                # Only get videos without proper files
                videos_query = videos_query.filter(
                    Q(video_file__isnull=True) | 
                    Q(video_file='')
                )

        total_videos = videos_query.count()
        
        if total_videos == 0:
            self.stdout.write(
                self.style.WARNING(
                    'All videos appear to have video files. '
                    'Use --replace-existing to replace all files or --check-file-size to check for small files.'
                )
            )
            return

        if limit:
            videos_query = videos_query[:limit]

        self.stdout.write(
            self.style.SUCCESS(
                f'Found {total_videos} videos to process. '
                f'Processing {len(videos_query)} videos with {len(video_files)} available video files...'
            )
        )

        # Process videos
        processed_count = 0
        successful_count = 0

        for video in videos_query:
            try:
                if processed_count >= len(video_files):
                    self.stdout.write(
                        self.style.WARNING('No more video files available in directory')
                    )
                    break

                video_file_path = video_files[processed_count]
                
                # Check if we should process this video
                if self.should_process_video(video, replace_existing, check_file_size):
                    result = self.add_video_file_to_video(video, video_file_path, dry_run)
                    
                    if result:
                        successful_count += 1
                        status = "Updated" if video.video_file else "Added"
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {status} video file to: {video.title}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Skipped: {video.title}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⏭ Skipped (has valid file): {video.title}')
                    )

                processed_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {video.title}: {str(e)}')
                )
                processed_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessing complete!\n'
                f'• Total processed: {processed_count}\n'
                f'• Successful: {successful_count}\n'
                f'• Remaining video files: {len(video_files) - processed_count}\n'
                f'• Remaining videos to process: {total_videos - successful_count}'
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN MODE: No changes were made to the database')
            )

    def get_video_files(self, video_dir):
        """Get all video files from directory"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        video_files = []

        for root, dirs, files in os.walk(video_dir):
            for file in files:
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in video_extensions):
                    full_path = os.path.join(root, file)
                    # Check file size to avoid tiny placeholder files
                    if os.path.getsize(full_path) > 1024:  # At least 1KB
                        video_files.append(full_path)

        # Shuffle to get random distribution
        random.shuffle(video_files)
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(video_files)} valid video files in directory')
        )
        
        return video_files

    def should_process_video(self, video, replace_existing, check_file_size):
        """Determine if a video should be processed"""
        if replace_existing:
            return True
            
        # Check if video has no file
        if not video.video_file or video.video_file.name == '':
            return True
            
        # Check for small files (likely placeholders)
        if check_file_size and hasattr(video, 'file_size'):
            return video.file_size < 1048576  # Less than 1MB
            
        # Check if file exists and is reasonable size
        try:
            if hasattr(video.video_file, 'path') and os.path.exists(video.video_file.path):
                actual_size = os.path.getsize(video.video_file.path)
                return actual_size < 1048576  # Less than 1MB
        except:
            pass
            
        return False

    def add_video_file_to_video(self, video, video_file_path, dry_run=False):
        """Add video file to existing Video object"""
        
        # Skip if video file doesn't exist
        if not os.path.exists(video_file_path):
            self.stdout.write(
                self.style.WARNING(f'Video file not found: {video_file_path}')
            )
            return False

        # Check file size
        file_size = os.path.getsize(video_file_path)
        if file_size < 1024:  # Less than 1KB
            self.stdout.write(
                self.style.WARNING(f'Video file too small (likely placeholder): {video_file_path}')
            )
            return False

        if dry_run:
            # Just show what would be done
            current_file = video.video_file.name if video.video_file else "None"
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would replace "{current_file}" with '
                    f'"{os.path.basename(video_file_path)}" for video: {video.title}'
                )
            )
            return True

        try:
            # Get current file info for logging
            current_file = video.video_file.name if video.video_file else "None"
            
            # Add the video file
            with open(video_file_path, 'rb') as f:
                video_file = File(f, name=os.path.basename(video_file_path))
                video.video_file = video_file
                video.save()

            # Update file_size field if it exists
            if hasattr(video, 'file_size'):
                video.file_size = file_size
                video.save(update_fields=['file_size'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Replaced "{current_file}" with "{os.path.basename(video_file_path)}"'
                )
            )

            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding video file to {video.title}: {str(e)}')
            )
            return False