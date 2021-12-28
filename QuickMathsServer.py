
import socket
import time
from scapy.all import get_if_list, get_if_addr
import struct
import selectors
import threading
import random
import enum

class Status(enum.Enum):
    lost=0
    won=1
    playing=2

class QuizGame:
    DEFAULT_PARTICIPENTS = 2

    def __init__(self):
        self.participents = self.DEFAULT_PARTICIPENTS
        self.team_status = {}
        self.winner = ""

    def addTeam(self,team_name):
        self.team_status[team_name] = Status.playing

    def doesTeamExist(self,team_name):
        return (team_name in self.team_status.keys())

    def generateQuestion(self):
        pass

    def getQuestion(self):
        return self.question

    def getAnswer(self):
        return self.answer

    def checkAnswer(self, team_name, answer):
        if (answer == self.answer):
            self.team_status[team_name] = Status.won
        else:
            self.team_status[team_name] = Status.lost
        return (answer == self.answer)

    # If a player was marked as won, they won. If only one player remains and all others lost, that player won. If all players lost, there is a draw.
    def winnerWasDecided(self):
        remaining_players = 0
        for team_name in self.team_status.keys():
            if(self.team_status[team_name] == Status.won):
                self.winner = team_name
                return True
            if (self.team_status[team_name] == Status.playing):
                remaining_players += 1
                remaining_team = team_name
        if (remaining_players == 1):
            self.winner = remaining_team
            return True
        if (remaining_players == 0):
            return True
        return False


    # Empty means draw
    def getWinner(self):
        return self.winner

    def gameOverMessage(self):
        message = f'Game over!\nThe correct answer was {self.answer}!\n\n'
        if (self.getWinner() == ""):
            message += f'The game resulted in a draw!'
        else:
            message += f'Cognratulations to the winner: {self.getWinner()}'
        return message



class QuickMathsGame(QuizGame):
    def __init__(self):
        super().__init__()
        self.question_generator = QuickMathsQuestionGenerator()
        self.generateQuestion()

    def generateQuestion(self):
        self.question, self.answer = self.question_generator.generate()

    def welcomeMessage(self):
        message = "Welcome to Quick Maths.\n"
        count = 1
        for team_name in self.team_status.keys():
            message += f"Player {count}: {team_name}\n"
            count += 1
        message += "==\nPlease answer the following question as fast as you can:\n"
        return message



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

        self.tcp_src_port = 0


    def setBroadcastSrcPort(self, broadcast_src_port):
        self.broadcast_src_port = broadcast_src_port

    def setBroadcastDestPort(self, broadcast_dest_port):
        self.broadcast_dest_port = broadcast_dest_port

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip
    def welcomeMessage(self):
        return self.game.welcomeMessage()

    def announceWinner(self, connection):
        announcment = self.game.gameOverMessage()
        connection.sendall(str.encode(announcment))

    def manage_connection(self, connection, condition, player_number):
        connection.settimeout(1)
        try:
            print(f"Waiting for team name from {connection.getpeername()}")
            team_name = connection.recv(1024).decode('utf-8').rstrip()
            print(f"Got team name: {team_name}")
        except socket.timeout:
            print(f"Didn't receive team name from {connection.getpeername()[0]}")
            self.announceWinner(connection)
            connection.close()
            return
        # Handle teams with the same name
        fixed_team_name = team_name
        modifier = 1
        
        with condition:
            while (self.game.doesTeamExist(fixed_team_name)):
                fixed_team_name = f"{team_name}({modifier})" 
                modifier += 1

            self.game.addTeam(fixed_team_name)

            condition.wait()

        welcome = self.welcomeMessage()
        prompt = self.game.getQuestion()
        connection.sendall(str.encode(welcome + prompt))

        connection.settimeout(0.1)
    
        while True:
            try: 
                data = connection.recv(2048)
            except socket.timeout:
                if (self.game.winnerWasDecided()):
                    self.announceWinner(connection)
                    connection.close()
                    return
                else:
                    continue
            if not data:
                break
            with condition:
                answer = int(data.decode('utf-8'))
                self.game.checkAnswer(fixed_team_name, answer)
                condition.notify_all()
                condition.wait_for(self.game.winnerWasDecided)
                self.announceWinner(connection)
                connection.close()
                return

            connection.sendall(str.encode(reply))
        connection.close()


    def startOffering(self):
        self.game = QuickMathsGame()

        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.bind(('', self.broadcast_src_port))
        print(f"Server started, listening on IP address {self.broadcast_socket.getsockname()[0]}")

        self.tcp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.tcp_socket.settimeout(1)
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


        self.tcp_socket.listen(2)

        count = 1
        ThreadCount = 0
        condition = threading.Condition()

        threads = []

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
                except KeyboardInterrupt:
                    print("Shutting down server. Goodbye!")
                    self.broadcast_socket.close()
                    self.tcp_socket.close()
                    return
                print('Connected to: ' + address[0] + ':' + str(address[1]))
                cur_thread = threading.Thread(target=self.manage_connection, args=(Client,condition, ThreadCount))
                threads.append(cur_thread)
                cur_thread.start()

                ThreadCount += 1
                if (ThreadCount == 2):
                    self.winner = ""
                    print("Enough players connected to start game.")
                    self.broadcast_socket.close()
                    self.tcp_socket.close()

                    self.startGame(threads,condition)    

    def startGame(self, threads, condition):
        time.sleep(3)
        with condition:
            condition.notify_all()
            condition.wait_for(self.game.winnerWasDecided)
        print("Game ended.")
        for thread in threads:
            thread.join()
        self.startOffering()
                        
        








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
    # interface_addr = promptChooseInterface()
    # server.setBroadcastDestIP(interface_addr)
    server.startOffering()

if __name__ == "__main__":
    main()