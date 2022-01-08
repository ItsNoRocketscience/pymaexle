# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 16:10:35 2020

@author: Leonard Maisch
"""

import socket
import threading
import sys
import time
from dice_games_lib import Player, MaexleGame, read_dices, make_dices


if len(sys.argv) > 2:
    server = str(sys.argv[1])
    port = int(sys.argv[2])
else:
    server = '192.168.178.47'
    port = 6012

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print('Could not create bind to socket with provided connection details:')
    print(f'IP: {server:s}, Port: {port:d}')
    print('Additional Info:')
    print(e)
    print('Exiting!')
    sys.exit()

# Optional argument for socket.listen:
# max number of people to connect
# Default: Unlimited number of clients connection possible
s.listen()
print('Waiting for a connection, Server Started!')

games = []
def threaded_client(conn, addr):
    conn.send(str.encode('Connected'))
    reply = None
    player = None
    while True:
        try:
            msg = conn.recv(2048).decode()

            if not msg:
                print('Disconnected from: ', addr)
                break

            elif msg == 'n_games':
                reply = str(len(games))

            elif msg.startswith('game'):
                n = msg.split('_')[-1]
                reply = games[int(n)].get_name()

            elif msg.startswith('newgame:'):
                player = Player(msg[8:], conn)
                new_game = MaexleGame(player)
                player.game = new_game
                games.append(new_game)
                reply = str(len(player.game.players))

            elif msg.startswith('joingame:'):
                i_game = int(msg.split(':')[1])
                player = Player(msg[10 + msg[9:].find(':'):], conn)
                games[i_game].add_player(player)
                player.game = games[i_game]
                reply = str(len(games[i_game].players))

            elif msg == 'rolled':
                player.game.send_to_players(player, 'rolled:' + player.name)
                reply = None

            elif msg == 'show':
                hidden_dices = player.game.get_hidden_dices()
                reply = make_dices(hidden_dices)
                player.game.send_to_players(player,
                                            f'showed:{reply:s}:{player.name:s}')

            elif msg == 'startgame':
                player.game.start_game()
                time.sleep(1.0)
                player.game.first_turn()
                reply = None

            elif msg.startswith('next'):
                dice_values = read_dices(msg[4:])
                player.game.send_to_players(player, 'passed:' + player.name)
                time.sleep(1.0)
                player.game.pass_dices(dice_values)
                reply = None

            elif msg == 'closegame':
                if not player.game == None:
                    print('Removing Player: ' + player.name)
                    player.game.remove_player(player)
                    if len(player.game.players) == 0:
                        print('Game empty: Removing Game')
                        games.remove(player.game)
                    player.game = None
                reply = None

            print('Received: ', msg)
            print('Sending: ', reply)
            if reply == None:
                pass
            else:
                conn.sendall(str.encode(reply))
        except socket.timeout:
            print('Connection timed out!')
            print('Disconnected from: ', addr)
            break
        except Exception as e:
            print(e)
            break

    print('Lost Connection')
    if player:
        if player.game:
            print('Removing Player: ' + player.name)
            player.game.remove_player(player)
            if len(player.game.players) == 0:
                print('Game empty: Removing Game')
                games.remove(player.game)
    conn.close()

while True:
    s.settimeout(1.0)
    try:
        conn, addr = s.accept()
        print('Connected to:', addr)

        threading.Thread(target=threaded_client, args=(conn, addr,)).start()
    except KeyboardInterrupt:
        print('Shutting Down!')
        break

    except socket.timeout:
        continue


