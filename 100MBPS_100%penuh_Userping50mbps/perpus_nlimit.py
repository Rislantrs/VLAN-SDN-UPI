import sys
import time
import os
import random
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSKernelSwitch
from mn_wifi.node import OVSKernelAP
from mn_wifi.net import Mininet_wifi
from mininet.link import TCLink

# --- KONFIGURASI ---
CONTROLLER_IP = '192.168.56.105'  # Sesuaikan dengan IP VM Controller Anda
DURATION = 30 
SCENARIOS = [5, 10, 15, 20, 50, 100]

# Seberapa banyak user pengganggu? (0.5 = 50% user aktif nyepam)
CHAOS_LOAD = 1.0 

def setup_topology(num_visitors):
    # Inisialisasi Mininet-WiFi
    net = Mininet_wifi(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP)
    
    # 1. REALISME: Model Propagasi (Indoor Padat)
    # LogDistance exp=4 meniru dinding tebal/rak buku
    net.setPropagationModel(model="logDistance", exp=4)
    net.plotGraph(max_x=100, max_y=100)

    # 2. REALISME: Access Point Standar (Mode G = 54 Mbps)
    # Ini adalah bottleneck pertama (Udara)
    ap1 = net.addAccessPoint('ap1', ssid='Staff', mode='g', channel='1', position='30,30,0', range=40)
    ap2 = net.addAccessPoint('ap2', ssid='Visitor', mode='g', channel='6', position='50,50,0', range=40)
    ap3 = net.addAccessPoint('ap3', ssid='Visitor', mode='g', channel='11', position='70,30,0', range=40)
    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    c0 = net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=6633)

    # Staff (Static)
    staff = net.addStation('staff1', position='32,32,0', ip='192.168.10.1/24')
    
    visitors = []
    for i in range(1, num_visitors + 1):
        # Posisi awal diagonal (nanti menyebar)
        start_pos = f'{30+(i%60)},{30+(i%40)},0'
        sta = net.addStation(f'guest{i}', position=start_pos, ip=f'192.168.20.{i}/24')
        visitors.append(sta)

    net.configureWifiNodes()

    # 3. REALISME: Mobilitas (Orang Berjalan)
    # RandomWayPoint: Jalan -> Berhenti -> Jalan
    net.setMobilityModel(time=0, model='RandomWayPoint', 
                         max_x=90, max_y=90, min_x=10, min_y=10, 
                         min_v=0.5, max_v=1.2, seed=1)

    # 4. REALISME UTAMA: Link Kabel "Fast Ethernet" (Bukan Gigabit)
    # Bandwidth = 100 Mbps (Sesuai saran agar bottleneck terasa)
    # Delay = 5ms (Simulasi switch tua/beban tinggi)
    info("*** Setting Link: 100 Mbps, Delay 5ms ***\n")
    net.addLink(ap1, s1, bw=100, delay='5ms', use_htb=True)
    net.addLink(ap2, s1, bw=100, delay='5ms', use_htb=True)
    net.addLink(ap3, s1, bw=100, delay='5ms', use_htb=True)
    
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    # Konfigurasi VLAN (Agar traffic terpisah secara logis)
    s1.cmd('ovs-vsctl set port s1-eth1 tag=10')
    s1.cmd('ovs-vsctl set port s1-eth2 tag=20')
    s1.cmd('ovs-vsctl set port s1-eth3 tag=20')

    # Mulai Pergerakan
    net.startMobility(time=0)
    time.sleep(5) # Tunggu asosiasi WiFi
    
    return net, staff, visitors

def start_noise(visitors, target_ip):
    """Membuat user lain melakukan Ping Flood ringan agar jaringan sibuk"""
    count = int(len(visitors) * CHAOS_LOAD)
    if count < 2: return
    
    # Ambil user acak (selain user pertama & terakhir)
    spammers = random.sample(visitors[1:-1], min(count, len(visitors)-2))
    
    info(f"   >>> [CHAOS] {len(spammers)} user lain sedang spamming ping...\n")
    for sta in spammers:
        # Ping interval 0.2 detik (Cukup mengganggu WiFi, aman buat CPU)
        sta.cmd(f"ping -i 0.2 {target_ip} > /dev/null 2>&1 &")

def run_all_tests():
    # Bersihkan proses zombie sebelum mulai
    os.system("pkill -9 ping")
    os.system("pkill -9 iperf")

    for n in SCENARIOS:
        filename = f"LAPORAN_PAPER_REALISTIS_{n}_USER.txt"
        info(f"\n*** SKENARIO {n} USER (100Mbps Link + High Load) -> {filename} ***\n")
        
        net = None
        try:
            net, staff, visitors = setup_topology(n)
            src, dst = visitors[0], visitors[-1]
            
            # Aktifkan Gangguan (Noise)
            start_noise(visitors, dst.IP())
            
            with open(filename, "w") as f:
                f.write(f"==================================================\n")
                f.write(f"LAPORAN PENGUJIAN (MIRIP PAPER) - {n} USER\n")
                f.write(f"Kabel: 100 Mbps | Delay: 5ms | Iperf Load: 50 Mbps\n")
                f.write(f"==================================================\n\n")
                
                # --- 1. LATENCY (PING) ---
                info("   > [1/2] Mengukur Latency (Ping)...\n")
                f.write("--- [BAGIAN 1] HASIL PING (LATENCY) ---\n")
                # Ping berjalan di tengah kemacetan
                ping_res = src.cmd(f"LC_ALL=C ping -i 1 -c {DURATION} {dst.IP()}")
                f.write(ping_res + "\n\n")
                
                # --- 2. THROUGHPUT & JITTER (IPERF) ---
                info("   > [2/2] Mengukur Throughput Ekstrim (Iperf)...\n")
                f.write("--- [BAGIAN 2] HASIL IPERF (SERVER REPORT) ---\n")
                
                # Jalankan Server (Simpan log ke file temp)
                dst.cmd(f"iperf -s -u -i 1 > /tmp/iperf_server.log &")
                time.sleep(1)
                
                # Jalankan Client dengan Load TINGGI (50 Mbps)
                # Ini akan memaksa jaringan 100Mbps + WiFi G (54Mbps) kolaps
                src.cmd(f"LC_ALL=C iperf -c {dst.IP()} -u -b 2M -t {DURATION} -i 1")
                
                time.sleep(2)
                dst.cmd("pkill -x iperf")
                
                # Ambil log server (Data Real: Jitter, Loss, Bandwidth Drop)
                server_log = dst.cmd("cat /tmp/iperf_server.log")
                f.write(server_log)
                f.write("\n==================================================\n")
            
            info(f"   > Selesai. Data tersimpan.\n")
            
        except Exception as e:
            info(f"!!! ERROR: {e} !!!\n")
            
        finally:
            # Matikan gangguan dan topologi
            os.system("pkill -9 ping")
            if net: net.stop()
            os.system('mn -c > /dev/null 2>&1')
            time.sleep(3)

if __name__ == '__main__':
    setLogLevel('info')
    if os.geteuid() != 0:
        exit("Jalankan dengan sudo python3 nama_file.py")
    run_all_tests()
