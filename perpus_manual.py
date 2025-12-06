import sys
import os
# Fix: Paksa Bahasa Inggris agar pingall tidak error
os.environ["LC_ALL"] = "C"

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSKernelSwitch
from mn_wifi.node import OVSKernelAP
from mn_wifi.net import Mininet_wifi
from mininet.link import TCLink
from mininet.cli import CLI

CONTROLLER_IP = '127.0.0.1'

def topology():
    os.system('mn -c > /dev/null 2>&1')
    net = Mininet_wifi(controller=RemoteController, link=TCLink, accessPoint=OVSKernelAP)
    info("*** Membuat Topologi 3 AP...\n")

    # 1. Access Points
    # AP1 (Staff - VLAN 10)
    ap1 = net.addAccessPoint('ap1', ssid='Staff_AP', mode='g', channel='1', position='30,30,0', range=50)
    # AP2 (Visitor Area 1 - VLAN 20)
    ap2 = net.addAccessPoint('ap2', ssid='Guest_AP', mode='g', channel='6', position='60,30,0', range=50)
    # AP3 (Visitor Area 2 - VLAN 20)
    ap3 = net.addAccessPoint('ap3', ssid='Guest_AP', mode='g', channel='11', position='90,30,0', range=50)

    # 2. Switch & Controller
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    c0 = net.addController('c0', controller=RemoteController, ip=CONTROLLER_IP, port=6633)

    # 3. Hosts
    # Staff (VLAN 10)
    h1 = net.addStation('h1', ip='192.168.10.1/24', position='31,31,0')
    h2 = net.addStation('h2', ip='192.168.10.2/24', position='32,32,0')
    h3 = net.addStation('h3', ip='192.168.10.3/24', position='33,33,0')
    h4 = net.addStation('h4', ip='192.168.10.4/24', position='34,34,0')

    # Visitors (VLAN 20)
    guest1 = net.addStation('guest1', ip='192.168.20.1/24', position='61,31,0') # di AP2
    guest2 = net.addStation('guest2', ip='192.168.20.2/24', position='62,32,0') # di AP2
    guest3 = net.addStation('guest3', ip='192.168.20.3/24', position='63,33,0') # di AP2
    guest4 = net.addStation('guest4', ip='192.168.20.4/24', position='91,31,0') # di AP3
    guest5 = net.addStation('guest5', ip='192.168.20.5/24', position='92,32,0') # di AP3

    net.configureWifiNodes()

    # 4. Link (Kabel)
    net.addLink(ap1, s1)
    net.addLink(ap2, s1)
    net.addLink(ap3, s1)

    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    # 5. VLAN Config
    s1.cmd('ovs-vsctl set port s1-eth1 tag=10') # AP1 Staff
    s1.cmd('ovs-vsctl set port s1-eth2 tag=20') # AP2 Visitor
    s1.cmd('ovs-vsctl set port s1-eth3 tag=20') # AP3 Visitor

    net.startMobility(time=0)
    
    info("\n*** READY! Masuk ke Mode CLI Manual...\n")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
