# Simulasi Jaringan WiFi Skala Besar dengan Mininet-WiFi (Project Ultimate)

Skrip `ultimate.py` adalah alat otomasi pengujian jaringan berbasis Python yang menggunakan **Mininet-WiFi**. Skrip ini dirancang untuk mensimulasikan lingkungan jaringan kampus atau kantor yang padat (High Density) dengan fitur realisme tinggi, termasuk pergerakan user, noise trafik, dan pembagian VLAN.

## 🚀 Fitur Utama

Kode ini tidak hanya sekadar menghubungkan node, tetapi menerapkan berbagai mekanisme untuk mendekati kondisi dunia nyata:

1.  **Topology Automation:** Otomatis membangun, menguji, dan menghapus topologi untuk berbagai skenario jumlah user (5, 10, 15, 20, 50, hingga 100 user) dalam satu kali eksekusi.
2.  **VLAN Segmentation (IEEE 802.1Q):**
      * **VLAN 10 (Staff):** Terisolasi untuk keamanan.
      * **VLAN 20 (Visitor):** Jaringan publik untuk user tamu.
      * Implementasi menggunakan `ovs-vsctl` pada switch Open vSwitch.
3.  **Realistic Physics & Mobility:**
      * **Propagasi Sinyal:** Menggunakan model `LogDistance` dengan eksponen 4 (mensimulasikan lingkungan dengan banyak tembok/halangan).
      * **Mobilitas:** User bergerak menggunakan model `RandomWayPoint` (kecepatan acak antara 0.5 - 1.2 m/s), mensimulasikan orang berjalan.
4.  **Channel Management:** Menggunakan 3 Access Point (AP) dengan kanal non-overlapping (Ch 1, 6, 11) untuk meminimalkan interferensi sinyal antar AP.
5.  **Traffic Noise Generator (Chaos Load):**
      * 50% dari user yang tidak sedang diuji akan bertindak sebagai "pengganggu" dengan mengirimkan trafik *ping* secara acak di latar belakang. Ini mensimulasikan jaringan yang sedang sibuk (*busy network*).
6.  **Headless Mode:** Berjalan tanpa GUI (tanpa X11 forwarding) untuk efisiensi performa maksimal saat simulasi beban berat (100 user).

## ⚙️ Konfigurasi Kecepatan & QoS

Skrip ini menerapkan pembatasan bandwidth dan delay untuk mensimulasikan perangkat keras jaringan nyata:

| Parameter | Nilai Konfigurasi | Keterangan |
| :--- | :--- | :--- |
| **Link Bandwidth** | **100 Mbps** | Mensimulasikan kabel Fast Ethernet antara AP ke Switch. |
| **Link Delay** | **5 ms** | Latency tambahan buatan untuk meniru jarak kabel fisik. |
| **Iperf UDP Limit** | **25 Mbps** | *Injection Rate* dibatasi agar pengujian tidak membuat jaringan kolaps total (`-b 25M`). |
| **Queueing** | **HTB (Hierarchical Token Bucket)** | Digunakan untuk manajemen antrian trafik pada link. |

## 🛠️ Skenario Pengujian

Skrip akan melakukan *looping* otomatis untuk skenario berikut:

  * **Jumlah User:** `[5, 10, 15, 20, 50, 100]`
  * **Protokol:**
    1.  **TCP:** Mengukur throughput pengiriman data yang reliable.
    2.  **UDP:** Mengukur throughput, jitter, dan packet loss untuk trafik real-time (seperti video/voip).

## 📊 Alur Kerja Kode (`How it Works`)

Setiap kali skenario dijalankan (misal: Skenario 50 User), kode melakukan langkah-langkah berikut:

1.  **Cleanup:** Membersihkan sisa topologi lama (`mn -c`) agar RAM bersih.
2.  **Setup Topologi:**
      * Membuat Controller Remote, Switch, dan 3 AP.
      * Membuat Station (User) sesuai jumlah skenario.
      * Menetapkan IP (Staff: `10.x`, Guest: `20.x`) dan posisi awal.
3.  **Aktivasi VLAN:** Mengonfigurasi port switch untuk tagging VLAN 10 dan 20.
4.  **Start Mobility:** User mulai bergerak secara acak.
5.  **Start Noise:** Memilih 50% user acak untuk membanjiri jaringan dengan trafik *ping*.
6.  **Pengujian (Logging):**
      * **Ping Test:** Mengukur latency (RTT) selama 30 detik.
      * **Iperf Test:** Server dinyalakan di node tujuan, client mengirim trafik selama 30 detik.
7.  **Reporting:** Hasil log disimpan otomatis ke file `.txt` (contoh: `LAPORAN_UDP_50_USER.txt`).
8.  **Teardown:** Mematikan simulasi dan lanjut ke jumlah user berikutnya.

## 📋 Cara Menjalankan

Karena Mininet memerlukan akses ke network stack kernel, skrip harus dijalankan dengan root:

```bash
sudo python3 ultimate.py
```

*Pastikan Controller (Ryu/ONOS/POX) sudah berjalan di IP `192.168.56.105` (atau sesuaikan variabel `CONTROLLER_IP` di baris 11).*

-----

### Catatan Tambahan

File ini menghasilkan laporan mentah yang mencakup:

  * Statistik Ping (Min/Avg/Max/Mdev).
  * Log Server Iperf (Bandwidth, Transfer, Jitter, Datagram Loss).
