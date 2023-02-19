import shutil
from typing import Dict
from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from hexOceanBackend.settings import STATIC_URL
from pathlib import Path
from users.permissions import Permissions
from PIL import Image as PILImage
from shutil import rmtree


def upload_to(self, _):
    return self.get_file_path()


class Image(models.Model):
    uuid = models.CharField(max_length=22, primary_key=True)
    title = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_to,
                              validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg'])])

    def get_file_extension(self) -> str:
        return self.image.name.split('.')[-1]

    def get_directory_path(self) -> Path:
        return Path(f'{STATIC_URL}{self.user.username}/{self.uuid}')

    def get_file_path(self, extension=None) -> Path:
        if extension is None:
            extension = self.get_file_extension()
        return self.get_directory_path().joinpath(Path(f'original.{extension}'))

    def get_thumbnail_file_path(self, size: int, extension=None) -> Path:
        # Performance: str.split() may be called multiple times
        if extension is None:
            extension = self.get_file_extension()
        return self.get_directory_path().joinpath(Path(f'thumbnail_{size}.{extension}'))

    def get_available_thumbnails(self) -> Dict[str, str]:
        extension = self.get_file_extension()
        original_path = self.get_file_path(extension)
        thumbnails = {}

        for thumbnail_size in Permissions.iter_allowed_thumbnail_sizes(self.user):
            thumbnail_path = self.get_thumbnail_file_path(thumbnail_size, extension)
            if not thumbnail_path.exists():
                self.create_thumbnail(original_path, thumbnail_path, thumbnail_size)

            # TODO: Make a link to static file
            thumbnails[f"{thumbnail_size}px"] = f'thumbnail_path{thumbnail_size}.link'

        return thumbnails

    @staticmethod
    def create_thumbnail(original_path: Path, thumbnail_path: Path, size: int) -> None:
        image = PILImage.open(original_path)

        width, height = image.size
        scale = height / size
        new_size = (int(width // scale), size)

        thumbnail = image.resize(new_size)
        thumbnail.save(thumbnail_path)

    def delete_files(self):
        shutil.rmtree(self.get_directory_path())
