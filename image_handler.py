import base64
from PIL import Image
import io

class ImageHandler:
    @staticmethod
    def process_image(file_path, max_size=(100, 100)):
        with Image.open(file_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail(max_size, Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @staticmethod
    def decode_image(encoded_image):
        image_data = base64.b64decode(encoded_image)
        return Image.open(io.BytesIO(image_data))
