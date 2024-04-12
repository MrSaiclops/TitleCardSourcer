# TitleCardSourcer
A versatile python script for generating high quality and relevant source images for TCM to use.
<img src="https://github.com/MrSaiclops/TitleCardSourcer/assets/88596884/28776bdf-37bb-4903-8ae5-70cb89522c68" width="500" height="auto">


### The Problem
TitleCardMaker is entering a new era with the WebUI becoming more robust. While I find it easy to achieve the effects I want with the overlay that TCM applies, I often feel that my source images are lacking. Plex offers one image based on the video file itself, and TMDB is dependant on user submissions. So there's little flexibility while remaining autonomous, especially if the media you're working with is more obscure (_Shockingly_, the same people lovingly curating frames from Breaking Bad are not putting the same effort toward The Real Housewives universe).

### The Solution
Use FFmpeg and OpenCV to extract frames from video files as they live in your media library, checking for blur and enhancing the one with the best clarity. The script supports various customization options such as quality, number of attempts for blurry images, time gap between attempts, blur detection threshold, start time for thumbnail extraction, and black bars (pillar/letter boxing) removal.
### Features
*  Efficient Thumbnail Generation: Utilizes FFmpeg to extract frames from video files at specified intervals.
*  Blur Detection: Utilizes OpenCV to check for image blur in the generated thumbnails.
*  Image Enhancement: Applies image enhancement using ImageMagick to improve thumbnail quality.
*  Customization: Offers various customization options such as thumbnail quality, number of attempts for blurry images, time gap between attempts, blur detection threshold, start time for thumbnail extraction, and black bars removal.
*  Multithreading: Utilizes multithreading to process multiple video files concurrently, optimizing performance.
*  Logging: Logs missing thumbnails and their blur values to a file for reference.
*  Colorized Console Output: Provides colorized console output to indicate the status of thumbnail generation.

## Installation
If I can do it, so can you!
### Prerequisites
*  Python3.x
*  FFmpeg
*  ImageMagick (Comes in requirements.txt)

### Steps (Using a [tteck](https://tteck.github.io/Proxmox/) Ubuntu/Debian installion as an example)
1. Install prerequisites
```console
sudo apt update && sudo apt install git ffmpeg imagemagick pip
```
2. Clone the repository and enter it
```console
git clone https://github.com/MrSaiclops/TitleCardSourcer && cd TitleCardSourcer
```
3. Install Python requirements
```console
pip install -r requirements.txt
```

## Usage
TitleCardSourcer assumes that you use [TRaSH's recommended naming scheme](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme/) for series, seasons, and episdes. It is run from the series folder, see the chart below:
```
Shows
└── Star Trek (1966) {imdb-tt0060028} <--- Run from in here
     ├── Season 01
     ├── Season 02
     ├── Season 03
     ├── ...
     └── thumbs <--------------------------This will be created by the script
         ├── s1e1.jpg
         ├── s1e4.jpg
         ├── s2e6.jpg
         ├── ...
         └── missing.txt <----------------- This is the running log of attempts for this series
```
### Basic run
To process a series, navigate to the parent folder containing all of the ``Season XX`` directories and run the following command:
```console
python3 /path/to/TitleCardSourcer.py
```
It will then recursively enter each season folder and attempt to create a titlecard from all video files therein. If one is found eligible, (For a basic run that means it's over the bluriness threshold of 100) it will be saved in the newly created ``thumbs`` directory that's stored in the parent folder Upon completion you can use ``cat ./thumbs/missing.txt`` to review which episodes failed and make changed for a subsequent run.

### Modifiers
Below are the modifiers that can be used to refine your search for a good titlecard:
| Modifier | Argument | Default | Description |
|---|---|---|---|
| Quality | -q, --quality | 100 | The # of frames for FFmpeg to inspect for the most "representitive" Generally speaking, a higher value here will yield clearer frames Higher numbers also yield more RAM usage, See: [FFmpeg docs](https://ffmpeg.org/ffmpeg-filters.html#thumbnail) |
| Attempts | -a, --attempts | 10 | The number of times to try an episode before giving up and printing the results to ``missing.txt`` |
| Timegap | -t, --timegap | 30 | The space to put between each attempt in the video. A default run checks in 30 second increments from 6 min in the video to 11 min |
| Blur Threshold | -b, --blur_threshold | 100 | The threshold at which point to accept or deny a proposed titlecard.  Lower values means blurrier. Depending on the resolution and file format have different average values. Audit ``missing.txt`` after a mostly failed run to determine the threshold that your subsequent run should have  |
| Start Time | -s, --start_time | 6 | The time in the video file to begin grabbing from. For some shows (I'm looking at your Desperate Housewives), the credits continue popping up in the lower third for the first 10 minutes, in which case you want to move your start time later out to prevent having random names in the titlecard |
| Remove Bars | -l --remove_bars | N/A | Applies ``imagemagick mogrify -bordercolor black -fuzz 20% -trim`` to the titlecard to remove letter/pillar boxing  |
