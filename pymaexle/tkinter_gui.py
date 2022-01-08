# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 15:02:59 2020

@author: Leonard Maisch
"""

import tkinter as tk
import random
import sys, os
import textwrap

def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
tk.Canvas.create_circle = _create_circle


class GameGUI:
    def __init__(self, master, client=None, player_name=None):
        self.master = master
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        self.master.resizable(False, False)
        self.set_icon('twodices.ico')

        if player_name:
            self.master.title('Quarantäne-Mäxle: ' + player_name)
        else:
            self.master.title('Quarantäne-Mäxle')
        self.client = client
        self.set_geo()

        self.set_frames()
        self.set_buttons()

        self.master.bind('<space>', self.key_show)
        self.master.bind('q', self.key_pass)
        self.master.bind('r', self.key_roll)

        tk.Label(self.master, text='Quarantäne-Mäxle',
                 font=('Courier', 20)).\
            grid(row=0, column=0)

        self.text_var = tk.StringVar(self.master)
        self.text_var.set('\n'*12)


        self.text_ent = tk.Label(self.master, textvariable=self.text_var,
                                 font=('Courier', 10), bg='white',
                                 wraplength=200, height=12, anchor=tk.N,
                                 justify=tk.LEFT)
        self.text_ent.grid(row=0, column=1, rowspan=2, padx=3, pady=3,
                           sticky=tk.N+tk.W)

        self.dice_shapes = ([], [])
        self.dice_values = (None, None)
        self.update_dices()

        self.deactivate_pass_button()
        self.deactivate_show_button()
        self.deactivate_start_button()
        if self.client:
            self.deactivate_roll_button()
        else:
            self.activate_roll_button()

    def set_icon(self, filename):
        try:
            if not hasattr(sys, "frozen"):
                filename = os.path.join(os.path.dirname(__file__), filename)
            else:
                filename = os.path.join(sys.prefix, filename)

            self.master.iconbitmap(filename)
        except Exception:
            pass

    def set_geo(self):
        width = 500
        height = 500
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        off_w = int((screen_width - width) / 2)
        off_h = int((screen_height - height) / 2)

        self.master.geometry(f'{width:d}x{height:d}+{off_w:d}+{off_h:d}')

    def set_frames(self):
        border_dict = {'highlightthickness': 2,
                       'highlightbackground': 'black'}

        c1_width = 290
        c2_width = 500 - c1_width
        tk.Frame(self.master, width=c2_width, height=200, **border_dict,
                 bg='white').grid(row=0, column=1, rowspan=2)

        self.master.grid_columnconfigure(0, minsize=c1_width)
        self.master.grid_columnconfigure(1, weight=1, minsize=c2_width)

        self.master.grid_rowconfigure(0, weight=1, minsize=70)
        self.master.grid_rowconfigure(1, weight=1, minsize=130)
        self.master.grid_rowconfigure(2, weight=1, minsize=90)
        self.master.grid_rowconfigure(3, weight=1, minsize=50)
        self.master.grid_rowconfigure(4, weight=1, minsize=50)
        self.master.grid_rowconfigure(5, weight=1, minsize=50)
        self.master.grid_rowconfigure(6, weight=1, minsize=50)
        self.master.grid_rowconfigure(7, minsize=10)

        self.canvas = tk.Canvas(self.master, width=c1_width, height=430,
                                highlightthickness=0)
        self.canvas.grid(row=1, column=0, rowspan=7)

    def set_buttons(self):
        self.start_button = tk.Button(self.master, text='Start',
                                      width=15, command=self.start_game)
        self.start_button.grid(row=2, column=1, sticky=tk.S,
                               padx=5, pady=5)
        self.show_button = tk.Button(self.master, text='Aufdecken',
                                     command=self.show, width=15)
        self.show_button.grid(row=3, column=1, sticky=tk.S,
                              padx=5, pady=5)

        self.roll_dice_button = tk.Button(self.master, text='Würfeln',
                                          command=self.roll_dice,
                                          width=15)
        self.roll_dice_button.grid(row=4, column=1, sticky=tk.S,
                                   padx=5, pady=5)

        self.pass_button = tk.Button(self.master, text='Weitergeben',
                                     command=self.pass_dices, width=15)
        self.pass_button.grid(row=5, column=1, sticky=tk.S,
                              padx=5, pady=5)

        self.close_button = tk.Button(self.master, text='Schließen',
                                      command=self.close, width=15)
        self.close_button.grid(row=6, column=1, sticky=tk.S,
                               padx=5, pady=5)

    def draw_dice(self, n_dice, num, color='black'):
        size = 150
        x1 = 75
        if n_dice == 0:
            y1 = 40
        elif n_dice == 1:
            y1 = 240
        x2 = x1 + size
        y2 = y1 + size

        self.dice_shapes[n_dice].append(
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         fill='white', width=4))

        circ_coords = []
        if num == None:
            pos = ((x1 + x2) / 2, (y1 + y2) / 2,)
            self.dice_shapes[n_dice].append(
                self.canvas.create_text(pos, text='?',
                                        font=('Purisa',55)))
            return
        if num == 0:
            pass
        elif num == 1:
            circ_coords.append(((x1 + x2) / 2, (y1 + y2) / 2,))
        elif num == 2:
            circ_coords.append((x1 + (x2 - x1) / 4, y1 + (y2 - y1) / 4,))
            circ_coords.append((x2 - (x2 - x1) / 4, y2 - (y2 - y1) / 4,))
        elif num == 3:
            circ_coords.append((x1 + (x2 - x1) / 6, y1 + (y2 - y1) / 6,))
            circ_coords.append((x1 + (x2 - x1) / 2, y1 + (y2 - y1) / 2,))
            circ_coords.append((x2 - (x2 - x1) / 6, y2 - (y2 - y1) / 6,))
        elif num == 4:
            circ_coords.append((x1 + (x2 - x1) / 4, y1 + (y2 - y1) / 4,))
            circ_coords.append((x2 - (x2 - x1) / 4, y1 + (y2 - y1) / 4,))
            circ_coords.append((x1 + (x2 - x1) / 4, y2 - (y2 - y1) / 4,))
            circ_coords.append((x2 - (x2 - x1) / 4, y2 - (y2 - y1) / 4,))
        elif num == 5:
            circ_coords.append((x1 + (x2 - x1) / 4, y1 + (y2 - y1) / 4,))
            circ_coords.append((x2 - (x2 - x1) / 4, y1 + (y2 - y1) / 4,))
            circ_coords.append((x1 + (x2 - x1) / 4, y2 - (y2 - y1) / 4,))
            circ_coords.append((x2 - (x2 - x1) / 4, y2 - (y2 - y1) / 4,))
            circ_coords.append(((x1 + x2) / 2, (y1 + y2) / 2,))
        elif num == 6:
            circ_coords.append((x1 + (x2 - x1) / 6, y1 + (y2 - y1) / 6,))
            circ_coords.append((x2 - (x2 - x1) / 6, y1 + (y2 - y1) / 6,))
            circ_coords.append((x1 + (x2 - x1) / 6, y1 + (y2 - y1) / 2,))
            circ_coords.append((x2 - (x2 - x1) / 6, y1 + (y2 - y1) / 2,))
            circ_coords.append((x1 + (x2 - x1) / 6, y2 - (y2 - y1) / 6,))
            circ_coords.append((x2 - (x2 - x1) / 6, y2 - (y2 - y1) / 6,))

        for pos in circ_coords:
            self.dice_shapes[n_dice].append(
                self.draw_num_circ(pos, color=color))


    def draw_num_circ(self, pos, color='black'):
        radius = 10
        return self.canvas.create_circle(pos[0], pos[1],
                                         radius, fill=color)

    def reset_dice(self, n_dice):
        for shape in self.dice_shapes[n_dice]:
            self.canvas.delete(shape)

    def reset_both_dices(self):
        self.reset_dice(0)
        self.reset_dice(1)

        self.draw_dice(0, None)
        self.draw_dice(1, None)


    def update_dices(self, numbers=None, color='black'):
        self.reset_dice(0)
        self.reset_dice(1)

        if numbers == None:
            self.draw_dice(0, self.dice_values[0], color=color)
            self.draw_dice(1, self.dice_values[1], color=color)
        else:
            self.draw_dice(0, numbers[0], color=color)
            self.draw_dice(1, numbers[1], color=color)

    def roll_dice(self):
        num_1 = random.randint(1, 6)
        num_2 = random.randint(1, 6)

        self.dice_values = (num_1, num_2)

        self.update_dices()
        self.update_text('Neu gewürfelt')
        self.deactivate_roll_button()
        self.deactivate_show_button()
        self.activate_pass_button()

        if self.client:
            self.client.roll()

    def pass_dices(self):
        """

        """
        if self.dice_values[0] == None:
            # Safety: Passing None makes game crash, unknown cause
            # Possibly reseting dice before deactivating button made it possible
            # to pass again => TODO: See if problem occurs again
            return
        if self.client:
            self.deactivate_roll_button()
            self.client.pass_dices(self.dice_values)
        else:
            # Testing: GUI without client, should be able to roll after passing
            self.activate_roll_button()

        self.deactivate_pass_button()
        self.reset_dices()
        self.update_text('Würfel weitergegeben')

    def reset_dices(self):
        self.dice_values = (None, None)
        self.update_dices()

    def show(self):
        if self.client:
            self.dice_values = self.client.show()
            self.update_text('Aufgedeckt')
            self.update_dices(color='red')
            self.deactivate_show_button()
        else:
            pass

    def key_show(self, event):
        if str(self.show_button['state']) == 'disabled':
            pass
        else:
            self.show()

    def key_pass(self, event):
        if str(self.pass_button['state']) == 'disabled':
            pass
        else:
            self.pass_dices()

    def key_roll(self, event):
        if str(self.roll_dice_button['state']) == 'disabled':
            pass
        else:
            self.roll_dice()

    def start_game(self):
        if self.client:
            self.client.start_game()
            self.deactivate_start_button()
        else:
            pass

    def activate_roll_button(self):
        self.roll_dice_button.config(state='normal')

    def deactivate_roll_button(self):
        self.roll_dice_button.config(state='disabled')

    def activate_pass_button(self):
        self.pass_button.config(state='normal')

    def deactivate_pass_button(self):
        self.pass_button.config(state='disabled')

    def activate_show_button(self):
        self.show_button.config(state='normal')

    def deactivate_show_button(self):
        self.show_button.config(state='disabled')

    def activate_start_button(self):
        self.start_button.config(state='normal')

    def deactivate_start_button(self):
        self.start_button.config(state='disabled')

    def update_text(self, text, max_lines=12):
        new_lines = textwrap.wrap(text, 25, break_long_words=False)
        new_text = self.text_var.get() + '\n' + '\n'.join(new_lines)
        self.text_var.set(new_text)
        lines = self.text_var.get().split('\n')

        # print(lines)
        n_lines = len(lines)
        if n_lines > max_lines:
            lines = lines[n_lines-max_lines:]

        # print(lines)
        # print('\n'.join(lines))
        self.text_var.set('\n'.join(lines))


    def close(self):
        if self.client:
            self.client.close_game()
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    gui = GameGUI(root)
    root.mainloop()