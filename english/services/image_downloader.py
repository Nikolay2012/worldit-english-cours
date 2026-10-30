"""
Загрузчик изображений по ссылкам

Используется при импорте заданий из csv,
где у слова могут быть указаны ссылки на изображения

Ссылка в csv может быть двух видов:
-прямая ссылка на изображение - изображение скачивается сразу
-ссылка на страницу сайта с иконкой (HTML) - на странице ищется тег изображения
по селектору IMAGE_SELECTOR, и изображение скачивается уже по ссылке из этого тега

Ссылка из HTML-страницы принимается, только если её домен есть в ALLOWED_IMAGE_HOSTS
Так сервер не ходит по чужим адресам, подставленным в страницу

Изображения скачиваются параллельно через aiohttp, в одной сессии,
но не больше MAX_IMAGES_PARALLEL_DOWNLOAD одновременно (через Semaphore)

Метод .download_images() - синхронный,
чтобы его можно было вызвать из обычного кода Django,
внутри он запускает асинхронную загрузку через asyncio.run()

На входе - словарь {ключ: ссылка},
на выходе - словарь {тот же ключ: файл изображения или None}

Ответ читается по частям - метод ._read_limited()
Если ответ больше лимита (MAX_HTML_SIZE для страницы, MAX_IMAGE_SIZE для изображения),
чтение сразу прекращается

Изображение не загружается (будет None), если:
-ссылка пустая или сервер не ответил за отведённое время (TIMEOUT)
-сервер вернул статус не 200
-ответ не изображение и не HTML-страница
-на странице нет тега изображения или у тега пустой src
-домен ссылки из страницы не входит в ALLOWED_IMAGE_HOSTS
-страница больше MAX_HTML_SIZE или изображение больше MAX_IMAGE_SIZE
-файл не является изображением (проверка через Pillow)

Вместо None в дальнейшем выставляется placeholder-изображение,
потому ошибки загрузки не останавливают импорт задания
"""

import asyncio
import io
from urllib.parse import urljoin, urlparse
import aiohttp

from PIL import Image
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile


class ImageDownloader:
    def __init__(self):
        
        # Ограничеие для семафора
        # Может производится загрузка только трех изображений одновременно
        self.MAX_IMAGES_PARALLEL_DOWNLOAD = 4
        
        # При загрузке изображений, для заданий, 
        # стоит ограничение на размер изображения в 2 МБ
        self.MAX_IMAGE_SIZE = 2 * 1024 * 1024
        
        # При загрузке HTML-страницы с изображением, 
        # стоит ограничение на размер страницы в 2 МБ
        self.MAX_HTML_SIZE = 2 * 1024 * 1024
        
        self.TIMEOUT = aiohttp.ClientTimeout(
            total=15,
            connect=5
        )
        
        # Уникальный селектор изображений на сайте magnific
        # Используется при парсе HTML страницы, адрес которой указан в csv для задания "слова"
        self.IMAGE_SELECTOR = '[data-cy="resource-detail-preview"] img'
        
        # 
        self.ALLOWED_IMAGE_HOSTS = ["cdn-icons-png.magnific.com"]
    
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
                image_url = await self._find_image_url(session=session, page_url=url)
                
                if image_url is None:
                    return None
                
                return await self._read_image(
                    session=session, 
                    image_url=image_url
                )
                
            except Exception:
                return None
    
    async def _read_image(
            self, 
            session: aiohttp.ClientSession, 
            image_url: str
        ) -> ContentFile | None:
        
        async with session.get(image_url) as response:
            
            if response.status != 200:
                return None
            
            if not response.headers.get("Content-Type", "").startswith("image/"):
                return None
            
            content = await self._read_limited(
                response=response,
                max_size=self.MAX_IMAGE_SIZE
            )
        
        if content is None:
            return None
        
        # Проверка на то, что сказанные байты являются изображением
        # через pil удобнее
        # Если возникнет ошибка, нижележащее исключение 
        # отработает и всёравно будет возвращено None
        Image.open(io.BytesIO(content)).verify()
        
        return ContentFile(content=content)
    
    async def _find_image_url(
            self, 
            session: aiohttp.ClientSession, 
            page_url: str
        ) -> str | None:
        
        async with session.get(page_url) as response:
            
            if response.status != 200:
                return None
            
            content_type = response.headers.get("Content-Type", "")
            
            if content_type.startswith("image/"):
                return page_url
            
            if not content_type.startswith("text/html"):
                return None
            
            html = await self._read_limited(
                response=response,
                max_size=self.MAX_HTML_SIZE
            )
        
        if html is None:
            return None
        
        # Отбираем тег изображения по указанному в self.IMAGE_SELECTOR селектору
        image = BeautifulSoup(html, "html.parser").select_one(
            self.IMAGE_SELECTOR
        )
        
        # Проверяем наличие как самого тега, так и атрибута src в нем (заполненного src)
        if image is None or not image.get("src"):
            return None
        
        # Собираем полную ссылку
        # дял запроса в методе read_image
        image_url = urljoin(page_url, image["src"])
        
        # Посоветовала нейронка
        # Разбираем ссылку на части, берем домен (hostname)
        # Сверяем поулченный домен с self.ALLOWED_IMAGE_HOSTS
        # Таким образом, сервер ходит только по ссылкам на CDN, 
        # где действительно лежат картинки
        if urlparse(image_url).hostname not in self.ALLOWED_IMAGE_HOSTS:
            return None
        
        return image_url
    
    async def _read_limited(
        self,
        response: aiohttp.ClientResponse,
        max_size: int
    ) -> bytes | None:
        
        content = bytearray()
        
        # Читаем полученный ответ по кускам в 64 кб
        async for chunk in response.content.iter_chunked(64 * 1024):
            content.extend(chunk)
            
            if len(content) > max_size:
                return None
            
        return bytes(content)
