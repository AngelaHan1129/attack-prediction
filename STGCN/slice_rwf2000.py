import subprocess
from pathlib import Path

# 請確認你的 FFmpeg 安裝在 C:\ffmpeg\bin
# 如果路徑不同，請修改這裡
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE_PATH = r"C:\ffmpeg\bin\ffprobe.exe"

def batch_slice_rwf(input_dir, output_dir, clip_sec=5, fps=30):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Current working dir:", Path.cwd())
    print("Input path:", input_path.resolve())
    
    video_files = []
    for ext in ["*.avi", "*.mp4", "*.mkv", "*.mov"]:
        video_files.extend(input_path.rglob(ext))

    print(f"Found {len(video_files)} video files")

    if not video_files:
        print("No video files found. Check your input path.")
        return

    for video_file in video_files:
        print(f"Processing: {video_file}")
        video_stem = video_file.stem
        clip_dir = output_path / video_stem
        clip_dir.mkdir(parents=True, exist_ok=True)

        duration_cmd = [
            FFPROBE_PATH, "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(video_file)
        ]

        try:
            # 確保檔案存在才執行
            if not Path(FFPROBE_PATH).exists():
                print(f"Error: FFprobe not found at {FFPROBE_PATH}")
                return

            duration = float(subprocess.check_output(duration_cmd).decode().strip())
            print(f"Duration: {duration:.2f}s")

            for start in range(0, int(duration), clip_sec):
                seg_len = min(clip_sec, duration - start)
                clip_num = f"{int(start / clip_sec):03d}"
                output_file = clip_dir / f"clip_{clip_num}.mp4"

                cmd = [
                    FFMPEG_PATH,
                    "-ss", f"{start:.1f}",
                    "-t", f"{seg_len:.1f}",
                    "-i", str(video_file),
                    "-r", str(fps),
                    "-an",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    str(output_file),
                    "-y",
                    "-loglevel", "error"
                ]

                subprocess.run(cmd, check=True)
                print(f"Created: {output_file}")

        except Exception as e:
            print(f"Error processing {video_file}: {e}")

if __name__ == "__main__":
    # 確保路徑正確：此腳本在 STGCN 資料夾內
    # 目標資料在 data/raw/rwf2000
    batch_slice_rwf("data/raw/rwf2000", "data/raw/clips")