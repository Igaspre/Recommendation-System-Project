import os
import shutil
from icrawler.builtin import GoogleImageCrawler
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Item

db_path = os.path.join(os.getcwd(), 'instance', 'users.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

IMAGES_DIR = os.path.join(os.getcwd(), 'app', 'static', 'images')
TEMP_DIR = os.path.join(os.getcwd(), 'app', 'static', 'temp_images')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

items = session.query(Item).all()

for item in items:
    filename = "".join(c for c in item.name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    print(f"Procesando: {item.name}")
    
    temp_item_dir = os.path.join(TEMP_DIR, 'download')
    if os.path.exists(temp_item_dir):
        shutil.rmtree(temp_item_dir)
    os.makedirs(temp_item_dir, exist_ok=True)
    
    crawler = GoogleImageCrawler(storage={'root_dir': temp_item_dir})
    crawler.crawl(keyword=item.name, max_num=1)
    
    downloaded_files = os.listdir(temp_item_dir)
    if downloaded_files:
        file_path = os.path.join(temp_item_dir, downloaded_files[0])
        try:
            with Image.open(file_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                target_path = os.path.join(IMAGES_DIR, f"{filename}.png")
                img.save(target_path, format='PNG')
                print(f"Imagen guardada en: {target_path}")
        except Exception as e:
            print(f"Error al procesar la imagen para {item.name}: {e}")
    else:
        print(f"No se encontró imagen para {item.name}")

shutil.rmtree(TEMP_DIR)
print("Proceso finalizado.")