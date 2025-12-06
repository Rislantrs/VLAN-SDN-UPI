import sys
import time
import os
import random
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSKernelSwitch
from mn_wifi.node import OVSKernelAP
from mn_wifi.net import Mininet_wifi
from mininet.link import TCLink

# --- KONFIGURASI UTAMA ---
CONTROLLER_IP = '192.168.56.105'
DURATION = 30
SCENARIOS = [5, 10, 15, 20, 50, 100]

# --- KONFIGURASI CHAOS (REALISME) ---
# Berapa persen user yang aktif mengganggu jaringan? (0.5 = 50%, 1.0 = 100%)
# SARAN: Mulai dari 0.5 (50%) dulu. Jika laptop kuat, naikkan ke 0.8 atau 1.0
TRAFFIC_LOAD = 0.5 

def setup_topology(num_visitors, bw_limit=1000):
    net = Mininet_wifi(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP)
    
    # 1. Fisika: Sinyal Tembok
    net.setPropagationModel(model="logDistance", exp=4)
    net.plotGraph(max_x=100, max_y=100)

    # 2. Bottleneck WiFi (Mode G = 54Mbps)
    ap1 = net.addAccessPoint('ap1', ssid='Staff', mode='g', channel='1', position='30,30,0', range=45)
    ap2 = net.addAccessPoint('ap2', ssid='Visitor', mode='g', channel='6', position='50,50,0', range=45)
    ap3 = net.addAccessPoint('ap3', ssid='Visitor', mode='g', channel='11', position='70,30,0', range=45)
    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    c0 = net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=6633)

    staff = net.addStation('staff1', position='32,32,0', ip='192.168.10.1/24')
    
    visitors = []
    for i in range(1, num_visitors + 1):
        start_pos = f'{30+(i%60)},{30+(i%40)},0'
        sta = net.addStation(f'guest{i}', position=start_pos, ip=f'192.168.20.{i}/24')
        visitors.append(sta)

    net.configureWifiNodes()

    # 3. Mobilitas
    net.setMobilityModel(time=0, model='RandomWayPoint', 
                         max_x=90, max_y=90, min_x=10, min_y=10, 
                         min_v=0.5, max_v=1.0, seed=1)

    # Link Kabel
    net.addLink(ap1, s1, bw=bw_limit, delay='1ms', use_htb=True)
    net.addLink(ap2, s1, bw=bw_limit, delay='1ms', use_htb=True)
    net.addLink(ap3, s1, bw=bw_limit, delay='1ms', use_htb=True)
    
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    s1.cmd('ovs-vsctl set port s1-eth1 tag=10')
    s1.cmd('ovs-vsctl set port s1-eth2 tag=20')
    s1.cmd('ovs-vsctl set port s1-eth3 tag=20')

    net.startMobility(time=0)
    time.sleep(5)
    return net, staff, visitors

def start_background_traffic(visitors, target_ip, load_percentage):
    """
    Fungsi ini membuat user lain 'berisik' (spamming ping)
    agar jaringan macet (Realistis).
    """
    # Hitung jumlah pengganggu
    num_noise = int(len(visitors) * load_percentage)
    if num_noise < 1: return []

    # Pilih user acak (kecuali user pertama dan terakhir yg dipake tes utama)
    potential_spammers = visitors[1:-1] 
    if not potential_spammers: return []
    
    # Safety check: Jangan ambil lebih dari yg ada
    sample_size = min(num_noise, len(potential_spammers))
    noise_makers = random.sample(potential_spammers, sample_size)
    
    info(f"   >>> [CHAOS] Mengaktifkan {len(noise_makers)} user background traffic...\n")
    
    for sta in noise_makers:
        # Ping Flood Ringan (-i 0.2 = 5 paket per detik)
        # Cukup untuk bikin macet WiFi tapi ringan buat CPU Laptop
        # Output dibuang ke /dev/null agar memory tidak penuh
        sta.cmd(f"ping -i 0.2 {target_ip} > /dev/null 2>&1 &")
    
    return noise_makers

def run_all_tests():
    # Pastikan bersih dari sisa proses sebelumnya
    os.system("pkill -9 ping")
    os.system("pkill -9 iperf")

    for n in SCENARIOS:
        filename = f"LAPORAN_CHAOS_{n}_USER.txt"
        info(f"\n*** SKENARIO {n} USER (CHAOS MODE {TRAFFIC_LOAD*100}%) -> {filename} ***\n")
        
        net = None
        try:
            net, staff, visitors = setup_topology(n, bw_limit=1000)
            
            # User Utama (Yang kita ukur)
            src, dst = visitors[0], visitors[-1]
            
            # --- MULAI CHAOS ---
            # User lain akan ngebom ping ke 'dst' (seolah-olah dst adalah server populer)
            start_background_traffic(visitors, dst.IP(), TRAFFIC_LOAD)
            
            with open(filename, "w") as f:
                f.write(f"==================================================\n")
                f.write(f"LAPORAN SUPER REALISTIS (CHAOS) - {n} USER\n")
                f.write(f"Background Load: {TRAFFIC_LOAD*100}% User Aktif\n")
                f.write(f"==================================================\n\n")
                
                # --- TEST UTAMA: PING ---
                info("   > [1/2] Mengukur Latency Utama...\n")
                f.write("--- [BAGIAN 1] HASIL PING (LATENCY) ---\n")
                # User utama mencoba ping di tengah kemacetan
                ping_res = src.cmd(f"LC_ALL=C ping -i 1 -c {DURATION} {dst.IP()}")
                f.write(ping_res + "\n\n")
                
                # --- TEST UTAMA: IPERF ---
                info("   > [2/2] Mengukur Jitter/Throughput Utama...\n")
                f.write("--- [BAGIAN 2] HASIL IPERF (JITTER PER DETIK) ---\n")
                
                dst.cmd(f"iperf -s -u -i 1 > /tmp/iperf_server.log &")
                time.sleep(1)
                
                # User utama mencoba streaming di tengah kemacetan
                src.cmd(f"LC_ALL=C iperf -c {dst.IP()} -u -b 2M -t {DURATION} -i 1")
                
                time.sleep(2)
                dst.cmd("pkill -x iperf")
                
                server_log = dst.cmd("cat /tmp/iperf_server.log")
                f.write(server_log)
                f.write("\n==================================================\n")
            
            info(f"   > Selesai. Cek file {filename}\n")
            
        except Exception as e:
            info(f"!!! ERROR: {e} !!!\n")
            
        finally:
            # PENTING: Matikan semua background traffic agar laptop tidak hang
            info("   > Membersihkan Background Processes...\n")
            os.system("pkill -9 ping") 
            if net: net.stop()
            os.system('mn -c > /dev/null 2>&1')
            time.sleep(3)

if __name__ == '__main__':
    setLogLevel('info')
    if os.geteuid() != 0:
        exit("Harus run sebagai root (sudo)")
    run_all_tests()
