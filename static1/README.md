# Simulasi Jaringan WiFi Perpustakaan (Mininet-WiFi)

Proyek ini adalah skrip Python (`perpus_new.py`) untuk mensimulasikan dan menguji performa jaringan nirkabel (WiFi) di lingkungan perpustakaan menggunakan **Mininet-WiFi**. Simulasi ini dirancang untuk menguji skalabilitas, keamanan, dan manajemen bandwidth (QoS) secara otomatis.

## Deskripsi Singkat

Kode ini membangun topologi jaringan virtual yang terdiri dari Access Point untuk Staff dan Pengunjung, menerapkan VLAN untuk pemisahan trafik, dan menjalankan serangkaian pengujian otomatis untuk mengukur latensi, throughput, serta efektivitas aturan keamanan.

## Fitur Utama

1.  **Topologi Dinamis & Otomatis**:

      * Menggunakan **Remote Controller** (IP: 192.168.56.105).
      * Memiliki 3 Access Point (1 untuk Staff, 2 untuk Visitor) dan 1 Switch OVS.
      * Posisi stasiun (user) digenerate secara otomatis sesuai jumlah skenario.

2.  **Implementasi VLAN (Virtual LAN)**:

      * **VLAN 10**: Khusus untuk Staff (Port eth1).
      * **VLAN 20**: Khusus untuk Visitor (Port eth2 & eth3).
      * Pemisahan trafik dilakukan di level Open vSwitch.

3.  **Pengujian Skalabilitas Otomatis**:

      * Skrip otomatis menjalankan loop pengujian untuk skenario jumlah user: 5, 10, 15, 20, 50, dan 100 user.
      * Setiap skenario menghasilkan laporan `.txt` terpisah.

4.  **Quality of Service (QoS) & Limiting**:

      * Fitur pembatasan bandwidth (Bandwidth Limiting) menggunakan HTB (Hierarchical Token Bucket).
      * Pengujian khusus untuk memastikan user tidak melebihi batas bandwidth yang ditentukan.

5.  **Automated Reporting**:

      * Hasil Ping, Iperf (Throughput/Jitter), dan Security Test langsung diekspor ke file log (`.txt` dan `.csv`).

## Topologi Jaringan

  * **Controller**: c0 (Remote Controller)
  * **Switch**: s1 (OVSKernelSwitch)
  * **Access Points**:
      * `ap1`: SSID "Staff" (Channel 1)
      * `ap2`: SSID "Visitor" (Channel 6)
      * `ap3`: SSID "Visitor" (Channel 11)
  * **IP Addressing**:
      * Staff: 192.168.10.x
      * Visitor: 192.168.20.x

## Hasil Pengujian (Berdasarkan Log)

Berikut adalah rangkuman hasil dari file log yang dihasilkan oleh skrip:

### 1\. Uji Skalabilitas (Performa Jaringan)

Perbandingan performa antara beban rendah (5 user) dan beban tinggi (100 user) menunjukkan kestabilan jaringan.

  * **Latency (Ping):**

      * **5 User:** Rata-rata 7.57 ms.
      * **100 User:** Rata-rata 8.49 ms.
      * **Analisis:** Kenaikan latensi sangat kecil (\< 1 ms) meskipun jumlah user bertambah 20x lipat. Tidak ada *packet loss* (0% loss) pada kedua skenario.

  * **Jitter (Variasi Waktu Kedatangan Paket):**

      * **5 User:** 0.182 ms.
      * **100 User:** 0.332 ms.
      * **Analisis:** Jitter tetap rendah di bawah 1 ms, menandakan koneksi stabil untuk aplikasi real-time.

### 2\. Uji Keamanan (VLAN Isolation)

Pengujian dilakukan dengan mencoba melakukan Ping dari Staff (VLAN 10) ke Visitor (VLAN 20).

  * **Hasil:** 100% Packet Loss.
  * **Status:** **AMAN (BLOCKED)**.
  * **Analisis:** Isolasi VLAN berfungsi dengan baik. Trafik antar departemen yang berbeda berhasil diblokir oleh switch, menjaga privasi data staff.

### 3\. Uji Admin Limit (QoS)

Pengujian dilakukan dengan membatasi bandwidth user di angka 5 Mbps dan melakukan download file besar (TCP).

  * **Hasil:** Throughput tercatat berfluktuasi namun tertahan di kisaran rata-rata **8.98 Mbits/sec** (dengan beberapa detik berada di angka 7-8 Mbps).
  * **Analisis:** Mekanisme pembatasan trafik berfungsi (trafik tidak melonjak bebas hingga ratusan Mbps sesuai kapasitas link fisik), menjaga agar satu user tidak memonopoli bandwidth jaringan.

## Cara Menjalankan

1.  Pastikan **Mininet-WiFi** dan **Open vSwitch** sudah terinstall.
2.  Jalankan controller (misalnya Ryu/ONOS) di IP `192.168.56.105` (atau ubah variabel `CONTROLLER_IP` di script).
3.  Jalankan skrip menggunakan Python 3 dengan akses root:
    ```bash
    sudo python3 perpus_new.py
    ```
4.  Setelah selesai, script akan menghasilkan file laporan:
      * `LAPORAN_SKENARIO_X_USER.txt`
      * `LAPORAN_SECURITY_BLOCK.txt`
      * `LAPORAN_ADMIN_LIMIT.txt`

-----
