
import socket
from scapy.all import get_if_list, get_if_addr
import struct

class Client:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"

    def __init__(self):
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        self.tcp_src_port = 0
        self.tcp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

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
            #There is one packet format used for all UDP communications:
            #    Magic cookie (4 bytes): 0xabcddcba. The message is rejected if it doesn’t start with this cookie
            #    Message type (1 byte): 0x2 for offer. No other message types are supported. 
            #    Server port (2 bytes): The port on the server that the client is supposed to connect to over TCP (the IP address of the server is the same for the UDP and TCP connections, so it doesn't need to be sent).
            format = "IBH"
            magic_cookie = 0xabcddcba
            message_type = 0x2
            var1, var2, var3 = struct.unpack(format,msgFromServer[0])
            if (var1 == magic_cookie and message_type == var2):
                print("Got valid offer! Need to TCP port " + str(var3))
                UDPClientSocket.close()
                self.connectToServer(msgFromServer[1][0],var3)
            else:
                print("Got an invalid offer.")

    def connectToServer(self, ip_addr, port):
        try:
            self.tcp_socket.connect((ip_addr,port))
        except socket.error as e:
            print(str(e))
        Response = self.tcp_socket.recv(1024)
        while True:
            Input = input('Say Something: ')
            self.tcp_socket.send(str.encode(Input))
            Response = self.tcp_socket.recv(1024)
            print(Response.decode('utf-8'))





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