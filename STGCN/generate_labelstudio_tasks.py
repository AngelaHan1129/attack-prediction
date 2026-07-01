import argparse
import json
from pathlib import Path
from urllib.parse import quote

VIDEO_EXTS = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v'}

def normalize_base_url(url: str) -> str:
    return url.rstrip('/')

def file_to_url(base_url: str, file_path: Path, root_dir: Path) -> str:
    rel = file_path.relative_to(root_dir).as_posix()
    return f"{normalize_base_url(base_url)}/{quote(rel)}"

def infer_split_and_class(file_path: Path, root_dir: Path):
    parts = file_path.relative_to(root_dir).parts
    split = parts[0] if len(parts) > 0 else ''
    gt_class = parts[1] if len(parts) > 1 else ''
    return split, gt_class

def scan_videos(root_dir: Path):
    files = []
    for p in root_dir.rglob('*'):
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            files.append(p)
    return sorted(files)

def build_tasks(root_dir: Path, base_url: str):
    tasks = []
    for idx, video_file in enumerate(scan_videos(root_dir), start=1):
        split, gt_class = infer_split_and_class(video_file, root_dir)
        tasks.append({
            "data": {
                "video": file_to_url(base_url, video_file, root_dir),
                "file_name": video_file.name,
                "relative_path": video_file.relative_to(root_dir).as_posix(),
                "split": split,
                "gt_class": gt_class
            },
            "meta": {
                "source": "rwf2000",
                "id": idx
            }
        })
    return tasks

def main():
    parser = argparse.ArgumentParser(description='Generate Label Studio tasks.json for RWF-2000 videos')
    parser.add_argument('--root-dir', required=True, help='Path to rwf2000 folder')
    parser.add_argument('--base-url', required=True, help='Base URL serving rwf2000')
    parser.add_argument('--output', default='tasks.json', help='Output JSON path')
    args = parser.parse_args()

    root_dir = Path(args.root_dir).expanduser().resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        raise SystemExit(f'root-dir not found: {root_dir}')

    tasks = build_tasks(root_dir, args.base_url)
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open('w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f'Wrote {len(tasks)} tasks to {out}')

if __name__ == '__main__':
    main()