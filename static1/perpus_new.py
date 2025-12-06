import sys
import time
import os
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSKernelSwitch
from mn_wifi.node import OVSKernelAP
from mn_wifi.net import Mininet_wifi
from mininet.link import TCLink

# --- KONFIGURASI ---
CONTROLLER_IP = '192.168.56.105'
DURATION = 30 
SCENARIOS = [5, 10, 15, 20, 50, 100]

def setup_topology(num_visitors, bw_limit=300):
    net = Mininet_wifi(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP)
    
    # Topologi Perpustakaan
    ap1 = net.addAccessPoint('ap1', ssid='Staff', mode='g', channel='1', position='30,30,0')
    ap2 = net.addAccessPoint('ap2', ssid='Visitor', mode='g', channel='6', position='50,50,0')
    ap3 = net.addAccessPoint('ap3', ssid='Visitor', mode='g', channel='11', position='70,30,0')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    c0 = net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=6633)

    staff = net.addStation('staff1', position='32,32,0', ip='192.168.10.1/24')
    visitors = []
    for i in range(1, num_visitors + 1):
        if i % 2 == 0: pos = f'{50+(i%5)},{50+(i%5)},0'
        else: pos = f'{70+(i%5)},{30+(i%5)},0'
        sta = net.addStation(f'guest{i}', position=pos, ip=f'192.168.20.{i}/24')
        visitors.append(sta)

    net.configureWifiNodes()
    net.addLink(ap1, s1, bw=bw_limit, use_htb=True)
    net.addLink(ap2, s1, bw=bw_limit, use_htb=True)
    net.addLink(ap3, s1, bw=bw_limit, use_htb=True)
    
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    s1.cmd('ovs-vsctl set port s1-eth1 tag=10')
    s1.cmd('ovs-vsctl set port s1-eth2 tag=20')
    s1.cmd('ovs-vsctl set port s1-eth3 tag=20')

    time.sleep(5)
    return net, staff, visitors

def run_all_tests():
    # Loop Skenario Jumlah User
    for n in SCENARIOS:
        filename = f"LAPORAN_SKENARIO_{n}_USER.txt"
        info(f"\n*** MENJALANKAN SKENARIO {n} USER -> Simpan ke {filename} ***\n")
        
        net, staff, visitors = setup_topology(n, bw_limit=300)
        src, dst = visitors[0], visitors[-1]
        
        with open(filename, "w") as f:
            f.write(f"==================================================\n")
            f.write(f"LAPORAN PENGUJIAN SKALABILITAS - {n} USER\n")
            f.write(f"==================================================\n\n")
            
            # --- 1. LATENCY (PING) ---
            info("   > Mengukur Latency (Ping)...\n")
            f.write("--- [BAGIAN 1] HASIL PING (LATENCY) ---\n")
            f.write("Command: ping -i 1 -c 30 <ip_dest>\n\n")
            
            # Jalankan Ping (Bahasa Inggris dipaksa biar formatnya umum)
            ping_res = src.cmd(f"LC_ALL=C ping -i 1 -c {DURATION} {dst.IP()}")
            f.write(ping_res)
            f.write("\n\n")
            
            # --- 2. THROUGHPUT & JITTER (IPERF) ---
            info("   > Mengukur Throughput & Jitter (Iperf)...\n")
            f.write("--- [BAGIAN 2] HASIL IPERF (JITTER & THROUGHPUT) ---\n")
            f.write("Command: iperf -c <ip_dest> -u -b 2M -t 30 -i 1\n\n")
            
            dst.cmd("LC_ALL=C iperf -s -u -i 1 &")
            time.sleep(1)
            # Jalankan Iperf Client
            iperf_res = src.cmd(f"LC_ALL=C iperf -c {dst.IP()} -u -b 2M -t {DURATION} -i 1")
            dst.cmd("killall -9 iperf")
            
            f.write(iperf_res)
            f.write("\n\n==================================================\n")
        
        info(f"   > Selesai. Data tersimpan di {filename}\n")
        net.stop()
        time.sleep(2)

    # --- 3. SECURITY TEST (BLOCK) ---
    info("\n*** MENJALANKAN SECURITY TEST ***\n")
    net, staff, visitors = setup_topology(5)
    with open("LAPORAN_SECURITY_BLOCK.txt", "w") as f:
        f.write("=== PENGUJIAN KEAMANAN VLAN (BLOCK) ===\n")
        f.write("Skenario: Staff (VLAN 10) Ping Visitor (VLAN 20)\n")
        f.write("Harapan: 100% Packet Loss (Unreachable)\n\n")
        
        res = staff.cmd(f"LC_ALL=C ping -c 4 -W 1 {visitors[0].IP()}")
        f.write(res)
        
        if "100% packet loss" in res:
            f.write("\n\n>>> KESIMPULAN: AMAN (BLOKIR BERHASIL)")
        else:
            f.write("\n\n>>> KESIMPULAN: GAGAL (TIDAK DIBLOKIR)")
            
    net.stop()

    # --- 4. ADMIN LIMIT TEST ---
    info("\n*** MENJALANKAN ADMIN LIMIT TEST ***\n")
    LIMIT = 5
    net, staff, visitors = setup_topology(5, bw_limit=LIMIT)
    with open("LAPORAN_ADMIN_LIMIT.txt", "w") as f:
        f.write(f"=== PENGUJIAN QOS LIMIT ({LIMIT} Mbps) ===\n")
        f.write("Skenario: Visitor download file besar via TCP\n")
        f.write(f"Harapan: Bandwidth mentok di angka {LIMIT} Mbps\n\n")
        
        visitors[1].cmd("LC_ALL=C iperf -s -i 1 &")
        time.sleep(1)
        res = visitors[0].cmd(f"LC_ALL=C iperf -c {visitors[1].IP()} -t 10 -i 1")
        visitors[1].cmd("killall -9 iperf")
        
        f.write(res)
        f.write("\n\n>>> SILAKAN CEK ANGKA 'Mbits/sec' DI ATAS. JIKA DEKAT 5 MBPS BERARTI SUKSES.")

    net.stop()
    info("\n*** SEMUA SELESAI! SILAKAN BUKA FILE .TXT ***\n")

if __name__ == '__main__':
    setLogLevel('info')
    run_all_tests()
