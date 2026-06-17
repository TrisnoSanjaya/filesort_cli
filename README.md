# File Sorter (CLI)

Program Python untuk mengelompokkan file **dan folder** berdasarkan
ekstensi ke dalam subfolder kategori (move/copy), dengan dukungan
dry-run, rekursif, dan konfigurasi kustom ekstensi.

## Fitur

- Kategori file default + konfigurasi kustom lewat JSON
- Mode `move` (pindah) atau `copy` (salin)
- Mode dry-run untuk melihat rencana tanpa eksekusi
- Pemindaian rekursif (opsional)
- **Sertakan folder** (`--include-folders`): folder/direktori juga ikut
  diurutkan ke kategori "Folder"
- Auto-rename duplikat (penanda angka urut)
- Ringkasan per kategori di akhir proses
- Menu utama saat dijalankan tanpa argumen
- **Donasi** ❤️ — dukung proyek via [Sociabuzz](https://sociabuzz.com/trisnosanjaya) (dari menu atau `--donate`)
- Hanya dependensi standar Python (tanpa pip install)

## Penggunaan

```bash
python file_sorter.py
```

Akan muncul menu utama:

```
  1   Urutkan File
  2   Donasi ❤️
  3   Keluar
```

Pilih **1** untuk masuk ke mode interaktif pengurutan file,
**2** untuk membuka halaman donasi di browser, atau **3** untuk keluar.

Atau langsung kasih argumen untuk mode CLI:

```bash
python file_sorter.py --source /path/folder --destination /path/tujuan --mode move --recursive --include-folders
```

### Argumen CLI

| Argumen | Alias | Keterangan |
|---|---|---|
| `--source` | `-s` | Folder sumber yang dirapikan |
| `--destination` | `-d` | Folder tujuan (default: di dalam folder sumber) |
| `--mode` | `-m` | `move` (default) atau `copy` |
| `--recursive` | `-r` | Pindai semua subfolder |
| `--dry-run` | `-n` | Simulasi tanpa memindah/menyalin |
| `--config` | `-c` | Path file JSON konfigurasi kustom |
| `--include-folders` | `-f` | Sertakan folder (direktori) dalam pengurutan |
| `--interactive` | `-i` | Paksa mode interaktif (tidak wajib) |
| `--donate` | | Buka halaman donasi di browser |

### Mode Interaktif

Cukup jalankan:

```bash
python file_sorter.py
```

Pilih **1** (**Urutkan File**) dari menu, lalu program akan meminta:
1. Folder sumber
2. Folder tujuan (Enter untuk default: di dalam folder sumber)
3. Mode (move/copy, default: move)
4. Rekursif? (y/n)
5. Sertakan folder juga? (y/n)

### Contoh CLI

```bash
# Dry-run dulu
python file_sorter.py -s ./Downloads -d ./Sorted --dry-run --include-folders

# Buka halaman donasi
python file_sorter.py --donate
```

## Konfigurasi Kustom

Buat file JSON dengan format berikut:

```json
{
  "Gambar": [".jpg", ".png"],
  "Dokumen": [".pdf", ".txt"],
  "Folder": [],
  "Lainnya": []
}
```

Semua ekstensi otomatis dinormalisasi ke lowercase. Kategori `"Folder"`
dicocokkan secara otomatis untuk direktori.
