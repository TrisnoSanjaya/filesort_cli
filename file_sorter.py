#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()

DEFAULT_CONFIG: Dict[str, List[str]] = {
    "Gambar": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"],
    "Dokumen": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".rtf", ".csv"],
    "Video": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    "Musik": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "Arsip": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Kode": [".py", ".js", ".html", ".css", ".json", ".xml", ".java", ".c", ".cpp", ".h", ".php", ".rb", ".go", ".ts", ".jsx", ".tsx"],
    "Folder": [],  # dicocokkan oleh is_dir(), bukan ekstensi
    "Lainnya": [],
}


def _baca(prompt: str, default: str = "") -> str:
    val = Prompt.ask(f"{prompt}", default=default)
    return val


def _baca_path(prompt: str, wajib: bool = False) -> Optional[str]:
    while True:
        val = Prompt.ask(f"{prompt}").strip()
        if not val and not wajib:
            return val
        p = Path(os.path.expandvars(os.path.expanduser(val))).resolve()
        if p.exists() and p.is_dir():
            return str(p)
        console.print("[red]Path tidak ditemukan atau bukan folder. Silakan ulangi.[/red]")


def _baca_ya(prompt: str, default: bool = False) -> bool:
    return Confirm.ask(f"{prompt}", default=default)


def _interactive_argv() -> List[str]:
    console.print()
    console.print(Panel.fit("[bold cyan]File Sorter[/bold cyan]", border_style="cyan"))
    console.print("[dim]Kelompokkan file berdasarkan ekstensi ke subfolder kategori[/dim]\n")
    src = None
    while not src:
        src = _baca_path("Masukkan folder sumber", wajib=True)
        if not src:
            console.print("[red]Folder sumber tidak boleh kosong.[/red]")
    argv: List[str] = ["--source", src]

    dst = _baca_path("Masukkan folder tujuan (Enter untuk default: di dalam folder sumber)")
    if dst:
        argv += ["--destination", dst]

    mode_raw = _baca("Mode (move/copy)", "move").lower().strip()
    if mode_raw in ("copy", "salin"):
        argv += ["--mode", "copy"]
    else:
        argv += ["--mode", "move"]

    if _baca_ya("Rekursif (pindai subfolder)?", default=True):
        argv += ["--recursive"]

    if _baca_ya("Sertakan folder (direktori) juga?"):
        argv += ["--include-folders"]

    print()
    return argv


def load_config(path: Optional[str]) -> Dict[str, List[str]]:
    if not path:
        return dict(DEFAULT_CONFIG)
    p = Path(path)
    if not p.exists():
        sys.exit(f"Error: file konfigurasi tidak ditemukan: {path}")
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        sys.exit(f"Error: gagal membaca konfigurasi: {e}")
    if not isinstance(data, dict):
        sys.exit("Error: konfigurasi harus berupa JSON object {'Kategori': ['.ext', ...]}")
    normalized: Dict[str, List[str]] = {}
    for k, v in data.items():
        if v is None:
            normalized[k] = []
        elif isinstance(v, list):
            normalized[k] = [f".{str(e).lower().lstrip('.')}" for e in v]
        else:
            sys.exit(f"Error: nilai kategori '{k}' harus berupa list")
    if "Lainnya" not in normalized:
        normalized["Lainnya"] = []
    return normalized


def build_ext_to_category(config: Dict[str, List[str]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for category, exts in config.items():
        for ext in exts:
            if ext:
                mapping[ext.lower()] = category
    return mapping


def gather_files(source: Path, recursive: bool, include_folders: bool = False) -> List[Path]:
    """Kumpulkan file (& folder jika include_folders=True) dari source."""
    out: List[Path] = []

    if recursive:
        # Kumpulkan semua file dari subfolder
        for root, _, filenames in os.walk(source):
            for fn in filenames:
                p = Path(root) / fn
                if p.is_file():
                    out.append(p)
        # Jika include_folders, tambahkan folder level-1 (top-level) saja
        if include_folders:
            for p in source.iterdir():
                if p.is_dir():
                    out.append(p)
    else:
        # Non-rekursif: iterdir level-1
        for p in source.iterdir():
            if p.is_file():
                out.append(p)
            elif include_folders and p.is_dir():
                out.append(p)

    return out


def categorize(path: Path, mapping: Dict[str, str]) -> str:
    """Tentukan kategori: folder → 'Folder', file → mapping ekstensi."""
    if path.is_dir():
        return "Folder"
    return mapping.get(path.suffix.lower(), "Lainnya")


def safe_destination(dest_dir: Path, filename: str) -> Path:
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    i = 1
    while True:
        new_name = f"{stem} ({i}){suffix}"
        candidate = dest_dir / new_name
        if not candidate.exists():
            return candidate
        i += 1


def ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        console.print(f"[red]Error: gagal membuat folder '{path}': {e}[/red]")
        return False


def run(
    source: str,
    destination: Optional[str],
    mode: str,
    recursive: bool,
    dry_run: bool,
    config_path: Optional[str],
    include_folders: bool = False,
) -> None:
    source_raw = os.path.expandvars(os.path.expanduser(source))
    source_path = Path(source_raw).resolve()
    if not source_path.exists() or not source_path.is_dir():
        sys.exit(f"Error: folder sumber tidak valid: {source}")

    config = load_config(config_path)
    mapping = build_ext_to_category(config)

    dest_raw = os.path.expandvars(os.path.expanduser(destination)) if destination else None
    dest_base = Path(dest_raw).resolve() if dest_raw else source_path

    files = gather_files(source_path, recursive, include_folders)
    total = len(files)
    tipe = "folder & file" if include_folders else "file"

    console.print(f"\n[bold cyan]Memindai {total} {tipe} dari:[/bold cyan] {source_path}")
    if dry_run:
        console.print("[yellow]=== MODE DRY-RUN (tidak ada yang akan dipindah/disalin) ===\n[/yellow]")

    stats: Dict[str, Dict[str, int]] = {
        "total": {"files": total, "success": 0, "skipped": 0, "failed": 0}
    }

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Memproses...", total=total)

        for idx, src in enumerate(files, start=1):
            category = categorize(src, mapping)
            dest_dir = dest_base / category
            dest_path = safe_destination(dest_dir, src.name)

            if src.resolve() == dest_path.resolve():
                stats.setdefault(category, {"success": 0, "skipped": 0, "failed": 0})
                stats[category]["skipped"] += 1
                stats["total"]["skipped"] += 1
                progress.advance(task)
                continue

            if dry_run:
                stats.setdefault(category, {"success": 0, "skipped": 0, "failed": 0})
                stats[category]["success"] += 1
                stats["total"]["success"] += 1
            else:
                if not ensure_dir(dest_dir):
                    stats.setdefault(category, {"success": 0, "skipped": 0, "failed": 0})
                    stats[category]["failed"] += 1
                    stats["total"]["failed"] += 1
                    progress.advance(task)
                    continue
                try:
                    if src.is_dir():
                        if mode == "copy":
                            shutil.copytree(str(src), str(dest_path))
                        else:
                            shutil.move(str(src), str(dest_path))
                    else:
                        if mode == "move":
                            shutil.move(str(src), str(dest_path))
                        else:
                            shutil.copy2(str(src), str(dest_path))
                    stats.setdefault(category, {"success": 0, "skipped": 0, "failed": 0})
                    stats[category]["success"] += 1
                    stats["total"]["success"] += 1
                except Exception as e:
                    console.print(f"\n[red][GAGAL] {src.name}: {e}[/red]")
                    stats.setdefault(category, {"success": 0, "skipped": 0, "failed": 0})
                    stats[category]["failed"] += 1
                    stats["total"]["failed"] += 1

            progress.advance(task)

    console.print()
    table = Table(title="Ringkasan", box=box.ROUNDED, title_justify="left")
    table.add_column("Kategori", style="cyan", width=14)
    table.add_column("Sukses", justify="right")
    table.add_column("Skip", justify="right")
    table.add_column("Gagal", justify="right")
    for cat in sorted(k for k in stats if k != "total"):
        s = stats[cat]
        table.add_row(cat, str(s["success"]), str(s["skipped"]), str(s["failed"]))

    # Baris total (bold)
    t = stats["total"]
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{t['success']}[/bold]",
        f"[bold]{t['skipped']}[/bold]",
        f"[bold]{t['failed']}[/bold]",
    )
    console.print(table)

    if stats["total"]["failed"]:
        sys.exit(1)


def main(argv: Optional[List[str]] = None) -> int:
    raw = list(argv) if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="File Sorter - Kelompokkan file & folder berdasarkan ekstensi ke subfolder kategori."
    )
    parser.add_argument("--source", "-s", default=None, help="Folder sumber yang akan dirapikan")
    parser.add_argument("--destination", "-d", default=None, help="Folder tujuan (default: di dalam folder sumber)")
    parser.add_argument("--mode", "-m", choices=["move", "copy"], default="move", help="move (pindah) atau copy (salin)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Pindai semua subfolder")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Tampilkan rencana tanpa eksekusi")
    parser.add_argument("--config", "-c", default=None, help="Path file JSON konfigurasi kustom")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode input interaktif: isi source/tujuan sendiri")
    parser.add_argument("--include-folders", "-f", action="store_true", help="Sertakan folder (direktori) dalam pengurutan")
    args = parser.parse_args(raw)

    if args.interactive or not args.source:
        # Tanpa argumen → otomatis mode interaktif
        ia_argv = _interactive_argv()
        ia = parser.parse_args(ia_argv)
        run(
            source=ia.source, destination=ia.destination, mode=ia.mode,
            recursive=ia.recursive, dry_run=ia.dry_run, config_path=ia.config,
            include_folders=ia.include_folders,
        )
        return 0

    run(
        source=args.source, destination=args.destination, mode=args.mode,
        recursive=args.recursive, dry_run=args.dry_run, config_path=args.config,
        include_folders=args.include_folders,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
