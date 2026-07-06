import os

from PIL import Image


def create_default_test_image(media_root):
    """
    Crée automatiquement default-product.jpg pour les tests
    """
    path = os.path.join(media_root, "announcements")
    os.makedirs(path, exist_ok=True)

    img_path = os.path.join(path, "default-product.jpg")

    if not os.path.exists(img_path):
        img = Image.new("RGB", (450, 450), color=(200, 200, 200))
        img.save(img_path, "JPEG")
