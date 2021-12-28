
import socket
from scapy.all import get_if_list, get_if_addr
import struct
import getch
import sys
import select
import threading
import multiprocessing

class Client:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"

    def __init__(self):
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        

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
        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) 
        self.broadcast_socket.bind(serverAddressPort)

        print("Client started, listening for offer requests...")

        self.tcp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


        while(True):
            msgFromServer = self.broadcast_socket.recvfrom(bufferSize)
            #There is one packet format used for all UDP communications:
            #    Magic cookie (4 bytes): 0xabcddcba. The message is rejected if it doesn’t start with this cookie
            #    Message type (1 byte): 0x2 for offer. No other message types are supported. 
            #    Server port (2 bytes): The port on the server that the client is supposed to connect to over TCP (the IP address of the server is the same for the UDP and TCP connections, so it doesn't need to be sent).
            format = "IBH"
            magic_cookie = 0xabcddcba
            message_type = 0x2
            var1, var2, var3 = struct.unpack(format,msgFromServer[0])
            if (var1 == magic_cookie and message_type == var2):
                print(f"Received offer from {msgFromServer[1][0]}, attempting to connect...")
                self.broadcast_socket.close()
                self.connectToServer(msgFromServer[1][0],var3)
                break
            else:
                print("Got an invalid offer.")


    def connectToServer(self, ip_addr, port):
        try:
            self.tcp_socket.connect((ip_addr,port))
        except socket.error as e:
            print(str(e))
        print(f"Connected to: {ip_addr}")
        initial_message = "Test Team Name\n"
        self.tcp_socket.sendall(str.encode(initial_message))
        Response = self.tcp_socket.recv(2048)
        if not Response:
            return
        #self.tcp_socket.settimeout(0.01)
        print(Response.decode('utf-8'))

        self.constant_input_thread = input_thread()
        self.constant_input_thread.setSocket(self.tcp_socket)
        self.constant_input_thread.start()
        
        
        while True:
            Response = self.tcp_socket.recv(2048)
            if not Response:
                break
            print(Response.decode('utf-8'))
            #Input = getch.getche()
        self.constant_input_thread.kill()
        self.tcp_socket.close()
        self.start()

# Needed to use multiprocessing to avoid GIL lock when using getch
#https://stackoverflow.com/questions/24192171/python-using-threading-to-look-for-key-input-with-getch
class input_thread (multiprocessing.Process):
    def __init__(self):
        super(input_thread, self).__init__()
    
    def setSocket(self,tcp_socket):
        self.tcp_socket = tcp_socket

    def sendData(self,data):
        try:
            self.tcp_socket.send(str.encode(data))
        except Exception as e:
            print(e)
    
    def run(self):
        print("Enter your answer: ")
        input = getch.getche()
        print("")
        self.sendData(input)




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
    # interface_addr = promptChooseInterface()
    # client.setBroadcastDestIP(interface_addr)
    client.start()

if __name__ == "__main__":
    main()