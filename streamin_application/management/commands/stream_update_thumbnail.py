import os
import random
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db.models import Q
from streamin_application.models import LiveStream


class Command(BaseCommand):
    help = 'Add or replace thumbnails for LiveStream objects from image directory'

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
            help='Limit the number of live streams to process'
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
        parser.add_argument(
            '--status',
            type=str,
            choices=['scheduled', 'live', 'ended', 'cancelled', 'all'],
            default='all',
            help='Filter streams by status'
        )

    def handle(self, *args, **options):
        image_dir = options['image_dir']
        dry_run = options['dry_run']
        limit = options['limit']
        replace_existing = options['replace_existing']
        check_thumbnail_size = options['check_thumbnail_size']
        status_filter = options['status']

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

        # Find live streams that need thumbnails
        streams_query = LiveStream.objects.all()
        
        # Filter by status if specified
        if status_filter != 'all':
            streams_query = streams_query.filter(status=status_filter)
            self.stdout.write(
                self.style.INFO(f'Filtering streams by status: {status_filter}')
            )
        
        if not replace_existing:
            if check_thumbnail_size:
                # Only get streams with small or potentially placeholder thumbnails
                streams_query = streams_query.filter(
                    Q(thumbnail__isnull=True) | 
                    Q(thumbnail='') |
                    Q(thumbnail__endswith='default.jpg') |
                    Q(thumbnail__endswith='placeholder.png')
                )
            else:
                # Only get streams without proper thumbnails
                streams_query = streams_query.filter(
                    Q(thumbnail__isnull=True) | 
                    Q(thumbnail='')
                )

        total_streams = streams_query.count()
        
        if total_streams == 0:
            self.stdout.write(
                self.style.WARNING(
                    'All live streams appear to have thumbnails. '
                    'Use --replace-existing to replace all thumbnails.'
                )
            )
            return

        if limit:
            streams_query = streams_query[:limit]

        self.stdout.write(
            self.style.SUCCESS(
                f'Found {total_streams} live streams to process. '
                f'Processing {len(streams_query)} streams with {len(image_files)} available images...'
            )
        )

        # Process live streams
        processed_count = 0
        successful_count = 0

        for stream in streams_query:
            try:
                if processed_count >= len(image_files):
                    self.stdout.write(
                        self.style.WARNING('No more image files available in directory')
                    )
                    break

                image_file_path = image_files[processed_count]
                
                # Check if we should process this stream
                if self.should_process_stream(stream, replace_existing, check_thumbnail_size):
                    result = self.add_thumbnail_to_stream(stream, image_file_path, dry_run)
                    
                    if result:
                        successful_count += 1
                        status = "Updated" if stream.thumbnail else "Added"
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {status} thumbnail for: {stream.title} ({stream.status})')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Skipped: {stream.title}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⏭ Skipped (has valid thumbnail): {stream.title}')
                    )

                processed_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {stream.title}: {str(e)}')
                )
                processed_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nLive Stream Thumbnail update complete!\n'
                f'• Total processed: {processed_count}\n'
                f'• Successful: {successful_count}\n'
                f'• Remaining images: {len(image_files) - processed_count}\n'
                f'• Remaining streams to process: {total_streams - successful_count}'
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

    def should_process_stream(self, stream, replace_existing, check_thumbnail_size):
        """Determine if a live stream should be processed for thumbnail update"""
        if replace_existing:
            return True
            
        # Check if stream has no thumbnail
        if not stream.thumbnail or stream.thumbnail.name == '':
            return True
            
        # Check for common placeholder names
        if stream.thumbnail.name and any(placeholder in stream.thumbnail.name.lower() for placeholder in 
                                      ['default', 'placeholder', 'none', 'temp']):
            return True
            
        # Check for small thumbnails (likely placeholders)
        if check_thumbnail_size:
            try:
                if hasattr(stream.thumbnail, 'path') and os.path.exists(stream.thumbnail.path):
                    actual_size = os.path.getsize(stream.thumbnail.path)
                    return actual_size < 10240  # Less than 10KB (likely placeholder)
            except:
                pass
            
        return False

    def add_thumbnail_to_stream(self, stream, image_file_path, dry_run=False):
        """Add thumbnail image to existing LiveStream object"""
        
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
            current_thumbnail = stream.thumbnail.name if stream.thumbnail else "None"
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would replace "{current_thumbnail}" with '
                    f'"{os.path.basename(image_file_path)}" for stream: {stream.title}'
                )
            )
            return True

        try:
            # Get current thumbnail info for logging
            current_thumbnail = stream.thumbnail.name if stream.thumbnail else "None"
            
            # Add the thumbnail image
            with open(image_file_path, 'rb') as f:
                image_file = File(f, name=os.path.basename(image_file_path))
                stream.thumbnail = image_file
                stream.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Replaced "{current_thumbnail}" with "{os.path.basename(image_file_path)}"'
                )
            )

            return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding thumbnail to {stream.title}: {str(e)}')
            )
            return False