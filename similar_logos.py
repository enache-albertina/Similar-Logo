from PIL import Image, ImageChops, UnidentifiedImageError
import os
import shutil

def compare_images(image_path1, image_path2, tolerance=500):
    try:
        img1 = Image.open(image_path1).convert('RGB')
        img2 = Image.open(image_path2).convert('RGB')
    except (IOError, UnidentifiedImageError):
        return None

    hist1 = img1.histogram()
    hist2 = img2.histogram()
    diff = sum(abs(h1 - h2) for h1, h2 in zip(hist1, hist2))
    return diff > tolerance  # True dacă sunt diferite, False dacă sunt similare

# === Config ===
logos_folder = "favicons"  
output_folder = "grupuri_similare"
os.makedirs(output_folder, exist_ok=True)

logos = [f for f in os.listdir(logos_folder) if f.endswith('.png')]
logo_paths = {f: os.path.join(logos_folder, f) for f in logos}

# Pentru a urmări ce imagini au fost deja grupate
grouped_logos = set()
grup_index = 1

for i in range(len(logos)):
    img1_name = logos[i]
    if img1_name in grouped_logos:
        continue

    img1_path = logo_paths[img1_name]
    grup = [img1_name]

    for j in range(i + 1, len(logos)):
        img2_name = logos[j]
        if img2_name in grouped_logos:
            continue

        img2_path = logo_paths[img2_name]
        similar = compare_images(img1_path, img2_path)

        if similar is not None and not similar:  # sunt similare
            grup.append(img2_name)
            grouped_logos.add(img2_name)

    if len(grup) > 1:
        grup_folder = os.path.join(output_folder, f"grup_{grup_index}")
        os.makedirs(grup_folder, exist_ok=True)
        for img_name in grup:
            src_path = logo_paths[img_name]
            dst_path = os.path.join(grup_folder, img_name)
            shutil.copy(src_path, dst_path)
        print(f"Creat {grup_folder} cu {len(grup)} imagini similare.")
        grouped_logos.update(grup)
        grup_index += 1


# Salvează fișierele negrupate într-un folder separat
output_singulare = "favicons_unice"
os.makedirs(output_singulare, exist_ok=True)

for img_name in logos:
    if img_name not in grouped_logos:
        src_path = logo_paths[img_name]
        dst_path = os.path.join(output_singulare, img_name)
        shutil.copy(src_path, dst_path)

print(f"{len(logos) - len(grouped_logos)} imagini unice copiate în {output_singulare}.")
