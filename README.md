# 🧠 Similar Logo Grouper

This Python project identifies **visually similar logos (favicons)** from a dataset of image files and automatically groups them into folders. It's useful for logo deduplication, clustering, and detecting slight variations across brand assets.

---

## 📂 Project Structure

- `favicons/` – Input folder containing all `.png` favicon images
- `grupuri_similare/` – Output folder where groups of similar logos are saved (e.g., `grup_1/`, `grup_2/`, ...)
- `favicons_unice/` – Output folder with logos that did not match any group
- `similar_logos.py` – The main script that performs image comparison and grouping
- `download.py` – (Optional) Script to download or manage favicon sources
- `logos.snappy.parquet` – Input data (presumably containing URLs or metadata)

---

## ⚙️ How It Works – Implementation Details

The script performs **pairwise image comparison** between all `.png` images found in the `favicons/` folder.

### Step-by-step process:

1. **Load all `.png` images** and store their file paths.
2. Loop through each image `i`:
   - For each other image `j > i`, compare it with `i`.
   - If image `j` is found to be visually similar to `i`, group them together.
   - Mark grouped images so they are not checked again.
3. Create a new output folder named `grup_N` (e.g., `grup_1`, `grup_2`, ...) for each group of similar images.
4. Copy all grouped images into their respective folders.
5. Images that were not grouped with any others are considered unique and are copied into the `favicons_unice/` folder.

---

## 🧠 Image Comparison Logic

The project uses a **simple histogram-based comparison** via the Pillow library (`PIL`).

- Images are opened and converted to RGB.
- A color histogram is calculated for each image (using `.histogram()`).
- The difference between two images is defined as the sum of absolute differences between their histograms:
  
```python
diff = sum(abs(h1 - h2) for h1, h2 in zip(hist1, hist2))
```

- A `tolerance` value (default: 500) determines how sensitive the comparison is.
  - **Lower tolerance** → stricter match
  - **Higher tolerance** → more relaxed match

If the `diff` is **less than or equal to** the tolerance, the two images are considered **similar**.

---

## 🧪 How to Run

### Requirements

- Python 3.x
- Pillow

### Install dependencies
```bash
pip install pillow
```

### Run the script
Make sure your `.png` images are in the `favicons/` folder, then:

```bash
python similar_logos.py
```

---

## 📤 Output Format

- All grouped images are saved in the folder `grupuri_similare/`, in subfolders named:
  - `grup_1/`
  - `grup_2/`
  - ...
  - Each of these contains 2 or more logos that are visually similar.

- All unique logos that didn't match any others are copied into:
  - `favicons_unice/`

### Example output structure:

```
grupuri_similare/
├── grup_1/
│   ├── logo_google.png
│   ├── logo_google2.png
├── grup_2/
│   ├── logo_amazon.png
│   ├── logo_amazon_light.png

favicons_unice/
├── logo_randomsite1.png
├── logo_smallcompany.png
```

You will also see printed messages like:

```
Creat grupuri_similare/grup_1 cu 3 imagini similare.
Creat grupuri_similare/grup_2 cu 2 imagini similare.
957 imagini unice copiate în favicons_unice.
```

---

## 🚀 Future Improvements

- Use perceptual hashing (e.g., `imagehash` or `OpenCV`) for more robust similarity
- Parallelize comparison for performance with large datasets
- Visual GUI for manual inspection of grouped logos
- Add CLI arguments for adjusting tolerance, input/output paths

