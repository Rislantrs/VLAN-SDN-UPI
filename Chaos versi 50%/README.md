# Simulasi Jaringan WiFi High-Density dengan Chaos Engineering

Proyek ini adalah simulasi jaringan WiFi perpustakaan menggunakan **Mininet-WiFi**. Simulasi ini dirancang untuk menguji ketahanan jaringan (Network Resilience) dalam kondisi beban tinggi yang realistis (*Chaos Mode*), di mana pengguna tidak hanya diam, tetapi bergerak dan menghasilkan trafik data secara aktif.

Tujuan utama simulasi adalah mengukur performa jaringan (Latency & Jitter) saat jumlah pengguna meningkat dari kondisi sepi hingga sangat padat.

## 🌟 Fitur Utama

Berikut adalah fitur teknis yang diimplementasikan dalam skrip `perpus_chaos.py`:

### 1\. Topologi Realistis

  * **Multi-AP Deployment:** Menggunakan 3 Access Point (AP) untuk membagi beban trafik:
      * `AP1` (Staff - Channel 1)
      * `AP2` & `AP3` (Visitor - Channel 6 & 11) untuk meminimalkan interferensi.
  * **VLAN Configuration:** Segmentasi trafik menggunakan VLAN tagging pada switch (VLAN 10 untuk Staff, VLAN 20 untuk Visitor).

### 2\. Model Fisika & Mobilitas

  * **Signal Propagation:** Menggunakan model `LogDistance` dengan eksponen 4, mensimulasikan lingkungan dalam gedung dengan tembok tebal yang menghalangi sinyal.
  * **Mobilitas User:** Menggunakan model `RandomWayPoint`, di mana user bergerak secara acak di dalam area perpustakaan dengan kecepatan bervariasi, mensimulasikan perilaku pengunjung nyata.

### 3\. Chaos Mode (Traffic Generator)

Fitur unggulan dari proyek ini adalah mekanisme **Background Traffic**:

  * Secara otomatis memilih 50% dari total user sebagai "pengganggu".
  * User "pengganggu" akan melakukan *flooding* trafik (ping flood ringan) ke jaringan secara bersamaan saat pengukuran berlangsung.
  * Ini memastikan hasil tes mencerminkan kondisi jaringan yang sibuk, bukan jaringan lab yang ideal.

-----

## 📋 Skenario Pengujian

Pengujian dilakukan secara otomatis dengan parameter berikut:

  * **Load Background:** 50% user aktif menghasilkan trafik sampah (noise).
  * **Durasi Test:** 30 detik per skenario.
  * **Limit Bandwidth:** Setiap link dibatasi (Throttling) untuk melihat efek bottleneck.

**Variasi Jumlah User (Scalability Test):**

1.  **5 User:** Kondisi sangat sepi.
2.  **10 User:** Kondisi sepi.
3.  **15 User:** Kondisi normal ringan.
4.  **20 User:** Kondisi normal.
5.  **50 User:** Kondisi ramai (High Density).
6.  **100 User:** Kondisi sangat padat (Extreme Density).

-----

## 📊 Hasil Analisis Data

Berdasarkan log laporan yang dihasilkan, berikut adalah ringkasan performa jaringan. Data diambil dari pengujian Latency (Ping) dan Quality of Service (Jitter via Iperf).

### Ringkasan Metrik

| Skenario (Jml User) | Avg Latency (ms) | Max Latency (ms) | Avg Jitter (ms) | Keterangan Status |
| :---: | :---: | :---: | :---: | :--- |
| **5 User** | 4.38 ms | 8.04 ms | 0.726 ms | 🟢 **Sangat Stabil**. Tidak ada antrean paket berarti. |
| **10 User** | 4.69 ms | 9.93 ms | 0.359 ms | 🟢 **Stabil**. Penambahan user belum membebani AP. |
| **15 User** | 5.51 ms | 11.13 ms | 0.430 ms | 🟢 **Stabil**. Latency mulai naik sedikit namun wajar. |
| **20 User** | 6.04 ms | 12.41 ms | 0.858 ms | 🟡 **Normal**. Mulai terlihat fluktuasi jitter. |
| **50 User** | **16.82 ms** | **76.79 ms** | 0.805 ms | 🔴 **Heavy Load**. Terjadi lonjakan latency signifikan (spikes). |
| **100 User** | 9.46 ms | 17.54 ms | 1.431 ms | 🔴 **Saturated**. Jitter tertinggi, menandakan variasi delay paket yang besar. |

### Analisis Mendalam

1.  **Titik Jenuh (Saturation Point):** Jaringan mulai mengalami degradasi performa yang nyata pada skenario **50 User**. Terlihat dari rata-rata latency yang melonjak hingga 3x lipat dibandingkan skenario 20 user, dengan lonjakan maksimal (spike) mencapai 76ms.
2.  **Stabilitas Jitter:** Meskipun latency naik, mekanisme buffer UDP (Iperf) masih mampu menjaga jitter di bawah 2ms bahkan pada 100 user. Ini menunjukkan streaming video kualitas rendah mungkin masih berjalan, namun aplikasi *real-time* (seperti VoIP/Game) akan terasa *laggy*.
3.  **Packet Loss:** Pada semua skenario, Packet Loss tercatat **0%**. Ini menandakan antrean (queue) di Switch/AP masih mampu menampung paket meskipun terjadi delay pengiriman.

-----

## 🚀 Cara Menjalankan Simulasi

Simulasi ini membutuhkan akses `root` karena Mininet berinteraksi langsung dengan kernel jaringan Linux.

1.  **Prasyarat:**

      * Ubuntu/Linux VM.
      * Python 3.
      * Mininet-WiFi terinstal.

2.  **Jalankan Script:**

    ```bash
    sudo python3 perpus_chaos.py
    ```

3.  **Output:**
    Script akan secara otomatis:

      * Membuat topologi.
      * Menjalankan skenario 5 s.d 100 user secara berurutan.
      * Menghasilkan file log individu (misal: `LAPORAN_CHAOS_50_USER.txt`).
      * Membersihkan proses (kill ping/iperf) setelah setiap tes selesai.

secara lokal.*
