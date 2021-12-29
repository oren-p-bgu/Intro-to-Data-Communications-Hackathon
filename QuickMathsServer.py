
from multiprocessing import Value
import socket
import time
from scapy.all import get_if_list, get_if_addr
import struct
import selectors
import threading
import random
import enum
import sys
import os
import ipaddress
import operator

# Helper class to display color in output
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


# Player status indicators
class Status(enum.Enum):
    lost=0
    won=1
    playing=2

# Generic class for a timed quiz game with multiple participents
class QuizGame:
    DEFAULT_PARTICIPENTS = 2
    DEFAULT_TIMEOUT = 10

    def __init__(self):
        self.participents = self.DEFAULT_PARTICIPENTS
        self.team_status = {}
        self.winner = ""
        self.timeout = self.DEFAULT_TIMEOUT
        self.start_time = time.time()

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

    # Checks if the given answer is correct, and updates the team's status accordingly (only one shot)
    def checkAnswer(self, team_name, answer):
        if (answer == self.answer):
            self.team_status[team_name] = Status.won
        else:
            self.team_status[team_name] = Status.lost
        return (answer == self.answer)

    def start(self):
        self.start_time = time.time()

    def timeIsUp(self):
        return ((time.time() - self.start_time) > self.timeout)

    # If time is up, there is a draw.
    # If a player was marked as won, they won. If only one player remains and all others lost, that player won. If all players lost, there is a draw.
    def winnerWasDecided(self):
        if (self.timeIsUp()):
            return True
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

    def forfeit(self, team_name):
        self.team_status[team_name] = Status.lost

    def getNumOfParticipents(self):
        return self.participents

    def getTeamNames(self):
        return self.team_status.keys()


    # Empty means draw
    def getWinner(self):
        return self.winner

    def gameOverMessage(self):
        message = f'{Colors.Bold}Game over!{Colors.Reset}\nThe correct answer was {Colors.Bold}{Colors.Green}{self.answer}{Colors.Reset}!\n\n'
        if (self.getWinner() == ""):
            message += f'The game resulted in a draw!'
        else:
            message += f'Congratulations to the winner: {Colors.Bold}{Colors.Magenta}{self.getWinner()}{Colors.Reset}'
        return message


# Quiz game with short single digits answers to simple addition and subtraction questions
class QuickMathsGame(QuizGame):
    def __init__(self):
        super().__init__()
        self.question_generator = QuickMathsQuestionGenerator()
        self.generateQuestion()

    def generateQuestion(self):
        self.question, self.answer = self.question_generator.generate()

    def welcomeMessage(self):
        message = f"""{Colors.Blue}
        
 __        __   _                             _                    
 \ \      / /__| | ___ ___  _ __ ___   ___   | |_ ___              
  \ \ /\ / / _ \ |/ __/ _ \| '_ ` _ \ / _ \  | __/ _ \             
   \ V  V /  __/ | (_| (_) | | | | | |  __/  | || (_) |            
    \_/\_/ \___|_|\___\___/|_| |_| |_|\___|   \__\___/     
              ___        _      _       __  __       _   _ 
             / _ \ _   _(_) ___| | __  |  \/  | __ _| |_| |__  ___ 
            | | | | | | | |/ __| |/ /  | |\/| |/ _` | __| '_ \/ __|
            | |_| | |_| | | (__|   <   | |  | | (_| | |_| | | \__ \\
             \__\_\\\\__,_|_|\___|_|\_\  |_|  |_|\__,_|\__|_| |_|___/
                                                                  

                                                                        
        {Colors.Reset}\n"""

        count = 1
        for team_name in self.team_status.keys():
            message += f"Player {count}: {Colors.Magenta}{team_name}{Colors.Reset}\n"
            count += 1
        message += "==\nPlease answer the following question as fast as you can:\n"
        return message


# Question generator for quiz games
class QuestionGenerator():
    def generate(self):
        return ("Prompt",0)

# Question generator for math quiz games
class QuickMathsQuestionGenerator(QuestionGenerator):
    def generate(self):
        answer = random.randint(0,9)
        number2 = random.randint(-9,9)
        number1 = answer - number2
        if (number2 >= 0):
            question = f"{Colors.Blue}How much is {number1}+{number2}?{Colors.Reset}"
        else:
            question = f"{Colors.Blue}How much is {number1}-{-1*number2}?{Colors.Reset}"
        return question, answer


# Formatting shortcut
def printInfo(string):
        print(f"{Colors.Yellow}{string}{Colors.Reset}")



# A server advertising itself on UDP and accepting client via TCP, up to the game's number of participents.
class Server:

    DEFAULT_BROADCAST_DEST_PORT = 13117
    DEFAULT_BROADCAST_DEST_IP = "127.0.0.1"
    DEFAULT_INTERFACE_NAME = "lo"
    DEFAULT_INTERFACE_ADDR = "127.0.0.1"
    DEFAULT_TEAM_NAME = "Hackstreet Boys"
    DEFAULT_HIGHSCORE_LIMIT = 5
    DEFAULT_DELAY_BEFORE_START_GAME = 3


    def __init__(self):
        self.broadcast_src_port = 0         # 0 means bind will choose a random available port
        self.broadcast_dest_port = Server.DEFAULT_BROADCAST_DEST_PORT
        self.broadcast_dest_ip = Server.DEFAULT_BROADCAST_DEST_IP

        self.tcp_src_port = 0
        self.interface_name = Server.DEFAULT_INTERFACE_NAME
        self.interface_addr = Server.DEFAULT_INTERFACE_ADDR

        self.history=[]
        self.history_updated = True

        self.team_name = Server.DEFAULT_TEAM_NAME

        self.highscore_limit = Server.DEFAULT_HIGHSCORE_LIMIT

        self.delay_before_start_game = Server.DEFAULT_DELAY_BEFORE_START_GAME


    def setInterface(self, interface_name, interface_addr):
        self.interface_name = interface_name
        self.interface_addr = interface_addr



    def setBroadcastSrcPort(self, broadcast_src_port):
        self.broadcast_src_port = broadcast_src_port

    def setBroadcastDestPort(self, broadcast_dest_port):
        self.broadcast_dest_port = broadcast_dest_port

    def setBroadcastDestIP(self, broadcast_dest_ip):
        print("Setting broadcast destination IP to " + broadcast_dest_ip)
        self.broadcast_dest_ip = broadcast_dest_ip
    def welcomeMessage(self):
        return f"You're playing on: {Colors.Magenta}{self.team_name}{Colors.Reset} Server\n{self.game.welcomeMessage()}"

    # Send to a client the closing message of the game and the current highscores.
    def announceWinner(self, connection):
        self.updateHistory()
        announcment = f"{self.game.gameOverMessage()}\n{self.getHistory()}"
        connection.sendall(str.encode(announcment))

    # Update the history of the games with the data from the current game.
    def updateHistory(self):
        if (self.history_updated):
            return
        winner = self.game.getWinner()
        team_names = self.game.getTeamNames()
        if (winner == ""):
            for team_name in team_names:
                index = next((i for i, item in enumerate(self.history) if item["name"] == team_name), None)
                if (index == None):
                    self.history.append({"name": team_name, "wins":0, "draws": 1, "losses" : 0})
                else:
                    self.history[index]["draws"] += 1
        else:
            for team_name in team_names:
                if (team_name == winner):
                    index = next((i for i, item in enumerate(self.history) if item["name"] == team_name), None)
                    if (index == None):
                        self.history.append({"name": team_name, "wins":1, "draws": 0, "losses" : 0})
                    else:
                        self.history[index]["wins"] += 1
                    continue

                index = next((i for i, item in enumerate(self.history) if item["name"] == team_name), None)
                if (index == None):
                    self.history.append({"name": team_name, "wins":0, "draws": 0, "losses" : 1})
                else:
                    self.history[index]["losses"] += 1
        self.history_updated = True

    # Returns a string of the formatted displayable version of the highscores
    def getHistory(self):
        record_format = Colors.Magenta + "{0:30}" + Colors.Reset + "|" + Colors.Green + "{1:7}" + Colors.Reset + "|" + Colors.Yellow + "{2:7}" + Colors.Reset + "|" + Colors.Red + "{3:7}" + Colors.Reset + "\n"
        history = f"\n{Colors.BackgroundYellow}~ Highscores ~{Colors.Reset}\n" + record_format.format("Name", "Wins", "Draws", "Losses")
        position = 1
        sorted_history = sorted(self.history, key=lambda d: d['losses'])
        sorted_history = sorted(self.history,key=lambda d: d['draws'], reverse=True)
        sorted_history = sorted(self.history,key=lambda d: d['wins'], reverse=True)

        for record in sorted_history:
            history += record_format.format(str(position) + ". " + record["name"],record["wins"],record["draws"],record["losses"])
            position += 1
            if (position > self.highscore_limit):
                break
        return history

    # The thread run for each client.
    # Started when a connection is made, expects to get a team name as the first data from the client.
    # Waits until condition is notified to signify the game has begun.
    # Sends the client the game's welcome messageand waits for it's answer.
    # If the client answers on time, it's answer is checked and it waits for all other players to finish.
    # If not, they lose.
    # Once the game has ended, announces the winner, closes the connection and exits.
    def manage_connection(self, connection, condition, player_number):
        connection.settimeout(1)
        try:
            team_name = connection.recv(1024).decode('utf-8').rstrip()
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
                # if client quit, automatically lost
                self.game.forfeit(fixed_team_name)
                connection.close()
                break
            with condition:
                try:
                    answer = int(data.decode('utf-8'))
                except ValueError as e:
                    answer = data.decode('utf-8')
                self.game.checkAnswer(fixed_team_name, answer)
                condition.notify_all()
                condition.wait_for(self.game.winnerWasDecided)
                self.announceWinner(connection)
                connection.close()
                return
        

    


    # Prepare for a game and start broadcasting a game is available.
    # Listen on TCP for incoming requests to play, allow up to the number of participents allowed by the game.
    # Once enough players have connected, close UDP and TCP advertising sockets and start game.
    def startOffering(self):
        self.game = QuickMathsGame()

        self.broadcast_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,  str(self.interface_name + '\0').encode('utf-8'))

        self.broadcast_socket.bind((self.interface_addr, self.broadcast_src_port))
        
        printInfo(f"Server started, listening on IP address {self.broadcast_socket.getsockname()[0]}")

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
            printInfo(f"Sending out offer {count}")

            #Accept times out after 1 second so broadcast goes out every 1 second
            self.broadcast_socket.sendto(bytesToSend, ("<broadcast>", self.broadcast_dest_port))
            count = count + 1
            while(True):
                try: 
                    Client, address = self.tcp_socket.accept()
                except socket.timeout:
                    break
                except KeyboardInterrupt:
                    printInfo("Shutting down server. Goodbye!")
                    self.broadcast_socket.close()
                    self.tcp_socket.close()
                    return
                printInfo('Connected to: ' + address[0] + ':' + str(address[1]))
                cur_thread = threading.Thread(target=self.manage_connection, args=(Client,condition, ThreadCount))
                threads.append(cur_thread)
                cur_thread.start()

                ThreadCount += 1
                if (ThreadCount == self.game.getNumOfParticipents()):
                    self.winner = ""
                    print(f"{Colors.Green}Enough players connected to start game.{Colors.Reset}")
                    self.broadcast_socket.close()
                    self.tcp_socket.close()

                    self.startGame(threads,condition) 
                    return   

    # Start a game with the connected clients.
    # Wait self.delay_before_start_game seconds after everyone connected before starting.
    # Once game ended, display highscores on the server and start advertising a new game.
    def startGame(self, threads, condition):
        self.history_updated = False
        time.sleep(self.delay_before_start_game)
        with condition:
            condition.notify_all()
            self.game.start()
        for thread in threads:
            thread.join()
        printInfo("Game ended.")
        print(self.getHistory())
        self.startOffering()
                        
        







# Helper function to help choose an interface
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
    server = Server()
    interface_name, interface_addr = promptChooseInterface()
    server.setInterface(interface_name , interface_addr)
    server.startOffering()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)