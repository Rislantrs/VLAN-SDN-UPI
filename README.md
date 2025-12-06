
# 📘 Panduan Simulasi Jaringan Perpustakaan (Hardcore Mode)

Dokumen ini berisi panduan lengkap untuk menjalankan simulasi topologi jaringan WiFi menggunakan Mininet-WiFi dengan kontrol manual (CLI). Mode ini memungkinkan Anda memanipulasi jaringan (bandwidth, delay, packet loss) secara *real-time* layaknya administrator jaringan.

-----

## 🛠️ Bagian 1: Persiapan Environment

Sebelum menjalankan simulasi, pastikan Anda bekerja di dalam *Virtual Environment* (Venv) agar instalasi Python tidak berantakan, dan Controller Ryu sudah terinstall.

### 1\. Membuat & Mengaktifkan Venv

Buka terminal baru, lalu jalankan perintah berikut:

```bash
# 1. Install paket venv (jika belum ada)
sudo apt install python3-venv

# 2. Membuat virtual environment bernama 'mn_env'
python3 -m venv mn_env

# 3. Mengaktifkan venv (Wajib dilakukan setiap kali membuka terminal baru)
source ~/.venvs/ryu/bin/activate
```

### 2\. Menginstall Ryu & Mininet-WiFi

Jika belum terinstall di dalam venv:

```bash
pip install ryu mininet-wifi
```

-----

## 🎮 Bagian 2: Menjalankan Controller (Terminal 1)

Kita membutuhkan "otak" jaringan agar Switch bisa bekerja. Kita akan menggunakan **Ryu Controller**.

1.  Buka **Terminal Baru**.
2.  Aktifkan venv: 
3.  Jalankan Controller:

<!-- end list -->

```bash
ryu-manager vlan_sw.py ryu.app.gui_topology.gui_topology
```

*Penjelasan: Ini menjalankan aplikasi switch dasar OpenFlow 1.3. Biarkan terminal ini terbuka dan jangan ditutup.*

-----

## 🚀 Bagian 3: Menjalankan Topologi (Terminal 2)

Ini adalah langkah untuk memulai simulasi topologi Mininet.

### ⚠️ Solusi Masalah Bahasa (Pingall Error)

Jika laptop Anda menggunakan Bahasa Indonesia, perintah `pingall` akan error (not parsed) karena outputnya "Paket hilang" bukan "Packet loss".

**Gunakan perintah ini untuk menjalankannya:**

```bash
# Masuk ke folder project dulu
cd /path/to/project/

# Jalankan dengan LC_ALL=C (Memaksa bahasa sistem jadi Inggris sementara)
sudo LC_ALL=C python3 perpus_manual.py
```

Tunggu hingga muncul prompt: `mininet-wifi>`. Sekarang Anda siap mengetik perintah manual\!

-----

## 📜 Bagian 4: Cheat Sheet Perintah Manual (CLI)

Berikut adalah daftar perintah yang bisa Anda ketik di `mininet-wifi>`.

### A. Cek Koneksi Dasar 📡

| Perintah | Penjelasan |
| :--- | :--- |
| `nodes` | Melihat daftar semua perangkat (AP, Switch, Host). |
| `h1 ping h2` | Tes koneksi sesama Staff (VLAN 10). |
| `h1 ping guest1` | **Tes Keamanan:** Harus GAGAL (RTO) karena beda VLAN. |
| `pingall` | Tes koneksi masal antar semua host. |
| `net` | Melihat susunan kabel/link antar perangkat. |

### B. Tes Kecepatan (Iperf) 🚀

**PENTING:** Siapkan Server terlebih dahulu sebelum Client menembak.

  * **TCP:** Stabil, speed naik-turun sesuai kondisi.
  * **UDP:** Maksa, cocok untuk simulasi streaming/serangan.

**1. Menyiapkan Server (Penerima)**

```bash
# Mode TCP Standard
guest5 iperf -s &

# Mode UDP (Wajib tambah -u)
guest5 iperf -s -u &
```

**2. Menjalankan Client (Pengirim)**

```bash
# Skenario 1: Download Biasa (TCP)
guest1 iperf -c 192.168.20.5

# Skenario 2: Simulasi User Dilimit (Misal cuma dikasih 2 Mbps)
guest1 iperf -c 192.168.20.5 -b 2M

# Skenario 3: Serangan Full Speed / Streaming 4K (UDP)
# Wajib pakai -u dan -b (target bandwidth)
guest1 iperf -c 192.168.20.5 -u -b 100M
```

### C. Skenario "Hardcore" (Manipulasi Jaringan Live) 🔧

Perintah ini menggunakan `py` untuk mengubah konfigurasi kabel secara langsung.

#### 1\. Perebutan Bandwidth (Congestion)

Simulasi saat banyak user download barengan.

```bash
# 1. Jalankan download user 1 (durasi 20 detik)
guest1 iperf -c 192.168.10.1 -t 20 &

# 2. Langsung jalankan user 2
guest2 iperf -c 192.168.10.1 -t 20
```

*Hasil: Speed kedua user akan anjlok (terbagi dua).*

#### 2\. Ubah Bandwidth Switch (Throttling)

Membuat kabel AP Visitor ke Switch jadi lemot (misal 5 Mbps).

```bash
# Set jadi 5 Mbps
py net.linksBetween(net.get('ap3'), net.get('s1'))[0].intf1.config(bw=5)

# Kembalikan ke 1000 Mbps (Normal)
py net.linksBetween(net.get('ap3'), net.get('s1'))[0].intf1.config(bw=1000)
```

#### 3\. Simulasi Kabel Rusak (Packet Loss)

Membuat jaringan putus-nyambung (loss 50%).

```bash
# Rusakin kabel
py net.linksBetween(ap2, s1)[0].intf1.config(loss=50)

# Cek efeknya (Pasti banyak RTO)
guest1 ping -c 10 h1

# Perbaiki kabel
py net.linksBetween(ap2, s1)[0].intf1.config(loss=0)
```

#### 4\. Simulasi Lag (High Latency/Delay)

Simulasi ping bengkak (misal delay 500ms).

```bash
# Tambah delay
py net.linksBetween(ap2, s1)[0].intf1.config(delay='500ms')

# Cek ping (Pasti jadi 1000ms+)
guest1 ping -c 3 h1

# Hapus delay
py net.linksBetween(ap2, s1)[0].intf1.config(delay='1ms')
```

#### 5\. Simulasi Kabel Putus (Link Failure)

Memutuskan koneksi host secara total.

```bash
# Cabut kabel h1
py net.get('ap2').stop()

# Pasang kabel h1
py net.get('ap2').start([net.get('c0')])
```

#### 6\. Simulasi User Jalan-jalan (Mobilitas)

Memindahkan posisi user menjauh dari WiFi.

```bash
# Pindah ke koordinat jauh (Sinyal hilang)
py guest1.setPosition('2000,2000,0')

# Cek ping (Harus RTO)
guest1 ping h1

# Pindah balik ke dekat AP
py guest1.setPosition('65,30,0')
```

#### 7\. Menampilkan Grafik

Jika grafik tertutup, panggil lagi dengan:

```bash
py net.plotGraph(max_x=100, max_y=100)
```

#### 8\. Penyadapan Paket (Sniffing)

Melihat paket yang lewat di h1.

```bash
# Jalankan tcpdump di h1
h1 tcpdump -i h1-eth0

# (Di terminal lain/background) Kirim ping
guest1 ping -c 5 h1 &
```

*(Tekan Ctrl+C di terminal mininet untuk stop tcpdump)*
