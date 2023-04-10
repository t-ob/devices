# Flask server that exposes an API which, when called, emits a wake-on-lan packet over the local network
# to the specified MAC address. This is used to wake up a computer that is asleep.

from flask import Flask, request, jsonify
import socket
from wakeonlan import send_magic_packet
from scapy.all import Ether, ARP, srp, sendp
import traceback

app = Flask(__name__)

@app.route('/wake', methods=['POST'])
def wake():
    try:
        data = request.get_json()
        mac_address = data['mac_address']
        ip_address = data.get('ip_address', '255.255.255.255')
        port = data.get('port', 9)

        send_magic_packet(mac_address, ip_address=ip_address, port=port)
        return jsonify({'status': 'success', 'message': f'Sent WoL packet to {mac_address}'}), 200

    except KeyError:
        return jsonify({'status': 'error', 'message': 'Missing mac_address parameter'}), 400
    except socket.error as e:
        return jsonify({'status': 'error', 'message': f'Socket error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500
    

@app.route('/scan', methods=['GET'])
def scan():
    try:
        network_ip = '192.168.4.0/24'
        arp_request = ARP(pdst=network_ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered, _ = srp(arp_request_broadcast, timeout=2, verbose=False)

        mac_addresses = []

        for sent, received in answered:
            mac_addresses.append({'ip': received.psrc, 'mac_address': received.hwsrc})

        return jsonify({'mac_addresses': mac_addresses}), 200
    except socket.error as e:
        print(f'Socket error: {str(e)}')
    except Exception as e:
        print(f'Error: {str(e)}')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
