import selectors
import socket
import struct
import sys
import threading
import time
import scapy.all as S


global blue
global red
global reset

blue = u"\u001b[34m"
reset =  u"\u001b[0m"
red = u"\u001b[31m"

IP = S.get_if_addr("eth1")
#broadcastIP = "172.1.0.255"
broadcast_port = 13117  # Port to listen on (non-privileged ports are > 1023)
tcp_port = 8080  # Port to listen on (non-privileged ports are > 1023)

# handle TCP connection each client to server by call this class with threading
class server_connect(threading.Thread):
    def __init__(self, conn, addr): 
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.client_name = ''

    def run(self):
        data = self.conn.recv(4096)
        self.client_name = data.decode("utf-8")


# handle for get input from client and stop listening to the socket after 10 seconds
# call this class with threading 
class server_game(threading.Thread):
    def __init__(self, conn):  
        threading.Thread.__init__(self)
        self.conn = conn
        self.points = 0
        self.group = ''

    def set_group(self, group):
        self.group = group

    def run(self):
        self.conn.settimeout(10)
        while 1:
            try:
                data = self.conn.recv(1024)
                data = data.decode("utf-8")
                if data is not None:
                    self.points += len(data)
                    print(data)
            except:
                break


# sending broadcast messages to all client that listen on the IP and Port
def broadcast_connect(Tcp_port, Broadcast_port):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print(blue + "Server started, listening on IP address " + socket.gethostbyname(socket.gethostname()).__str__() + reset)
    broadcast_port = Broadcast_port
    tcp_port = Tcp_port
    #broadcast_message = struct.pack('4s2sh', bytearray.fromhex('feedbeef'), bytearray.fromhex('02'), tcp_port)
    broadcast_message = struct.pack('!IbH', 4276993775, 2 ,tcp_port)
    start = time.time()
    while time.time() - start < 10:
        try:
            broadcast_socket.sendto(broadcast_message, ('<broadcast>', broadcast_port))
            time.sleep(1)
        except:
            pass
    broadcast_socket.close()
    return tcp_port


def run_server(Tcp_port, Broadcast_port ,IP):
    # initial client by TCP socket
    tcp_port = broadcast_connect(Tcp_port, Broadcast_port)
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #tcp_socket.bind((IP, tcp_port))
        tcp_socket.bind(("", tcp_port))
    except:
        return
    client_counter = 1
    group_1 = []
    group_2 = []
    threads = []
    clients = {}
    # managing 4 clients connections to server by threading (server connect class)
    while client_counter < 5:
        tcp_socket.listen(1)
        try:
            tcp_socket.settimeout(10)
            conn, addr = tcp_socket.accept()
            tcp_socket.settimeout(None)
        except:
            print("No clients")
            return
        client_counter += 1
        serv = server_connect(conn, addr)
        player = server_game(conn)
        clients[serv] = player
        serv.start()
        threads.append(serv)

    # groups division   
    for t in threads:
        t.join()
        if len(group_1) < 2:
            group_1.append(t)
            clients[t].set_group(group_1)
        elif len(group_2) < 2:
            group_2.append(t)
            clients[t].set_group(group_2)
    welcome_msg = ("Welcome to Keyboard Spamming Battle Royale." +
                   "\nGroup 1:\n==\n" + group_1[0].client_name + "\n" + group_1[1].client_name + "\n"
                                                                                               "Group 2:\n==\n" +
                   group_2[0].client_name + "\n" + group_2[1].client_name + "\n\n" +
                   "Start pressing keys on your keyboard as fast as you can!!\n")
    # sending welcome and starting massage 
    # then start the threads of server game  
    for client in clients.values():
        client.conn.send(bytes(welcome_msg, 'utf-8'))
        client.start()

    # ending game for all clients      
    for client in clients.values():
        client.join()

    # summing the points of the groups after the game has ended
    group_1_points = clients[group_1[0]].points + clients[group_1[1]].points
    group_2_points = clients[group_2[0]].points + clients[group_2[1]].points

    if group_1_points > group_2_points:
        winner = group_1
        winner_number = 1
    else:
        winner = group_2
        winner_number = 2

    game_over_msg = ("Game over!\n" +
                     "Group 1 typed in {} characters. Group 2 typed in {} characters.\n".format(group_1_points,
                                                                                                group_2_points)
                     + "Group " + str(winner_number) + " wins!\n\n" +
                     "Congratulations to the winners:\n==\n" +
                     winner[0].client_name + winner[1].client_name)

    # send game over massage and close all TCP clients sockets
    for client in clients.values():
        client.conn.send(bytes(game_over_msg, 'utf-8'))
        client.conn.close()
    
    tcp_socket.close()
    print(game_over_msg)

    print(red + "Game over, sending out offer requests...\n" + reset)


while 1:
    run_server(tcp_port, broadcast_port, IP)
    time.sleep(2)
