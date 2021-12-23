
import socket
import time
from scapy.all import get_if_list, get_if_addr
class Server:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"

    def __init__(self):
        self.broadcast_src_port = 0         # 0 means bind will choose a random available port
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def setBroadcastSrcPort(self, broadcast_src_port):
        self.broadcast_src_port = broadcast_src_port

    def setBroadcastDestPort(self, broadcast_dest_port):
        self.broadcast_dest_port = broadcast_dest_port

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip

    def startOffering(self):
        msgFromServer       = "Test offer"
        bytesToSend         = str.encode(msgFromServer)

        # Bind to address and ip
        self.broadcast_socket.bind(('', self.broadcast_src_port))

        print("UDP server up and broadcasting")

        count = 1

        # Start broadcasting
        while(True):
            print("Sending out offer " + str(count))
            self.broadcast_socket.sendto(bytesToSend, (self.broadcast_dest_ip, self.broadcast_dest_port))
            time.sleep(1)
            count = count + 1
            
def promptChooseInterface():
    interface_names =get_if_list()
    indexed_interface_names = {}

    index = 1
    for name in interface_names:
        indexed_interface_names[index] = name
        print(str(index) + ") " + name)
        index = index + 1

    valid_choice = False
    choice = 0
    while(not valid_choice):
        try:
            choice = int(input("Please select an interface to broadcast on (enter its number and press enter): "))
            if (choice in indexed_interface_names.keys()):
                valid_choice = True
                continue
        except ValueError as e:
            pass
        print("Invalid choice. Please try again.")

    return get_if_addr(indexed_interface_names.get(choice))

def main():
    server = Server()
    interface_addr = promptChooseInterface()
    server.setBroadcastDestIP(interface_addr)
    server.startOffering()

if __name__ == "__main__":
    main()