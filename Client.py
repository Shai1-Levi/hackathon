import multiprocessing
import socket
import struct
import time

import sys
from select import select
import tty
import scapy.all as S
import termios
import getch

group_name = "shimons"


IP = S.get_if_addr("eth1")
UDP_Port = 13117


# get user input from keyboard
# this function has called by proccess
def reader_user_input(socket):
    while 1:
        c = getch.getche()
        socket.send(bytes(c, 'utf-8'))

def get_broadcast_offer_from_server(IP, UDP_Port):
    broadcast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    broadcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_client.bind(("", UDP_Port))
    return broadcast_client


while 1:
    broadcast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    broadcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_client.bind(("", UDP_Port))
    print("Client started, listening for offer requests...")
    #broadcast_client = get_broadcast_offer_from_server(IP, UDP_Port)
    data, addr = broadcast_client.recvfrom(1024)
    

    #read packet from server by packet format
    #msg = struct.unpack('4s2sh', data)
    msg = struct.unpack('!IbH', data)
    host = addr[0]  # Standard loopback interface address (localhost)
    port = msg[2]
    print("Received offer from %s, attempting to connect..." % host)
    broadcast_client.close()

    # start connceting to server by sending requset over TCP
    while 1:
        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect((host, port))
            tcp_client.send(bytes(group_name + "\n", 'utf-8'))
            break
        except:
            time.sleep(0.5)
            pass

     # reciving welcome message and print the message to the user   
    welcome_msg = ''
    while welcome_msg == '':
        welcome_msg = tcp_client.recv(4096)
        print(welcome_msg.decode("utf-8"))
    
    # starting new multiprocessing.Process for reciving user inputs
    # with the reader_user_input function
    # after 10 seconds terminate the Process
    start = time.time()
    p = multiprocessing.Process(target=reader_user_input, name = "reader_user_input", args = (tcp_client,))
    p.start()
    time.sleep(10)
    p.terminate()

    # reciving game over massage from the server and print it to user
    game_over_msg = tcp_client.recv(4096)
    print(game_over_msg.decode("utf-8"))
    tcp_client.close()
    print("Server disconnected, listening for offer requests...\n")
    time.sleep(2)
    # after the game was end, the client start a new trying to recive 
    # offer for connection from servers
