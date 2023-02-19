from tempfile import NamedTemporaryFile
from typing import Tuple
from PIL import Image as PILImage
from django.contrib.auth.models import User
from images.models import Image
from tests.data.temp_users import TempUsers
from rest_framework.test import APIClient


class TempImages:
    UPLOAD_URL = '/api/upload'

    @staticmethod
    def generate_image(suffix: str, size: Tuple[int, int]) -> NamedTemporaryFile:
        image = PILImage.new('RGB', size)
        tmp_file = NamedTemporaryFile(suffix=suffix)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    @classmethod
    def populate_images(cls, api_client: APIClient):
        if not User.objects.filter(username=TempUsers.basic['username']):
            TempUsers.populate_users()

        for user in (TempUsers.basic, TempUsers.premium, TempUsers.enterprise):
            api_client.login(username=user['username'], password=user['password'])
            image = cls.generate_image('.png', (100, 100))
            api_client.post(cls.UPLOAD_URL, {'title': user['username'], 'image': image}, format='multipart')
            api_client.logout()
