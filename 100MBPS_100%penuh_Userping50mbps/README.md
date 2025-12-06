# 📚 Simulasi Jaringan WiFi Perpustakaan (High Load Scenario)

Proyek ini mensimulasikan lingkungan jaringan perpustakaan menggunakan **Mininet-WiFi**. Skenario dirancang untuk menguji ketahanan jaringan "legacy" (standar lama) di bawah beban trafik yang sangat berat dan kepadatan pengguna yang bervariasi.

## 🛠️ Fitur & Skenario Pengujian

Berdasarkan kode `perpus_nlimit.py`, simulasi ini memiliki karakteristik "Realistis" sebagai berikut:

### 1. Model Propagasi Hambatan (Indoor)
* Menggunakan **LogDistance Propagation Model** dengan eksponen `exp=4`.
* **Tujuan:** Mensimulasikan lingkungan perpustakaan yang penuh dengan dinding tebal dan rak buku yang menghambat sinyal WiFi lebih parah daripada ruang terbuka.

### 2. Bottleneck Bandwidth (Skenario Perangkat Lama)
* **WiFi:** Menggunakan Mode 'g' (802.11g) dengan kecepatan teoritis maksimal 54 Mbps.
* **Kabel (Backhaul):** Link antara Access Point (AP) dan Switch dibatasi pada **100 Mbps** dengan delay buatan **5ms**.
* **Tujuan:** Meniru kondisi jaringan sekolah/kampus lama yang belum di-upgrade ke Gigabit atau WiFi 6.

### 3. Mobilitas & Kepadatan
* **Model Pergerakan:** `RandomWayPoint` (User berjalan acak, berhenti sejenak, lalu jalan lagi) dengan kecepatan berjalan santai (0.5 - 1.2 m/s).
* **Variasi User:** Diuji pada 5, 10, 15, 20, 50, hingga 100 user (visitor).

### 4. Traffic Chaos (Gangguan Latar Belakang)
* Fitur `start_noise`: Semua user (kecuali penguji) melakukan **Ping Flood** (interval 0.2 detik) ke jaringan.
* **Tujuan:** Menciptakan "noise" trafik broadcast/multicast yang tinggi untuk membebani CPU switch dan airtime WiFi.

## 💡 Analisis Mendalam

### 1. Throughput & Packet Loss (Bottleneck WiFi G)
* [cite_start]**Fakta:** Di semua skenario (5 s.d 100 user), packet loss konsisten di angka **~79%**[cite: 11, 22, 35, 46, 60, 71].
* **Analisis:** Ini terjadi bukan karena jumlah user, melainkan keterbatasan teknologi.
    * Pengujian memaksa trafik **50 Mbps**.
    * Standar **WiFi 802.11g** memiliki *theoretical speed* 54 Mbps, namun *real-world throughput* biasanya hanya **20-25 Mbps**.
    * Karena simulasi juga menyalakan "Noise" (ping dari user lain) dan model dinding tebal, bandwidth efektif turun drastis menjadi sekitar **10 Mbps** (20% dari 50 Mbps yang dikirim).
    * **Kesimpulan:** Jaringan kolaps secara *bandwidth* sejak awal karena beban pengujian melebihi kapasitas fisik Access Point.

### 2. Latency "Break Point" (Titik Kritis)
* **Stabil (5-20 User):** Rata-rata latency masih sangat bagus (4ms - 6ms). [cite_start]Jaringan masih mampu menangani antrian paket (queue) meskipun bandwidth penuh[cite: 5, 16, 40, 65].
* [cite_start]**Lonjakan Ekstrem (50 User):** Terjadi lonjakan latency yang signifikan dari ~6ms menjadi **32ms** (naik 500%), dengan spike maksimum mencapai **119ms**[cite: 49, 51].
* **Analisis:**
    * Pada 50 user, CPU pada controller/switch virtual mulai kewalahan memproses *ARP request* dan *Ping Noise* dari 50 node secara bersamaan.
    * Terjadi fenomena **Bufferbloat** atau antrian panjang di Switch OVS karena banyaknya user yang berebut *Time Slot* WiFi.

### 3. Stabilitas Koneksi (Out-of-Order Datagrams)
* [cite_start]Pada 50 dan 100 user, laporan Iperf menunjukkan ratusan paket yang diterima **Out-of-Order** (tidak berurutan)[cite: 35, 60].
* Ini menandakan bahwa pada kepadatan tinggi, jaringan mengalami *severe congestion* (kemacetan parah), dimana paket harus dikirim ulang atau mengambil rute antrian yang berbeda, menyebabkan kualitas layanan (QoS) untuk aplikasi seperti Voice/Video call akan hancur (kresek-kresek/putus).

---

## 📝 Kesimpulan
Simulasi ini berhasil membuktikan bahwa:
1.  **Limitasi Hardware:** Access Point standar lama (Mode G) tidak mampu menangani beban modern (50 Mbps) terlepas dari jumlah usernya (Loss 79% konstan).
2.  **Skalabilitas:** Jaringan masih "bisa dipakai" untuk browsing ringan hingga **20 user**.
3.  **Titik Kegagalan:** Pada **50 user**, jaringan mengalami degradasi latency yang parah. Untuk lingkungan perpustakaan nyata dengan >50 pengunjung, **wajib** melakukan upgrade ke WiFi 5 (AC) atau WiFi 6 (AX) dan menggunakan manajemen bandwidth (QoS) untuk mencegah satu user menghabiskan semua bandwidth.
