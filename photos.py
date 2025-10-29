# photos.py
from flask import Blueprint, request, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import os, random
from utils import TH3, TH1, TH2

photos_bp = Blueprint('photos', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'}
MAX_IMAGE_SIZE = 2000

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@photos_bp.route("/cats")
def cats():
    from app import app  # Import here to avoid circular import
    UPLOAD_FOLDER = os.path.join(app.static_folder or os.path.join(app.root_path, "static"), "cats")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    LAST_FILE = os.path.join(UPLOAD_FOLDER, "_last10.txt")  # stores the previous batch
    msg = request.args.get('msg', '')
    shuffle = "shuffle" in request.args

    try:
        files = [
            f for f in os.listdir(UPLOAD_FOLDER)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            and not f.startswith("_")  # skip internal files like _last10.txt
        ]
    except FileNotFoundError:
        files = []

    if not files:
        return f"""
        <!DOCTYPE html><html><head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body{{background:{TH3};color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}}
          a{{color:{TH1};text-decoration:none;display:inline-block;margin:1em}}
        </style>
        </head><body>
          <a href="/">← MENU</a>
          <h2>🐈 Gallery</h2>
          <p>No images found in <code>static/cats</code>.</p>
          <a href="/cats/upload" style="background:{TH1};color:#000;padding:0.5em 1em;border:none;border-radius:6px;text-decoration:none;">Upload</a>
          <p class="msg" style="color:{TH2};font-weight:bold;margin:1em 0;">{msg}</p>
        </body></html>
        """

    # --- Load last 10 used photos ---
    prev_batch = []
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE) as f:
            prev_batch = [ln.strip() for ln in f if ln.strip()]

    # --- Choose 10 photos, excluding previous ones when shuffling ---
    if shuffle:
        available = [f for f in files if f not in prev_batch]
        if len(available) < 10:
            available = files.copy()  # reset if not enough
        sample = random.sample(available, min(10, len(available)))
        with open(LAST_FILE, "w") as f:
            f.write("\n".join(sample))
    else:
        # first visit or non-shuffle — reuse previous batch if exists
        sample = prev_batch or random.sample(files, min(10, len(files)))

    # --- Build HTML ---
    imgs = "\n".join(
        f'<img loading="lazy" src="{url_for("static", filename=f"cats/{name}")}" '
        f'style="width:min(900px,96%);max-width:100%;margin:0.75em auto;display:block;border-radius:12px;"/>'
        for name in sample
    )

    html = f"""
    <!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body{{background:{TH3};color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}}
      a{{color:{TH1};text-decoration:none;display:inline-block;margin:1em;font-size:1.6em}}
      h2{{margin:0.5em 0 0.25em}}
      .buttons{{margin:1em 0}}
      .msg{{color:{TH2};font-weight:bold;margin:1em 0;}}
    </style>
    </head><body>
      <div class="buttons">
        <a href="/">← BACK TO MENU</a>
        <a href="/cats?shuffle=1">🔀 SHUFFLE</a>
        <a href="/cats/upload">📤 Upload</a>
      </div>
      <h2>🐈 Gallery</h2>
      <p style="opacity:0.7;">Showing {len(sample)} of {len(files)} photos</p>
      <p class="msg">{msg}</p>
      {imgs}
      <div class="buttons">
        <a href="/">← MENU</a>
        <a href="/cats?shuffle=1">🔀 SHUFFLE</a>
        <a href="/cats/upload">📤 Upload</a>
      </div>
    </body></html>
    """
    return html


@photos_bp.route("/cats/upload", methods=['GET', 'POST'])
def cats_upload():
    from app import app  # Import here to avoid circular import
    UPLOAD_FOLDER = os.path.join(app.static_folder or os.path.join(app.root_path, "static"), "cats")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if request.method == 'POST':
        files = request.files.getlist('file')
        saved_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                temp_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(temp_path)
                try:
                    im = Image.open(temp_path)
                    if im.width > MAX_IMAGE_SIZE or im.height > MAX_IMAGE_SIZE:
                        im.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
                    jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                    jpg_path = os.path.join(UPLOAD_FOLDER, jpg_filename)
                    im.convert('RGB').save(jpg_path, 'JPEG', quality=85)
                    os.remove(temp_path)
                    saved_count += 1
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    os.remove(temp_path)
        if saved_count:
            msg = f"Uploaded and processed {saved_count} photo{'s' if saved_count > 1 else ''}!"
        else:
            msg = "No valid files uploaded."
        return redirect(url_for('photos.cats') + f'?msg={msg}')

    html = f"""
    <!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body{{background:{TH3};color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}}
      a{{color:{TH1};text-decoration:none;display:inline-block;margin:1em}}
      form{{margin:2em 0;}}
      input[type="file"]{{margin:1em 0;}}
      button{{background:{TH1};color:#000;padding:0.7em 1.5em;border:none;border-radius:6px;font-size:1.2em;}}
      .note{{opacity:0.7;font-size:0.9em;margin-top:1em;}}
    </style>
    </head><body>
      <a href="/cats">← Back to Gallery</a>
      <h2>Upload Photos</h2>
      <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" multiple accept="image/*">
        <!-- Optional: Uncomment for token-based authentication -->
        <!-- <input type="text" name="token" placeholder="Enter token" style="margin:1em 0;padding:0.5em;"> -->
        <p class="note">Tap to choose from gallery or take a new photo.</p>
        <button type="submit">Upload</button>
    </form>
      <a href="/">← MENU</a>
    </body></html>
    """
    return html
