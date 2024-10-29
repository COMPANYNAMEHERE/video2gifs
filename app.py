import os
import random
import string
import uuid
import threading
import shutil
import atexit
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, flash, jsonify, make_response
)
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'  # Replace with a secure key in production

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
OUTPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'output')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB limit

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Default Settings
default_settings = {
    'num_chunks': 3,
    'gif_duration': 2.0,
    'frame_rate': 10,
    'resolution': '480p'
}

# Load settings from a file or use defaults
SETTINGS_FILE = 'settings.txt'

def load_settings():
    settings = default_settings.copy()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if key in settings:
                        if isinstance(settings[key], int):
                            try:
                                settings[key] = int(value)
                            except ValueError:
                                pass
                        elif isinstance(settings[key], float):
                            try:
                                settings[key] = float(value)
                            except ValueError:
                                pass
                        else:
                            settings[key] = value
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")

settings = load_settings()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_random_filename(extension='gif'):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + f'.{extension}'

# Global dictionary to track tasks
tasks = {}
tasks_lock = threading.Lock()

def generate_gifs_task(task_id, filename):
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'Loading Video'
            tasks[task_id]['progress'] = 5  # Loading video is 5%

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        clip = VideoFileClip(video_path)
        duration = clip.duration

        with tasks_lock:
            tasks[task_id]['status'] = 'Splitting Video into Chunks'
            tasks[task_id]['progress'] = 10  # Splitting is 5%

        num_chunks = settings['num_chunks']
        gif_duration = settings['gif_duration']
        frame_rate = settings['frame_rate']
        resolution = settings['resolution']

        if duration < gif_duration * num_chunks:
            with tasks_lock:
                tasks[task_id]['status'] = 'Failed: Video too short'
                tasks[task_id]['progress'] = 100
            clip.close()
            # Delete the uploaded video file
            os.remove(video_path)
            return

        # Determine resolution
        resolution_map = {
            '240p': (426, 240),
            '360p': (640, 360),
            '480p': (854, 480),
            '720p': (1280, 720),
            '1080p': (1920, 1080)
        }
        target_resolution = resolution_map.get(resolution, (854, 480))

        max_start = duration - gif_duration * num_chunks
        selected_starts = sorted([random.uniform(0, max_start) for _ in range(num_chunks * 3)])

        gifs = []
        total_tasks = 3 * num_chunks + 2  # Including concatenation and writing
        current_task = 2  # Already completed loading and splitting

        for i in range(3):
            clips = []
            for j in range(num_chunks):
                # Check if stop has been requested
                with tasks_lock:
                    if tasks[task_id].get('stop', False):
                        tasks[task_id]['status'] = 'Stopped by User'
                        tasks[task_id]['progress'] = current_task / total_tasks * 100
                        clip.close()
                        # Delete the uploaded video file
                        os.remove(video_path)
                        return

                start_time = selected_starts[i * num_chunks + j]
                subclip = clip.subclip(start_time, start_time + gif_duration)
                clips.append(subclip)
                current_task += 1
                progress = int((current_task / total_tasks) * 100)
                with tasks_lock:
                    tasks[task_id]['progress'] = progress
                    tasks[task_id]['status'] = f'Processing Chunk {i+1}-{j+1}'

            final_clip = concatenate_videoclips(clips)
            final_clip = final_clip.resize(newsize=target_resolution)
            gif_filename = generate_random_filename()
            gif_path = os.path.join(app.config['OUTPUT_FOLDER'], gif_filename)
            final_clip.write_gif(gif_path, fps=frame_rate, program='ffmpeg')
            gifs.append(gif_filename)
            final_clip.close()
            current_task += 1
            progress = int((current_task / total_tasks) * 100)
            with tasks_lock:
                tasks[task_id]['progress'] = progress
                tasks[task_id]['status'] = f'Finished Processing Chunk {i+1}'

        clip.close()

        with tasks_lock:
            tasks[task_id]['gifs'] = gifs
            tasks[task_id]['progress'] = 100
            tasks[task_id]['status'] = 'Completed'

        # Delete the uploaded video file after processing
        os.remove(video_path)

    except Exception as e:
        with tasks_lock:
            tasks[task_id]['status'] = f'Failed: {str(e)}'
            tasks[task_id]['progress'] = 100
        # Attempt to delete the uploaded video file
        try:
            os.remove(video_path)
        except:
            pass

    finally:
        # Optionally, delete the uploaded video file here if not already deleted
        pass

# Cleanup function to delete all uploaded and output files on shutdown
def cleanup_files():
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    except Exception as e:
        print(f"Error during cleanup: {e}")

atexit.register(cleanup_files)

@app.route('/')
def index():
    # Check if there's an ongoing task via cookie
    task_id = request.cookies.get('current_task')
    gifs = []
    if task_id:
        with tasks_lock:
            task = tasks.get(task_id)
            if task and task['status'] not in ['Completed', 'Stopped by User'] and not task['status'].startswith('Failed'):
                pass  # Ongoing task
            elif task and task['status'] == 'Completed':
                gifs = task['gifs']
                # Clear the cookie
                resp = make_response(render_template('index.html', gifs=zip(gifs, [url_for('uploaded_file', filename='output/' + gif) for gif in gifs])))
                resp.set_cookie('current_task', '', expires=0)
                return resp
            elif task and (task['status'].startswith('Failed') or task['status'] == 'Stopped by User'):
                flash(task['status'])
                # Clear the cookie
                resp = make_response(render_template('index.html', gifs=None))
                resp.set_cookie('current_task', '', expires=0)
                return resp
            else:
                # Invalid task_id
                resp = make_response(render_template('index.html', gifs=None))
                resp.set_cookie('current_task', '', expires=0)
                return resp
    return render_template('index.html', gifs=None)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)
        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks[task_id] = {'progress': 0, 'status': 'Queued', 'gifs': [], 'stop': False}
        thread = threading.Thread(target=generate_gifs_task, args=(task_id, filename))
        thread.start()
        # Create response and set cookie
        resp = make_response(jsonify({'task_id': task_id}), 202)
        resp.set_cookie('current_task', task_id, max_age=3600, samesite='Lax')
        return resp
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

@app.route('/progress/<task_id>')
def progress(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task ID'}), 404
    return jsonify({'progress': task['progress'], 'status': task['status'], 'gifs': task['gifs']})

@app.route('/stop/<task_id>', methods=['POST'])
def stop_task(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            return jsonify({'error': 'Invalid task ID'}), 404
        if task['status'] in ['Completed', 'Stopped by User'] or task['status'].startswith('Failed'):
            return jsonify({'error': 'Task already completed or stopped.'}), 400
        task['stop'] = True
    return jsonify({'message': 'Task stop requested.'}), 200

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    global settings
    if request.method == 'POST':
        try:
            settings['num_chunks'] = int(request.form.get('num_chunks', settings['num_chunks']))
            settings['gif_duration'] = float(request.form.get('gif_duration', settings['gif_duration']))
            settings['frame_rate'] = int(request.form.get('frame_rate', settings['frame_rate']))
            settings['resolution'] = request.form.get('resolution', settings['resolution'])
            save_settings(settings)
            flash('Settings updated successfully.')
            return redirect(url_for('settings_page'))
        except ValueError:
            flash('Invalid input. Please enter valid values.')
            return redirect(request.url)
    return render_template('settings.html', settings=settings)

@app.route('/static/uploads/output/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
