
import socket
from scapy.all import get_if_list, get_if_addr
import struct
import getch
import sys
import os
import select
import threading
import multiprocessing

class Colors:
    Black = "\u001b[30m"
    Red= "\u001b[31m"
    Green= "\u001b[32m"
    Yellow= "\u001b[33m"
    Blue= "\u001b[34m"
    Magenta= "\u001b[35m"
    Cyan= "\u001b[36m"
    White= "\u001b[37m"

    BrightBlack = "\u001b[30;1m"
    BrightRed= "\u001b[31;1m"
    BrightGreen= "\u001b[32;1m"
    BrightYellow= "\u001b[33;1m"
    BrightBlue= "\u001b[34;1m"
    BrightMagenta= "\u001b[35;1m"
    BrightCyan= "\u001b[36;1m"
    BrightWhite= "\u001b[37;1m"

    BackgroundBlack = "\u001b[40m"
    BackgroundRed= "\u001b[41m"
    BackgroundGreen= "\u001b[42m"
    BackgroundYellow= "\u001b[43m"
    BackgroundBlue= "\u001b[44m"
    BackgroundMagenta= "\u001b[45m"
    BackgroundCyan= "\u001b[46m"
    BackgroundWhite= "\u001b[47m"

    BackgroundBrightBlack = "\u001b[40;1m"
    BackgroundBrightRed= "\u001b[41;1m"
    BackgroundBrightGreen= "\u001b[42;1m"
    BackgroundBrightYellow= "\u001b[43;1m"
    BackgroundBrightBlue= "\u001b[44;1m"
    BackgroundBrightMagenta= "\u001b[45;1m"
    BackgroundBrightCyan= "\u001b[46;1m"
    BackgroundBrightWhite= "\u001b[47;1m"

    Bold = "\u001b[1m"
    
    Reset= "\u001b[0m"

class Client:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"
    DEFAULT_INTERFACE_NAME = "lo"
    DEFAULT_INTERFACE_ADDR = "127.0.0.1"

    def __init__(self):
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        
        self.interface_name = Client.DEFAULT_INTERFACE_NAME
        self.interface_addr = Client.DEFAULT_INTERFACE_ADDR

        self.tcp_src_port = 0

        self.tcp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        
    def setInterface(self, interface_name, interface_addr):
        self.interface_name = interface_name
        self.interface_addr = interface_addr

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip

    def start(self):
        while(True):
            msgFromClient       = "Hello UDP Server"

            bytesToSend         = str.encode(msgFromClient)

            serverAddressPort   = (b"0", self.broadcast_dest_port)

            bufferSize          = 1024


            # Create a UDP socket at client side
            self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) 
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            #self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,  str(self.interface_name + '\0').encode('utf-8'))

            self.broadcast_socket.bind(serverAddressPort)

            print(f"{Colors.Yellow}Client started, listening for offer requests...{Colors.Reset}")

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
                try:
                    var1, var2, var3 = struct.unpack(format,msgFromServer[0])
                    if (var1 == magic_cookie and message_type == var2):
                        print(f"{Colors.Yellow}Received offer from {msgFromServer[1][0]}, attempting to connect...{Colors.Reset}")
                        self.connectToServer(msgFromServer[1][0],var3)
                        break
                    else:
                        print(f"{Colors.Red}Got an invalid offer from {msgFromServer[1][0]}.{Colors.Reset}")
                except struct.error as e:
                    print(f"{Colors.Red}Got a malformed offer from {msgFromServer[1][0]}.{Colors.Reset}")
                


    def connectToServer(self, ip_addr, port):
        self.tcp_socket.settimeout(20)
        try:
            self.tcp_socket.connect((ip_addr,port))
        except socket.error as e:
            print(f"{Colors.Red}Couldn't connect to: {ip_addr}{Colors.Reset}")            
            print(str(e))
            return
        self.broadcast_socket.close()
        print(f"{Colors.Green}Connected to: {ip_addr}{Colors.Reset}")
        initial_message = "Test Team Name\n"
        try:
            self.tcp_socket.sendall(str.encode(initial_message))
            self.tcp_socket.settimeout(None)
            print(f"{Colors.Green}Waiting for game to start...{Colors.Reset}")
            Response = self.tcp_socket.recv(2048)
        except socket.error as e:
            print(f"{Colors.Red}Connection error with: {ip_addr}{Colors.Reset}")            
            print(str(e))
            return
        if not Response:
            print(f"{Colors.Yellow}{ip_addr} closed the connection.{Colors.Reset}")        
            return
        #self.tcp_socket.settimeout(0.01)
        print(Response.decode('utf-8'))

        self.constant_input_thread = input_thread()
        self.constant_input_thread.setSocket(self.tcp_socket)
        self.constant_input_thread.start()
        
        
        while True:
            try:
                Response = self.tcp_socket.recv(2048)
            except socket.error as e:
                print(f"{Colors.Red}Connection error with: {ip_addr}{Colors.Reset}")            
                print(str(e))
                break
            if not Response:
                print(f"{Colors.Yellow}{ip_addr} closed the connection.{Colors.Reset}")        
                break
            print(Response.decode('utf-8'))
            #Input = getch.getche()
        self.constant_input_thread.kill()
        self.tcp_socket.close()
        return

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
        try:
            input = getch.getche()
        except OverflowError as e:
            input = ""
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

    return indexed_interface_names.get(choice), get_if_addr(indexed_interface_names.get(choice))

def main():
    client = Client()
    interface_name, interface_addr = promptChooseInterface()
    client.setInterface(interface_name , interface_addr)
    client.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)