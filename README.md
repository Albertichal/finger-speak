# Finger Speak 🖐️🔊

Aplikasi Python real-time yang membaca gestur tangan lewat webcam, menampilkan teks di layar, dan **membacakannya dengan suara (text-to-speech)**. Kalau kedua tangan terdeteksi bersamaan, aplikasi menampilkan efek visual (thermal, neon, edges, invert, cyberpunk, mono) di sekitar tangan, lalu memutar video setelah animasi "SCANNING..." selesai.

Dibangun dengan **OpenCV** (kamera & rendering) dan **MediaPipe** (deteksi landmark tangan).

---

## Cara Kerja Singkat

| Kondisi | Yang terjadi |
|---|---|
| 1 tangan, jumlah jari 1–5 | Teks muncul di bawah layar + dibacakan (TTS) |
| 2 tangan terdeteksi | Efek visual muncul di kotak antar tangan, lalu animasi scan 3 detik, lalu video `recordings/IMG.MP4` diputar full-screen dengan audio |
| Tombol `q` | Keluar dari aplikasi |

Pemetaan jumlah jari → kalimat (bisa diubah di `GESTURES` dalam `main.py`):

```
1 jari  → "Sistem Information"
2 jari  → "From the"
3 jari  → "Aliya"
4 jari  → "My name is"
5 jari  → "Hello"
```

---

## 1. Yang Perlu Disiapkan (Prasyarat)

Project ini **paling mulus dijalankan di Windows** karena kodenya memanggil font `arial.ttf` secara langsung. Di Linux/Mac tetap bisa jalan (ada fallback font default), tapi tampilan teks akan sedikit berbeda.

Kamu butuh:
- Laptop/PC dengan **webcam**
- Koneksi internet (untuk download tools & library)
- Sekitar 30–45 menit untuk setup pertama kali

---

## 2. Install Visual Studio Code

Kalau belum ada VS Code:

1. Buka https://code.visualstudio.com/
2. Klik tombol **Download** sesuai OS kamu (Windows/Mac/Linux)
3. Jalankan installer, next-next sampai selesai
4. Saat instalasi (khusus Windows), centang opsi:
   - ✅ *Add to PATH*
   - ✅ *Register Code as an editor for supported file types*
5. Buka VS Code, install extension **Python** (buatan Microsoft) lewat tab Extensions (ikon kotak di sidebar kiri, `Ctrl+Shift+X`), cari "Python", klik Install.

---

## 3. Install Python

MediaPipe **belum stabil di Python versi paling baru**. Disarankan pakai **Python 3.10 atau 3.11**.

1. Buka https://www.python.org/downloads/release/python-3110/ (atau versi 3.10)
2. Scroll ke bawah, download installer sesuai OS (misal *Windows installer (64-bit)*)
3. Jalankan installer:
   - ✅ **WAJIB centang "Add python.exe to PATH"** di halaman pertama installer
   - Klik "Install Now"
4. Cek instalasi berhasil, buka Terminal/Command Prompt, ketik:
   ```bash
   python --version
   ```
   Harus muncul `Python 3.10.x` atau `3.11.x`.

---

## 4. Install Git (opsional, untuk clone repo)

Kalau belum punya Git:

1. Download di https://git-scm.com/downloads
2. Install dengan pengaturan default (next-next-finish)
3. Cek dengan:
   ```bash
   git --version
   ```

> Kalau malas install Git, kamu bisa langsung download ZIP repo dari GitHub: buka https://github.com/Albertichal/finger-speak → tombol hijau **Code** → **Download ZIP** → extract.

---

## 5. Install FFmpeg (WAJIB untuk audio video)

Program ini butuh `ffmpeg` untuk mengekstrak audio dari `recordings/IMG.MP4`. Tanpa ini, video tetap main tapi **tanpa suara**.

### Windows
1. Buka https://www.gyan.dev/ffmpeg/builds/ → download **ffmpeg-release-essentials.zip**
2. Extract ke folder, misal `C:\ffmpeg`
3. Tambahkan `C:\ffmpeg\bin` ke Environment Variable **PATH**:
   - Ketik "Environment Variables" di Start Menu → *Edit the system environment variables*
   - Klik **Environment Variables** → pilih `Path` di *System variables* → **Edit** → **New** → masukkan `C:\ffmpeg\bin`
   - OK semua
4. Buka Command Prompt **baru**, cek:
   ```bash
   ffmpeg -version
   ```

### macOS
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

---

## 6. Clone / Download Project

Buka Terminal (atau Terminal di dalam VS Code: `Ctrl+`` `), lalu:

```bash
git clone https://github.com/Albertichal/finger-speak.git
cd finger-speak
```

Kalau pakai ZIP: extract, lalu `cd` ke folder hasil extract-nya.

Buka folder ini di VS Code:
```bash
code .
```

---

## 7. Buat Virtual Environment (disarankan)

Supaya library project ini tidak bentrok dengan project Python lain:

```bash
python -m venv venv
```

Aktifkan:
- **Windows (cmd):**
  ```bash
  venv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```bash
  venv\Scripts\Activate.ps1
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

Kalau berhasil, di depan baris terminal akan muncul `(venv)`.

---

## 8. Install Dependencies

Repo aslinya **tidak menyertakan `requirements.txt`**, jadi buat file baru bernama `requirements.txt` di root folder project, isi dengan:

```
opencv-python
mediapipe
numpy
Pillow
pyttsx3
pygame
moviepy
```

Lalu install semua sekaligus:

```bash
pip install -r requirements.txt
```

> ⚠️ Catatan versi: MediaPipe kadang belum support Python versi paling baru (misal 3.13). Kalau `pip install mediapipe` gagal, itu tandanya versi Python kamu terlalu baru — install Python 3.10/3.11 lalu ulangi dari langkah venv.

### Khusus Linux — suara TTS
`pyttsx3` di Linux butuh backend `espeak`:
```bash
sudo apt install espeak
```

---

## 9. Siapkan File Video

Program memutar file `recordings/IMG.MP4`. Pastikan foldernya ada:

```
finger-speak/
├── main.py
├── requirements.txt
└── recordings/
    └── IMG.MP4
```

Kalau clone dari GitHub, folder `recordings` sudah ikut ter-clone. Kalau file `IMG.MP4` kosong/tidak ada, aplikasi tetap jalan untuk deteksi 1 tangan, tapi bagian 2-tangan tidak akan memutar apa-apa (tidak crash, hanya diam).

---

## 10. Jalankan Program

Pastikan masih di folder project dan venv aktif, lalu:

```bash
python main.py
```

- Window kamera akan terbuka fullscreen
- Angkat 1 tangan, tunjukkan 1–5 jari → teks + suara muncul
- Angkat 2 tangan berdekatan → efek visual → scan → video muncul
- Tekan **`q`** untuk keluar

---

## 11. Troubleshooting

| Masalah | Solusi |
|---|---|
| `Kamera tidak bisa dibuka` | Pastikan tidak ada aplikasi lain (Zoom, Teams, dll) yang memakai webcam. Coba ganti `cv2.VideoCapture(0)` jadi `cv2.VideoCapture(1)` di `main.py` kalau punya lebih dari 1 kamera. |
| `ModuleNotFoundError: No module named 'cv2'` dsb | Venv belum aktif, atau `pip install -r requirements.txt` belum dijalankan/gagal. |
| Tidak ada suara video | `ffmpeg` belum terinstall/tidak ada di PATH. Cek dengan `ffmpeg -version`. |
| Tidak ada suara TTS (Linux) | Install `espeak`: `sudo apt install espeak`. |
| Font terlihat aneh / kotak-kotak | Wajar di Linux/Mac, kode hardcode `arial.ttf` (font Windows). Bisa diedit di fungsi `draw_custom_text()` untuk pakai font lain, misal DejaVuSans. |
| `pip install mediapipe` gagal | Kemungkinan versi Python kamu tidak didukung MediaPipe. Gunakan Python 3.10 atau 3.11. |
| Instalasi `mediapipe`/`opencv` lambat/gagal di Windows lama | Update `pip` dulu: `python -m pip install --upgrade pip`. |

---

## 12. Struktur Project

```
finger-speak/
├── main.py            # seluruh logika aplikasi (kamera, deteksi, TTS, efek, video)
├── requirements.txt   # daftar library (dibuat manual, tidak ada di repo asli)
└── recordings/
    └── IMG.MP4        # video yang diputar saat 2 tangan terdeteksi
```

---

## Kredit

Dibuat oleh [Albertichal](https://github.com/Albertichal). README ini disusun berdasarkan analisis kode `main.py` karena repo asli belum memiliki dokumentasi.
