import os
import subprocess
import re
import argparse
import cv2
from datetime import datetime
from colorama import init, Fore
import threading
from queue import Queue

# Initialize colorama
init()

# Parse command line arguments
parser = argparse.ArgumentParser(description="Generate thumbnails for video files.")
parser.add_argument("-q", "--quality", type=int, default=100, help="Thumbnail quality (default: 100)")
parser.add_argument("-a", "--attempts", type=int, default=10, help="Number of attempts for blurry image (default: 10)")
parser.add_argument("-t", "--timegap", type=int, default=30, help="Time gap in seconds between attempts (default: 30)")
parser.add_argument("-b", "--blur_threshold", type=float, default=100, help="Threshold for blur detection (default: 100)")
parser.add_argument("-s", "--start_time", type=int, default=6, help="Start time in minutes (default: 6)")
parser.add_argument("-l", "--remove_bars", action="store_true", help="Remove black bars from thumbnails")
args = parser.parse_args()

# Directory containing the video files
dir_path = "."

# Output directory for the thumbnails
outdir = os.path.join(dir_path, "thumbs")

# Create the output directory if it doesn't exist
os.makedirs(outdir, exist_ok=True)

# Log file for missing thumbnails
missing_log = os.path.join(outdir, "missing.txt")

# Define the video file extensions
video_extensions = (".avi", ".mkv", ".mp4", ".mov")

# Get already generated thumbnails
generated_thumbnails = set(os.listdir(outdir))

# Lock to synchronize access to shared resources
lock = threading.Lock()

# Queue for video files to process
file_queue = Queue()

# Function to log missing thumbnails
def log_missing(outfile, blur_values):
    rounded_blur_values = [round(value, 1) for value in blur_values]
    average_blur = sum(blur_values) / len(blur_values)
    max_blur = max(blur_values)
    with lock:
        with open(missing_log, "a") as log_file:
            log_file.write(f"{outfile} (blurriness: ")
            log_file.write(", ".join([f"{value:.1f}" for value in rounded_blur_values]).ljust(50))
            log_file.write(f") avg {average_blur:.2f} max {max_blur:.2f}\n")

# Function to print colored text
def print_colored(text, color):
    with lock:
        print(color + text + Fore.RESET)

# Function to check image blur
def is_blurry(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# Function to remove black bars
def remove_black_bars(image_path):
    if os.path.exists(image_path):
        subprocess.run(['mogrify', '-bordercolor', 'black', '-fuzz', '20%', '-trim', image_path], check=True)

# Function to process a single video file
def process_video():
    while True:
        file_path = file_queue.get()
        if file_path is None:
            break
        try:
            # Extract the season and episode numbers from the file name
            match = re.search(r'S(\d{1,2})E(\d{1,2})', file_path, flags=re.IGNORECASE)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                # Generate the output file name
                outfile = f"s{season}e{episode}.jpg"
                if outfile in generated_thumbnails:
                    print_colored(f"Thumbnail already exists for {outfile}. Skipping.", Fore.CYAN)
                    continue
                # Attempt to generate a non-blurry thumbnail
                attempt = 1
                offset = args.start_time * 60  # Initial offset
                blur_values = []
                while attempt <= args.attempts:
                    try:
                        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'quiet', '-ss', f'00:{offset//60:02d}:{offset%60:02d}', '-i', file_path, '-vf', f'thumbnail={args.quality}', '-vframes', '1', '-q:v', '2', f"{os.path.join(outdir, outfile)}.tmp.jpg"], check=True, stdin=subprocess.PIPE)
                        # Check for blur
                        blur_value = is_blurry(f"{os.path.join(outdir, outfile)}.tmp.jpg")
                        blur_values.append(blur_value)
                        if blur_value < args.blur_threshold:  # Check against threshold
                            os.remove(f"{os.path.join(outdir, outfile)}.tmp.jpg")  # Delete blurry image
                            print_colored(f"Attempt {attempt}: Thumbnail is blurry ({blur_value:.2f}) for {outfile}.", Fore.YELLOW)
                            attempt += 1
                            offset += args.timegap  # Increment offset for next attempt
                            if attempt > args.attempts:
                                print_colored(f"All attempts failed for {outfile}.", Fore.RED)
                                log_missing(outfile, blur_values)
                                break
                            continue
                        else:
                            # Rename the thumbnail file
                            os.rename(f"{os.path.join(outdir, outfile)}.tmp.jpg", os.path.join(outdir, outfile))
                            # Apply image enhancement using ImageMagick
                            subprocess.run(['convert', os.path.join(outdir, outfile), '-channel', 'rgb', '-auto-level', os.path.join(outdir, outfile)])
                            print_colored(f"Thumbnail generated and enhanced for {outfile} (Blur value: {blur_value:.2f}).", Fore.GREEN)
                            break
                    except subprocess.CalledProcessError:
                        print_colored(f"Failed to generate thumbnail for {outfile}.", Fore.RED)
                        log_missing(outfile, blur_values)
                        break

                # Remove black bars if flag is set
                if args.remove_bars:
                    remove_black_bars(os.path.join(outdir, outfile))

        except Exception as e:
            print_colored(f"Error processing file {file_path}: {e}", Fore.RED)
        finally:
            file_queue.task_done()

# Function to start logging for the run
def start_logging_run():
    with open(missing_log, "a") as log_file:
        log_file.write("=" * 50 + "\n")
        log_file.write(f"Run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Arguments used: {args}\n")
        log_file.write("=" * 50 + "\n")

# Function to finish logging for the run
def finish_logging_run(start_time):
    end_time = datetime.now()
    total_runtime = (end_time - start_time).total_seconds()
    with open(missing_log, "a") as log_file:
        log_file.write("=" * 50 + "\n")
        log_file.write(f"Run completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Total runtime: {total_runtime:.2f} seconds\n")
        log_file.write("=" * 50 + "\n\n")

# Start logging for the run
start_time = datetime.now()
start_logging_run()

# Find all video files in the directory and its subdirectories
for root, _, files in os.walk(dir_path):
    for file in files:
        if file.lower().endswith(video_extensions):
            file_queue.put(os.path.join(root, file))

# Create worker threads
num_threads = min(len(os.sched_getaffinity(0)), file_queue.qsize())  # Number of available CPU cores
threads = []
for _ in range(num_threads):
    thread = threading.Thread(target=process_video)
    thread.start()
    threads.append(thread)

# Wait for all file processing to complete
file_queue.join()

# Stop worker threads
for _ in range(num_threads):
    file_queue.put(None)

# Join worker threads
for thread in threads:
    thread.join()

# Finish logging for the run
finish_logging_run(start_time)

# Change the permissions of the thumbs folder and all its contents
os.chmod(outdir, 0o777)
