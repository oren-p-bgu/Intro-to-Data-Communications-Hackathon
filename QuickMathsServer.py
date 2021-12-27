
import socket
import time
from scapy.all import get_if_list, get_if_addr
import struct
import selectors
import threading
import random

class QuizGame:
    DEFAULT_PARTICIPENTS = 2

    def __init__(self):
        self.participents = self.DEFAULT_PARTICIPENTS

    def generateQuestion(self):
        pass

    def getQuestion(self):
        return self.question

    def checkAnswer(self, answer):
        return (answer == self.answer)

class QuickMathsGame(QuizGame):
    def __init__(self):
        super().__init__()
        self.question_generator = QuickMathsQuestionGenerator()
        self.generateQuestion()

    def generateQuestion(self):
        self.question, self.answer = self.question_generator.generate()

class QuestionGenerator():
    def generate(self):
        return ("Prompt",0)

class QuickMathsQuestionGenerator(QuestionGenerator):
    def generate(self):
        answer = random.randint(0,9)
        number2 = random.randint(-9,9)
        number1 = answer - number2
        if (number2 >= 0):
            question = f"How much is {number1}+{number2}?"
        else:
            question = f"How much is {number1}-{-1*number2}?"
        return question, answer

class Server:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"

    def __init__(self):
        self.broadcast_src_port = 0         # 0 means bind will choose a random available port
        self.broadcast_dest_port = self.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = self.DEFAULT_BROADCAST_DEST_IP
        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.tcp_src_port = 0
        self.tcp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.tcp_socket.settimeout(1)

        self.game = QuickMathsGame()

        self.winner = ""

    def winnerWasDecided(self):
        return (not self.winner == "")

    def setBroadcastSrcPort(self, broadcast_src_port):
        self.broadcast_src_port = broadcast_src_port

    def setBroadcastDestPort(self, broadcast_dest_port):
        self.broadcast_dest_port = broadcast_dest_port

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip
    
    def threaded_client(self, connection, condition):
        prompt = self.game.getQuestion()
        connection.sendall(str.encode(prompt))
        connection.settimeout(0.1)
        with condition:
            while True:
                try: 
                    data = connection.recv(2048)
                except socket.timeout:
                    if (self.winnerWasDecided()):
                        reply = 'Server Says: A winner was decided! Goodbye!'
                        connection.sendall(str.encode(reply))
                        connection.close()
                        return
                    else:
                        continue
                answer = int(data.decode('utf-8'))
                if (self.game.checkAnswer(answer)):
                    reply = 'Server Says: Correct answer!!!'
                    connection.sendall(str.encode(reply))
                    self.winner = "Test team"
                    condition.notify()
                    connection.close()
                    return
                else:
                    reply = 'Server Says: Wrong answer!!!'
                if not data:
                    break
                connection.sendall(str.encode(reply))
            connection.close()


    def startOffering(self):

        self.tcp_socket.bind(('', self.tcp_src_port))

        #There is one packet format used for all UDP communications:
        #    Magic cookie (4 bytes): 0xabcddcba. The message is rejected if it doesn’t start with this cookie
        #    Message type (1 byte): 0x2 for offer. No other message types are supported. 
        #    Server port (2 bytes): The port on the server that the client is supposed to connect to over TCP (the IP address of the server is the same for the UDP and TCP connections, so it doesn't need to be sent).
        format = "IBH"
        magic_cookie = 0xabcddcba
        message_type = 0x2
        server_port = self.tcp_socket.getsockname()[1]
        bytesToSend = struct.pack(format,magic_cookie,message_type,server_port)

        # Bind to address and ip
        self.broadcast_socket.bind(('', self.broadcast_src_port))

        print("UDP server up and broadcasting")
        self.tcp_socket.listen(2)

        count = 1
        ThreadCount = 0
        condition = threading.Condition()
        self.winner = ""

        # Start broadcasting
        while(True):
            timedout = False
            print("Sending out offer " + str(count))

            #Accept times out after 1 second so broadcast goes out every 1 second
            self.broadcast_socket.sendto(bytesToSend, (self.broadcast_dest_ip, self.broadcast_dest_port))
            count = count + 1
            while(True):
                try: 
                    Client, address = self.tcp_socket.accept()
                except socket.timeout:
                    break
                print('Connected to: ' + address[0] + ':' + str(address[1]))
                threading.Thread(target=self.threaded_client, args=(Client,condition, )).start()

                ThreadCount += 1
                if (ThreadCount == 2):
                    self.winner = ""
                    print("Got two connections. Had enough! Waiting!")
                    with condition:
                        condition.wait_for(self.winnerWasDecided)
                        count = 1
                        ThreadCount = 0
                        condition = threading.Condition()
                        break
                        
        


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