
import socket
from scapy.all import get_if_list, get_if_addr

class Client:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"

    def __init__(self):
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip

    def start(self):

        


        msgFromClient       = "Hello UDP Server"

        bytesToSend         = str.encode(msgFromClient)

        serverAddressPort   = (self.broadcast_dest_ip, self.broadcast_dest_port)

        bufferSize          = 1024


        # Create a UDP socket at client side
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) 
        UDPClientSocket.bind(serverAddressPort)

        while(True):
            msgFromServer = UDPClientSocket.recvfrom(bufferSize)

            msg = "Message from Server {}".format(msgFromServer[0])
            # Sending a reply to client
            print(msg)

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
    client = Client()
    interface_addr = promptChooseInterface()
    client.setBroadcastDestIP(interface_addr)
    client.start()

if __name__ == "__main__":
    main()