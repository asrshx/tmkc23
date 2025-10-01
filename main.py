from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
import os, uuid, subprocess, threading
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Session management

BASE_UPLOAD_FOLDER = "user_projects"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = set(['py', 'html', 'css', 'js'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML template with stylish drag-drop + build/start input
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flask Code Builder Panel</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background: #f4f4f4; padding: 30px; }
#drop-area {
    border: 2px dashed #007bff;
    border-radius: 10px;
    padding: 30px;
    text-align: center;
    color: #007bff;
    margin-bottom: 20px;
    cursor: pointer;
}
#drop-area.highlight { background-color: #e9f5ff; }
.card { margin-bottom: 15px; }
</style>
</head>
<body>
<div class="container">
  <h2 class="mb-4">Flask Code Builder & Web Preview</h2>

  <div id="drop-area">
    <p>Drag & Drop your code files here or click to upload</p>
    <input type="file" id="fileElem" multiple style="display:none">
  </div>

  <form method="POST" action="/" id="buildForm">
    <div class="mb-3">
      <label class="form-label">Build Command</label>
      <input type="text" class="form-control" name="build_cmd" placeholder="e.g., python -m pip install -r requirements.txt">
    </div>
    <div class="mb-3">
      <label class="form-label">Start Command</label>
      <input type="text" class="form-control" name="start_cmd" placeholder="e.g., python app.py">
    </div>
    <button class="btn btn-primary" type="submit">Submit & Build</button>
  </form>

  {% if preview_url %}
  <hr>
  <h4>Your Web Preview:</h4>
  <a href="{{ preview_url }}" target="_blank" class="btn btn-success">Open Web Page</a>
  {% endif %}
</div>

<script>
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileElem');

dropArea.addEventListener('click', () => fileInput.click());

['dragenter','dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); dropArea.classList.add('highlight'); });
});
['dragleave','drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); dropArea.classList.remove('highlight'); });
});
dropArea.addEventListener('drop', e => {
    const dt = e.dataTransfer;
    const files = dt.files;
    uploadFiles(files);
});
fileInput.addEventListener('change', e => uploadFiles(fileInput.files));

function uploadFiles(files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('file', file);
    }
    fetch("/", { method: 'POST', body: formData }).then(() => location.reload());
}
</script>
</body>
</html>
"""

def run_start_command(user_folder, start_cmd):
    """Runs the start command in background thread"""
    subprocess.Popen(start_cmd, cwd=user_folder, shell=True)

@app.route("/", methods=["GET", "POST"])
def index():
    # Assign unique user session folder
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_folder = os.path.join(BASE_UPLOAD_FOLDER, session['user_id'])
    os.makedirs(user_folder, exist_ok=True)

    preview_url = None

    if request.method == "POST":
        # Handle uploaded files
        files = request.files.getlist("file")
        for file in files:
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))

        # Handle build & start commands
        build_cmd = request.form.get('build_cmd')
        start_cmd = request.form.get('start_cmd')
        if build_cmd:
            subprocess.Popen(build_cmd, cwd=user_folder, shell=True)

        if start_cmd:
            threading.Thread(target=run_start_command, args=(user_folder, start_cmd), daemon=True).start()
            preview_url = f"http://127.0.0.1:5000/user_preview/{session['user_id']}/"

    return render_template_string(HTML, preview_url=preview_url)

@app.route("/user_preview/<user_id>/")
def user_preview(user_id):
    """Serve user's uploaded files as static site"""
    user_folder = os.path.join(BASE_UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return "User files not found."
    # Serve index.html by default
    return send_from_directory(user_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
