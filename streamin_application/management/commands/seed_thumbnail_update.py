import os
import random
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db.models import Q
from streamin_application.models import Video


class Command(BaseCommand):
    help = 'Add or replace thumbnails for Video objects from image directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--image-dir',
            type=str,
            default='D:/static/admin/Backup/CAMERA/photoz',
            help='Path to directory containing image files for thumbnails'
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
            help='Replace existing thumbnails even if they exist'
        )
        parser.add_argument(
            '--check-thumbnail-size',
            action='store_true',
            help='Only replace thumbnails smaller than a threshold (10KB)'
        )

    def handle(self, *args, **options):
        image_dir = options['image_dir']
        dry_run = options['dry_run']
        limit = options['limit']
        replace_existing = options['replace_existing']
        check_thumbnail_size = options['check_thumbnail_size']

        # Validate image directory
        if not os.path.exists(image_dir):
            self.stdout.write(
                self.style.ERROR(f'Image directory does not exist: {image_dir}')
            )
            return

        # Get all image files from directory
        image_files = self.get_image_files(image_dir)
        
        if not image_files:
            self.stdout.write(
                self.style.ERROR('No image files found in the specified directory')
            )
            return

        # Find videos that need thumbnails
        videos_query = Video.objects.all()
        
        if not replace_existing:
            if check_thumbnail_size:
                # Only get videos with small or potentially placeholder thumbnails
                videos_query = videos_query.filter(
                    Q(thumbnail__isnull=True) | 
                    Q(thumbnail='') |
                    Q(thumbnail__endswith='default.jpg') |
                    Q(thumbnail__endswith='placeholder.png')
                )
            else:
                # Only get videos without proper thumbnails
                videos_query = videos_query.filter(
                    Q(thumbnail__isnull=True) | 
                    Q(thumbnail='')
                )

        total_videos = videos_query.count()
        
        if total_videos == 0:
            self.stdout.write(
                self.style.WARNING(
                    'All videos appear to have thumbnails. '
                    'Use --replace-existing to replace all thumbnails.'
                )
            )
            return

        if limit:
            videos_query = videos_query[:limit]

        self.stdout.write(
            self.style.SUCCESS(
                f'Found {total_videos} videos to process. '
                f'Processing {len(videos_query)} videos with {len(image_files)} available images...'
            )
        )

        # Process videos
        processed_count = 0
        successful_count = 0

        for video in videos_query:
            try:
                if processed_count >= len(image_files):
                    self.stdout.write(
                        self.style.WARNING('No more image files available in directory')
                    )
                    break

                image_file_path = image_files[processed_count]
                
                # Check if we should process this video
                if self.should_process_video(video, replace_existing, check_thumbnail_size):
                    result = self.add_thumbnail_to_video(video, image_file_path, dry_run)
                    
                    if result:
                        successful_count += 1
                        status = "Updated" if video.thumbnail else "Added"
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {status} thumbnail for: {video.title}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Skipped: {video.title}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⏭ Skipped (has valid thumbnail): {video.title}')
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
                f'\nThumbnail update complete!\n'
                f'• Total processed: {processed_count}\n'
                f'• Successful: {successful_count}\n'
                f'• Remaining images: {len(image_files) - processed_count}\n'
                f'• Remaining videos to process: {total_videos - successful_count}'
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN MODE: No changes were made to the database')
            )

    def get_image_files(self, image_dir):
        """Get all image files from directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        image_files = []

        for root, dirs, files in os.walk(image_dir):
            for file in files:
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in image_extensions):
                    full_path = os.path.join(root, file)
                    # Check file size to avoid tiny placeholder images
                    if os.path.getsize(full_path) > 1024:  # At least 1KB
                        image_files.append(full_path)

        # Shuffle to get random distribution
        random.shuffle(image_files)
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(image_files)} valid image files in directory')
        )
        
        return image_files

    def should_process_video(self, video, replace_existing, check_thumbnail_size):
        """Determine if a video should be processed for thumbnail update"""
        if replace_existing:
            return True
            
        # Check if video has no thumbnail
        if not video.thumbnail or video.thumbnail.name == '':
            return True
            
        # Check for common placeholder names
        if video.thumbnail.name and any(placeholder in video.thumbnail.name.lower() for placeholder in 
                                      ['default', 'placeholder', 'none', 'temp']):
            return True
            
        # Check for small thumbnails (likely placeholders)
        if check_thumbnail_size:
            try:
                if hasattr(video.thumbnail, 'path') and os.path.exists(video.thumbnail.path):
                    actual_size = os.path.getsize(video.thumbnail.path)
                    return actual_size < 10240  # Less than 10KB (likely placeholder)
            except:
                pass
            
        return False

    def add_thumbnail_to_video(self, video, image_file_path, dry_run=False):
        """Add thumbnail image to existing Video object"""
        
        # Skip if image file doesn't exist
        if not os.path.exists(image_file_path):
            self.stdout.write(
                self.style.WARNING(f'Image file not found: {image_file_path}')
            )
            return False

        # Check file size and dimensions (basic validation)
        file_size = os.path.getsize(image_file_path)
        if file_size < 1024:  # Less than 1KB
            self.stdout.write(
                self.style.WARNING(f'Image file too small (likely placeholder): {image_file_path}')
            )
            return False

        if dry_run:
            # Just show what would be done
            current_thumbnail = video.thumbnail.name if video.thumbnail else "None"
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would replace "{current_thumbnail}" with '
                    f'"{os.path.basename(image_file_path)}" for video: {video.title}'
                )
            )
            return True

        try:
            # Get current thumbnail info for logging
            current_thumbnail = video.thumbnail.name if video.thumbnail else "None"
            
            # Add the thumbnail image
            with open(image_file_path, 'rb') as f:
                image_file = File(f, name=os.path.basename(image_file_path))
                video.thumbnail = image_file
                video.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Replaced "{current_thumbnail}" with "{os.path.basename(image_file_path)}"'
                )
            )

            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding thumbnail to {video.title}: {str(e)}')
            )
            return False