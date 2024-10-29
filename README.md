# Video to GIF Converter 🎥 ➞ 🎞️

A web application for converting video clips into GIFs, optimized for web preview and sharing. Ideal for creating animated thumbnails or social media posts. Built using **Flask** and **MoviePy**, users can upload videos, select settings, and download the resulting GIFs easily.

## Features

- **Upload Video**: Supports MP4, AVI, MOV, and MKV formats for GIF conversion.
- **Multiple GIF Creation**: Splits videos into sequential chunks, similar to YouTube previews, to create multiple GIFs.
- **Customizable Settings**: Configure the number of chunks, GIF duration, frame rate, and resolution.
- **Stop Conversion**: Option to stop the GIF creation process at any time.
- **Responsive Design**: User-friendly interface built with Bootstrap, compatible across devices.
- **Progress Tracking**: Progress bar to show conversion status.
- **Efficient File Management**: Deletes temporary files after processing to save space.
- **Optimized Results**: Offers three different GIF options for quality selection.

## Installation

### Prerequisites

- **Python 3.8+**
- **FFmpeg**: Required by MoviePy for processing video files.

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/COMPANYNAMEHERE/video2gif.git
   cd video2gif
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure FFmpeg is Installed**

   - **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your PATH.
   - **macOS**: Install via Homebrew:
     ```bash
     brew install ffmpeg
     ```
   - **Linux**: Install using the package manager:
     ```bash
     sudo apt-get install ffmpeg
     ```

## Usage

1. **Run the Application**

   ```bash
   python app.py
   ```

2. **Open in Browser**

   Navigate to `http://127.0.0.1:5000/` in your browser. Keep the terminal window open while using the application.

3. **Upload and Convert**

   - **Upload**: Select a video file for conversion.
   - **Configure Settings**: Adjust GIF settings as needed.
   - **Download GIFs**: View and download the generated GIFs.

## Configuration

Edit `settings.txt` to configure default settings:

```plaintext
num_chunks=3
gif_duration=2.0
frame_rate=10
resolution=480p
```

- **num_chunks**: Number of segments to split the video into.
- **gif_duration**: Duration (in seconds) of each GIF.
- **frame_rate**: Frames per second, affecting animation smoothness.
- **resolution**: Output resolution (`240p`, `360p`, `480p`, `720p`, `1080p`).

## Directory Structure

```plaintext
video2gif/
├── app.py                 # Main application file
├── requirements.txt       # List of dependencies
├── settings.txt           # Default GIF settings
├── static/                # Static assets (CSS, JavaScript, etc.)
│   ├── css/
│   ├── js/
│   └── uploads/           # Folder for uploaded videos
│       └── output/        # Folder for generated GIFs
└── templates/             # HTML templates
    ├── index.html         # Main page template
    └── settings.html      # Settings page template
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss.

## Troubleshooting

1. **FFmpeg Not Found**: Ensure FFmpeg is installed and added to the system PATH.
2. **Large Video Files**: Videos up to 500MB are supported; reduce file size if needed.
3. **Permission Issues**: Ensure `uploads` and `output` folders have read/write permissions.
4. **Server Not Running**: Ensure the server is active in your terminal.

## Contact

For questions or issues, open an issue on this repository or contact the maintainers.

## TODO

- Convert GIFs to be optimized for web better.
- Fix progress bar to be more accurate.
- Download videos straight from YouTube.
- Support more video formats (e.g., WebM, FLV).
- Improve mobile experience for a better user interface.

Enjoy creating GIFs! 🎉 Experiment and explore related tools to expand your creative possibilities. Happy GIF making! 🚀

