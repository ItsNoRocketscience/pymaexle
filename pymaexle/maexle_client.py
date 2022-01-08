# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 16:09:25 2020

@author: Leonard Maisch

Changelog:
    v1.0: 09.05.20:
        - Birthday present for Darius Lauch
        - More or less stable
        - Fun and makes you drunk really fast
    v1.1: 21.02.21:
        - Entry-field slightly larger, prevents shifting of text that is
          slightly too large (e.g. "Darius hat weitergegeben!")
        - Text direction flipped (newer now at the bottom)
        - If another player shows, meaningful text is now displayed
        - If one player shows, dice values are now shown for all other
          players in green and in red for her/himself
        - (Hopefully) fixed a problem, that occured when None's were passed and
          the make_dices function raised an exception that caused a crash
          => Fix: deactivating pass button before setting dice-values to None
        - Added version in title of window
"""
import tkinter as tk
import tkinter.messagebox
import threading
import socket
from tkinter_gui import GameGUI
from dice_games_lib import read_dices, make_dices, dice_to_string, read_config
import sys, os, time
import pathlib


class ClientGUI:
    def __init__(self, master, ip='', port=0, verbose=False,
                 version='1.1'):
        self.master = master
        self.master.resizable(False, False)
        self.master.title('Lobby Client v' + version)
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        self.set_icon('rocket.ico')

        self.set_geo()
        self.set_frames()

        tk.Label(self.master, text='Lobby', font=('Courier', 25)).\
            grid(row=0, column=0, columnspan=2)

        self.ip = tk.StringVar(self.master)
        self.ip.set(ip)
        # self.ip.set('192.168.178.39')
        self.port = tk.StringVar(self.master)
        self.port.set(str(port))
        self.player_name = tk.StringVar(self.master)
        self.found_txt = tk.StringVar(self.master)
        self.found_txt.set('')
        self.client = None

        self.verbose = verbose

        tk.Label(self.master, text='Server IP Adress:').\
            grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        tk.Label(self.master, text='Port:').\
            grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
        tk.Label(self.master, text='Player Name:').\
            grid(row=6, column=0, sticky=tk.E, padx=5, pady=5)
        tk.Label(self.master, textvariable=self.found_txt).\
            grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        tk.Entry(self.master, textvariable=self.ip).grid(
            row=1, column=1, sticky=tk.E+tk.W, padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.port).grid(
            row=2, column=1, sticky=tk.E+tk.W, padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.player_name).grid(
            row=6, column=1, sticky=tk.E+tk.W, padx=5, pady=5)

        self.connect_button = tk.Button(self.master, text='Connect',
                                        width=15, command=self.connect)
        self.connect_button.grid(row=3, column=0, columnspan=2,
                                 sticky=tk.W, padx=5, pady=5)

        self.refresh_button = tk.Button(self.master, text='Refresh',
                                        width=15, command=self.refresh)
        self.refresh_button.grid(row=3, column=0, columnspan=2,
                                 sticky=tk.E, padx=5, pady=5)
        self.deactivate_refresh_button()

        self.new_game_button = tk.Button(self.master, text='New Game',
                                         width=15, command=self.new_game)
        self.new_game_button.grid(row=7, column=0, columnspan=2,
                                  sticky=tk.W, padx=5, pady=5)

        self.join_game_button = tk.Button(self.master, text='Join Game',
                                          width=15, command=self.join_game)
        self.join_game_button.grid(row=7, column=1, sticky=tk.E,
                                   padx=5, pady=5)
        self.deactivate_join_game_button()
        self.deactivate_new_game_button()

        self.game_list = tk.Listbox(self.master, height=6, width=20)
        self.game_list.grid(row=5, column=0, columnspan=2, padx=5, pady=5,
                            sticky=tk.NSEW)

    def set_icon(self, filename):
        try:
            if not hasattr(sys, "frozen"):
                filename = os.path.join(os.path.dirname(__file__), filename)
            else:
                filename = os.path.join(sys.prefix, filename)

            self.master.iconbitmap(filename)
        except Exception:
            pass

    def set_frames(self):
        tk.Frame(self.master, width=300, height=50).\
            grid(row=0, column=0, columnspan=2)

        tk.Frame(self.master, width=100, height=30).\
            grid(row=1, column=0)
        tk.Frame(self.master, width=200, height=30).\
            grid(row=1, column=1)

        tk.Frame(self.master, width=100, height=30).\
            grid(row=2, column=0)
        tk.Frame(self.master, width=200, height=30).\
            grid(row=2, column=1)

        tk.Frame(self.master, width=300, height=30).\
            grid(row=3, column=0, columnspan=2)

        tk.Frame(self.master, width=300, height=30).\
            grid(row=4, column=0, columnspan=2)

        tk.Frame(self.master, width=300, height=100).\
            grid(row=5, column=0, columnspan=2)

        tk.Frame(self.master, width=100, height=30).\
            grid(row=6, column=0)
        tk.Frame(self.master, width=200, height=30).\
            grid(row=6, column=1)
        tk.Frame(self.master, width=300, height=30).\
            grid(row=7, column=0, columnspan=2)

    def set_geo(self):
        width = 300
        height = 400
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        off_w = int((screen_width - width) / 2)
        off_h = int((screen_height - height) / 2)

        self.master.geometry(f'{width:d}x{height:d}+{off_w:d}+{off_h:d}')

    def connect(self):
        if not self.client == None:
            self.client = None

        conn_details = self.get_connection()
        if conn_details[1] == None:
            self.found_txt.set('Connection failed!')
            return

        try:
            self.client = MaexleNetwork(conn_details[0], conn_details[1],
                                        verbose=self.verbose)
        except Exception:
            self.found_txt.set('Connection failed!')
            return

        self.activate_refresh_button()
        self.refresh()

    def refresh(self):
        self.game_list.delete(0, tk.END)
        self.deactivate_new_game_button()
        self.deactivate_join_game_button()
        games = self.client.get_games()

        self.activate_new_game_button()

        if games == None:
            self.found_txt.set('No Games found')
            return
        if len(games) == 1:
            self.found_txt.set('Found One Game')
        else:
            self.found_txt.set(f'Found {len(games):d} Games')

        self.activate_join_game_button()
        for game in games:
            self.game_list.insert(tk.END, game)


    def get_connection(self):
        ip_addr = self.ip.get()

        try:
            port = self.port.get()
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            tk.messagebox.showerror(title='Verbindung ungültig',
                                    message='Port muss eine ganze Zahl'
                                    ' zwischen 1 und 65535 sein!')
            return (None, None)

        return (ip_addr, port)

    def activate_connect_button(self):
        self.connect_button.config(state='normal')

    def deactivate_connect_button(self):
        self.connect_button.config(state='disabled')

    def activate_new_game_button(self):
        self.new_game_button.config(state='normal')

    def deactivate_new_game_button(self):
        self.new_game_button.config(state='disabled')

    def activate_join_game_button(self):
        self.join_game_button.config(state='normal')

    def deactivate_join_game_button(self):
        self.join_game_button.config(state='disabled')

    def activate_refresh_button(self):
        self.refresh_button.config(state='normal')

    def deactivate_refresh_button(self):
        self.refresh_button.config(state='disabled')

    def deactivate_all(self):
        self.deactivate_refresh_button()
        self.deactivate_new_game_button()
        self.deactivate_join_game_button()

    def get_player_name(self):
        player_name = self.player_name.get()
        if player_name == '':
            tk.messagebox.showerror(title='Name ungültig',
                                    message='Bitte Namen eingeben')
            return None

        if len(player_name) > 23:
            tk.messagebox.showerror(title='Name ungültig', message=
                                    'Name darf maximal 23 Zeichen haben')
            return None

        return player_name


    def new_game(self):
        player_name = self.get_player_name()
        if not player_name:
            return

        self.client.new_game(player_name)
        new_win = tk.Toplevel(self.master)

        self.gui = GameGUI(new_win, client=self.client,
                           player_name=player_name)
        self.gui.update_text(f'Du bist Spieler 1!')
        self.client.new_thread(self.gui, True)
        self.deactivate_all()


    def join_game(self):
        player_name = self.get_player_name()
        if not player_name:
            return
        try:
            selection = self.game_list.curselection()[0]
        except IndexError:
            tk.messagebox.showerror(title='Auswahl fehlt',
                                    message='Kein Spiel ausgewählt!')
            return

        i_player = self.client.join_game(player_name, selection)
        new_win = tk.Toplevel(self.master)
        self.gui = GameGUI(new_win, client=self.client,
                           player_name=player_name)
        self.gui.update_text(f'Du bist Spieler {i_player:d}!')
        self.client.new_thread(self.gui)
        self.deactivate_all()

    def close(self):
        if self.client:
            self.client.close()
        self.master.destroy()


class MaexleNetwork:
    def __init__(self, ip_addr, port, verbose=False):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip_addr
        self.port = port
        self.addr = (self.ip, self.port)
        self.status = self.connect()
        if self.status == None:
            raise Exception
        self.i_player = 0
        self.verbose = verbose
        if self.verbose:
            print(self.status)

    def connect(self):
        try:
            self.client.settimeout(1.0)
            self.client.connect(self.addr)
            return self.client.recv(2048).decode()
        except Exception:
            return None

    def get_games(self):
        n_games = int(self.send('n_games'))
        if self.verbose:
            print(n_games)

        if n_games == 0:
            return None

        games = []
        for i in range(n_games):
            games.append(self.send(f'game_{i:d}'))

        return games

    def new_game(self, player_name):
        self.i_player = int(self.send(f'newgame:{player_name:s}'))
        if self.verbose:
            print(self.i_player)

    def join_game(self, player_name, i_game):
        self.i_player = int(self.send(f'joingame:{i_game:d}:{player_name:s}'))
        if self.verbose:
            print(self.i_player)
        return self.i_player

    def start_game(self):
        self.send('startgame', False)

    def pass_dices(self, dice_values):
        self.send('next' + make_dices(dice_values), False)

    def close_game(self):
        self.running = False
        self.thread.join()
        self.send('closegame')
        self.i_player = 0

    def new_thread(self, gui, host=False):
        self.running = True
        self.thread = threading.Thread(target=self.thread_listen_game,
                                       args=(gui, host))
        self.pause_thread = False
        self.thread.start()

    def thread_listen_game(self, gui, host=False):
        n_player_game = self.i_player
        game_running = False

        self.client.settimeout(0.2)
        while self.running:
            if self.pause_thread:
                time.sleep(0.2)
                continue
            try:
                msg = self.client.recv(2048).decode()
                if self.verbose:
                    print(msg)
                if msg.startswith('newplayer:'):
                    pn = msg[10:]
                    gui.update_text(f'Spieler {pn:s} beigetreten!')
                    if n_player_game == 1 and host and not game_running:
                        gui.activate_start_button()
                    n_player_game += 1

                elif msg.startswith('remplayer:'):
                    pn = msg[10:]
                    gui.update_text(f'{pn:s} hat das Spiel verlassen!')
                    n_player_game -= 1
                    if n_player_game == 1 and not host:
                        host = True
                        gui.update_text('Du bist jetzt Host des Spiels!')
                    if n_player_game == 1:
                        gui.deactivate_start_button()
                        gui.deactivate_roll_button()
                        gui.deactivate_pass_button()
                        gui.deactivate_show_button()
                        gui.reset_dices()
                        gui.update_text('Warte auf andere Spieler ...')
                        game_running = False

                elif msg == 'startgame':
                    game_running = True
                    gui.update_text('Spiel gestartet!')

                elif msg == 'firstturn':
                    gui.activate_roll_button()
                    gui.update_text('Du bist dran!')

                elif msg.startswith('rolled:'):
                    pn = msg[7:]
                    gui.reset_both_dices()
                    gui.update_text(f'{pn:s} hat gewürfelt!')

                elif msg.startswith('passed:'):
                    pn = msg[7:]
                    gui.update_text(f'{pn:s} hat weitergegeben!')

                elif msg.startswith('showed:'):
                    dv = read_dices(msg[7:10])
                    gui.update_dices(numbers=dv, color='green')
                    dv_string = dice_to_string(dv)
                    pn = msg[11:]
                    gui.update_text(f'{pn:s} hat aufgedeckt: '
                                    # f'{dv[0]:d} & {dv[1]:d}!')
                                    f'{dv_string:s}!')

                elif msg == 'turn':
                    gui.update_text('Du bist dran!')
                    gui.activate_roll_button()
                    gui.activate_show_button()

            except socket.timeout:
                pass

    def roll(self):
        self.send('rolled', False)

    def show(self):
        self.pause_thread = True
        time.sleep(0.2)

        hidden_dices = read_dices(self.send('show'))
        self.pause_thread = False

        return hidden_dices

    def send(self, data, recv=True):
        try:
            self.client.send(str.encode(data))
            if recv:
                return self.client.recv(2048).decode()
            else:
                return
        except socket.error as e:
            if self.verbose:
                print(e)
            else:
                pass

    def close(self):
        self.running = False
        self.client.close()
        time.sleep(0.2)

if __name__ == '__main__':
    root = tk.Tk()
    config_file_path = pathlib.Path('.config')
    if config_file_path.is_file():
        data = read_config(config_file_path)
        ip = data['ip']
        port = data['port']
        gui = ClientGUI(root, ip=ip, port=port, verbose=False)
    else:
        gui = ClientGUI(root, verbose=False)
    root.mainloop()

