"""
Utilitários para otimização de imagens no upload.
"""
import os
from PIL import Image

# Configurações de otimização de imagem
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1080
THUMBNAIL_SIZE = (300, 300)
PROFILE_PHOTO_SIZE = (200, 200)
IMAGE_QUALITY = 85
WEBP_QUALITY = 80
MAX_FILE_SIZE_MB = 5


def optimize_image(image_path, max_width=MAX_IMAGE_WIDTH, max_height=MAX_IMAGE_HEIGHT, quality=IMAGE_QUALITY):
    """
    Otimiza uma imagem redimensionando e comprimindo.
    Retorna o tamanho do arquivo otimizado em bytes.
    """
    try:
        img = Image.open(image_path)

        # Converter para RGB se necessário (para JPEG/WebP)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Criar fundo branco para imagens transparentes
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionar mantendo proporção
        width, height = img.size
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Remover metadados EXIF
        data = list(img.getdata())
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(data)

        # Salvar com otimização
        img_without_exif.save(image_path, 'JPEG', quality=quality, optimize=True, progressive=True)

        # Retornar tamanho do arquivo
        return os.path.getsize(image_path)
    except Exception as e:
        print(f"Erro ao otimizar imagem: {e}")
        return 0


def create_thumbnail(image_path, thumbnail_path, size=THUMBNAIL_SIZE, quality=IMAGE_QUALITY):
    """
    Cria uma thumbnail otimizada da imagem.
    Retorna True se bem-sucedido, False caso contrário.
    """
    try:
        img = Image.open(image_path)

        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Criar thumbnail mantendo proporção
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Salvar thumbnail
        img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)

        return True
    except Exception as e:
        print(f"Erro ao criar thumbnail: {e}")
        return False


def convert_to_webp(image_path, quality=WEBP_QUALITY):
    """
    Converte uma imagem para o formato WebP para melhor compressão.
    Retorna o novo caminho do arquivo se bem-sucedido, None caso contrário.
    """
    try:
        img = Image.open(image_path)

        # Converter para RGB se necessário
        if img.mode != 'RGB' and img.mode != 'RGBA':
            img = img.convert('RGB')

        # Criar novo nome de arquivo com extensão .webp
        base, _ = os.path.splitext(image_path)
        webp_path = f"{base}.webp"

        # Salvar como WebP
        img.save(webp_path, 'WEBP', quality=quality, optimize=True)

        # Remover arquivo original
        os.remove(image_path)

        return webp_path
    except Exception as e:
        print(f"Erro ao converter para WebP: {e}")
        return None


def optimize_profile_photo(image_path, size=PROFILE_PHOTO_SIZE, quality=IMAGE_QUALITY):
    """
    Otimiza foto de perfil redimensionando e comprimindo.
    Retorna True se bem-sucedido, False caso contrário.
    """
    try:
        img = Image.open(image_path)

        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionar para tamanho de perfil
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Salvar com otimização
        img.save(image_path, 'JPEG', quality=quality, optimize=True)

        return True
    except Exception as e:
        print(f"Erro ao otimizar foto de perfil: {e}")
        return False
