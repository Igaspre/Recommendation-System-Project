import os
import sys
from PIL import Image

def reducir_png(ruta_imagen, num_colores=256):
    try:
        with Image.open(ruta_imagen) as img:
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
                cuantizada = img.quantize(colors=num_colores, method=Image.FASTOCTREE)
            else:
                cuantizada = img.convert("P", palette=Image.ADAPTIVE, colors=num_colores)
            
            cuantizada.save(ruta_imagen, optimize=True)
            print(f"Procesada: {ruta_imagen}")
    except Exception as e:
        print(f"Error al procesar {ruta_imagen}: {e}")

def procesar_carpeta(carpeta, num_colores=256):
    if not os.path.isdir(carpeta):
        print(f"Error: '{carpeta}' no es un directorio válido.")
        sys.exit(1)
    
    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".png"):
            ruta = os.path.join(carpeta, archivo)
            reducir_png(ruta, num_colores)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    
    carpeta_imagenes = sys.argv[1]
    procesar_carpeta(carpeta_imagenes)
