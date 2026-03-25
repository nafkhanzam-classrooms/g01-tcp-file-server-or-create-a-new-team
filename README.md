[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Nama                   | NRP          | Kelas                |
| ---------------------- | ------------ | -------------------- |
| Farikh Muhammad Fauzan | 5025241135   | D                    |
| Bara Semangat Rohmani  | 5025241144   | D                    |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```

```

## Penjelasan Program
Aplikasi ini adalah sebuah TCP File Server & Terminal Chatroom yang dibangun menggunakan bahasa Python. Klien dapat saling bertukar pesan (broadcast) serta mengelola file di dalam server (upload, download, dan melihat daftar file).

Program ini terdiri dari **1 File Client** (`[0]-Client.py`) dan **4 File Server** yang memiliki fitur identik, namun dirancang dengan pendekatan arsitektur *concurrency* yang berbeda-beda untuk membandingkan tingkat efisiensi alokasi memorinya:

1.  **`[2]-Server-Sync.py` (Synchronous / Blocking):** Pendekatan paling dasar. Server hanya melayani satu klien dalam satu waktu. Klien lain yang mencoba masuk harus mengantre hingga klien pertama memutus koneksi.
2.  **`[3]-Server-Thread.py` (Multithreading):** Menggunakan modul `threading`. Sistem operasi akan menciptakan *thread* baru secara eksklusif untuk setiap klien yang terhubung. Sangat stabil, namun rakus memori jika menangani banyak koneksi secara masif.
3.  **`[1]-Server-Select.py` (I/O Multiplexing - Select):** Menggunakan modul `select` untuk memantau aktivitas (Read/Write) dari banyak *socket* sekaligus menggunakan satu *thread* tunggal (Event Loop). Jauh lebih hemat resource dibandingkan Multithreading dan bersifat *cross-platform*.
4.  **`[4]-Server-Poll.py` (I/O Multiplexing - Poll):** Menggunakan *syscall* `poll` yang spesifik berjalan di OS berbasis UNIX/Linux (kami mengujinya melalui subsistem Arch Linux WSL). Menawarkan performa pengawasan *file descriptor* yang lebih superior dan efisien dibandingkan `select` untuk skala koneksi yang sangat besar.

**Fitur & Protokol:**
Untuk membedakan antara pesan chat biasa dan transfer file, program ini menggunakan separator khusus `<SEP>`.

  * **`/list`**: Server menggunakan `os.listdir()` untuk mengirim daftar nama file di direktori server.
  * **`/upload <filename>`**: Klien mengirim header `f"/upload<SEP>filename<SEP>filesize"`, diikuti dengan pengiriman *byte chunk* dari file lokal.
  * **`/download <filename>`**: Klien meminta file. Jika ada, server merespons dengan header `FILE_INCOME` lalu menembakkan *byte chunk* file tersebut untuk ditulis oleh klien secara lokal.

## Screenshot Hasil
