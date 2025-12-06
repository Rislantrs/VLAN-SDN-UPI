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
CONTROLLER_IP = '192.168.56.105'  # Sesuaikan IP Controller
SCENARIOS = [5, 10, 15, 20, 50, 100]
DURATION = 30  
CHAOS_LOAD = 0.5  # 50% user lain jadi "Noise"

def setup_topology(num_visitors):
    # Bersihkan sisa topologi lama
    os.system('mn -c > /dev/null 2>&1')
    
    net = Mininet_wifi(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP)
    
    # 1. REALISME: Fisika Sinyal
    net.setPropagationModel(model="logDistance", exp=4)
    
    # --- BAGIAN INI SAYA MATIKAN BIAR GAK FREEZE ---
    # net.plotGraph(max_x=100, max_y=100) 
    # -----------------------------------------------

    # 2. REALISME: WiFi Mode G
    ap1 = net.addAccessPoint('ap1', ssid='Staff', mode='g', channel='1', position='30,30,0', range=45)
    ap2 = net.addAccessPoint('ap2', ssid='Visitor', mode='g', channel='6', position='50,50,0', range=45)
    ap3 = net.addAccessPoint('ap3', ssid='Visitor', mode='g', channel='11', position='70,30,0', range=45)
    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    c0 = net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=6633)

    # Staff
    staff = net.addStation('staff1', position='32,32,0', ip='192.168.10.1/24')
    
    visitors = []
    for i in range(1, num_visitors + 1):
        start_pos = f'{30+(i%60)},{30+(i%40)},0'
        sta = net.addStation(f'guest{i}', position=start_pos, ip=f'192.168.20.{i}/24')
        visitors.append(sta)

    net.configureWifiNodes()

    # 3. REALISME: Mobilitas (Tetap jalan di background walaupun gak ada gambar)
    net.setMobilityModel(time=0, model='RandomWayPoint', 
                         max_x=90, max_y=90, min_x=10, min_y=10, 
                         min_v=0.5, max_v=1.2, seed=1)

    # 4. REALISME: Link 100 Mbps
    info("*** Link: 100 Mbps (Fast Ethernet) + Delay 5ms ***\n")
    net.addLink(ap1, s1, bw=100, delay='5ms', use_htb=True)
    net.addLink(ap2, s1, bw=100, delay='5ms', use_htb=True)
    net.addLink(ap3, s1, bw=100, delay='5ms', use_htb=True)
    
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

def start_noise(visitors, target_ip):
    count = int(len(visitors) * CHAOS_LOAD)
    if count < 2: return
    spammers = random.sample(visitors[1:-1], min(count, len(visitors)-2))
    info(f"   >>> [NOISE] {len(spammers)} user lain sedang aktif...\n")
    for sta in spammers:
        sta.cmd(f"ping -i 0.5 {target_ip} > /dev/null 2>&1 &")

def run_test_session(protocol_type):
    info(f"\n\n############################################################\n")
    info(f"       MULAI TEST: {protocol_type} (SCENARIO 5-100 USER)")
    info(f"\n############################################################\n")

    for n in SCENARIOS:
        filename = f"LAPORAN_{protocol_type}_{n}_USER.txt"
        info(f"\n*** [{protocol_type}] SKENARIO {n} USER -> {filename} ***\n")
        
        net = None
        try:
            net, staff, visitors = setup_topology(n)
            src, dst = visitors[0], visitors[-1]
            
            start_noise(visitors, dst.IP())
            
            with open(filename, "w") as f:
                f.write(f"==================================================\n")
                f.write(f"LAPORAN {protocol_type} (REALISTIS/BUSY) - {n} USER\n")
                f.write(f"Kabel: 100Mbps | UDP Target: 50Mbps | No GUI\n")
                f.write(f"==================================================\n\n")
                
                # --- A. PING TEST ---
                info(f"   > [{protocol_type}] Mengukur Latency (Ping)...\n")
                f.write(f"--- [BAGIAN 1] HASIL PING SEBELUM {protocol_type} ---\n")
                ping_res = src.cmd(f"LC_ALL=C ping -i 1 -c {DURATION} {dst.IP()}")
                f.write(ping_res + "\n\n")
                
                # --- B. IPERF TEST ---
                info(f"   > [{protocol_type}] Mengukur Traffic...\n")
                f.write(f"--- [BAGIAN 2] HASIL IPERF {protocol_type} (SERVER LOG) ---\n")
                
                if protocol_type == 'UDP':
                    dst.cmd(f"iperf -s -u -i 1 > /tmp/iperf_server.log &")
                else:
                    dst.cmd(f"iperf -s -i 1 > /tmp/iperf_server.log &")
                
                time.sleep(1)
                
                if protocol_type == 'UDP':
                    # Target 50 Mbps (Bikin macet tapi gak mati total)
                    src.cmd(f"LC_ALL=C iperf -c {dst.IP()} -u -b 25M -t {DURATION} -i 1")
                else:
                    src.cmd(f"LC_ALL=C iperf -c {dst.IP()} -t {DURATION} -i 1")
                
                time.sleep(2)
                dst.cmd("pkill -x iperf")
                
                server_log = dst.cmd("cat /tmp/iperf_server.log")
                f.write(server_log)
                f.write("\n==================================================\n")
            
            info(f"   > Selesai {n} User. Lanjut...\n")
            
        except Exception as e:
            info(f"!!! ERROR: {e} !!!\n")
            
        finally:
            os.system("pkill -9 ping")
            if net: net.stop()
            time.sleep(2)

if __name__ == '__main__':
    setLogLevel('info')
    if os.geteuid() != 0:
        exit("Jalankan dengan sudo!")
        
    run_test_session('TCP')
    time.sleep(5)
    run_test_session('UDP')
    
    info("\n*** SELESAI! SILAKAN CEK FILE LAPORAN ***\n")
