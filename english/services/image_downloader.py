import asyncio
import io
import aiohttp

from PIL import Image
from django.core.files.base import ContentFile


class ImageDownloader:
    def __init__(self):
        
        self.MAX_IMAGES_PARALLEL_DOWNLOAD = 6
        self.MAX_IMAGE_SIZE = 2 * 1024 * 1024
        self.TIMEOUT = aiohttp.ClientTimeout(
            total=8,
            connect=2
        )
    
    def download_images(self, urls: dict) -> dict:
        """
        Синхронная оболочка для вызова ._download_all()
        """
        
        return asyncio.run(
            self._download_all(urls=urls)
        )
    
    async def _download_all(self, urls: dict) -> dict:
        
        semaphore = asyncio.Semaphore(self.MAX_IMAGES_PARALLEL_DOWNLOAD)
        
        async with aiohttp.ClientSession(
            timeout=self.TIMEOUT
        ) as session:
            
            keys = list(urls.keys())
            tasks = []
            
            for key in keys:
                tasks.append(
                    self._download_one(
                        session,
                        semaphore,
                        urls[key]
                    )
                )
            
            files = await asyncio.gather(*tasks)
        
        return dict(
            zip(keys,files)
        )
    
    async def _download_one(
            self,
            session: aiohttp.ClientSession,
            semaphore: asyncio.Semaphore,
            url: str
        ) -> ContentFile | None:
        """
        
        Метод для запроса загрузки каждого изображения
        В методе определяется, было ли успешно загружено изображение
        В неуспешном случае - return None (о котором подробнее ниже, в этом же комментарии)
        
        Изображение не получено
        В дальнейшем, от этого результата будет выставлено 
        placeholder-изображение (стандартное изображение):
        return None
        """
        
        async with semaphore:
            try:
                
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    if not response.headers.get("Content-Type", ""):
                        return None
                    
                    # Пытаемся прочесть на один байт больше максимального размера
                    # Если файл больше self.MAX_IMAGE_SIZE, 
                    # то добавленный байт будет свидетельством о том, что файл действительно больше разрешенного
                    content = await response.content.read(
                        self.MAX_IMAGE_SIZE + 1
                    )
                    
                    if len(content) > self.MAX_IMAGE_SIZE:
                        return None
                
                # Проверка на то, что сказанные байты являются изображением
                # через pil удобнее
                # Если возникнет ошибка, нижележащее исключение 
                # отработает и всёравно будет возвращено None
                Image.open(io.BytesIO(content)).verify()
                
            except Exception:
                return None
        
        return ContentFile(content=content)