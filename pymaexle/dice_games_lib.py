# -*- coding: utf-8 -*-        Traceback (most recent call last):
"""
Created on Tue May  5 10:10:25 2020

@author: Leonard Maisch
"""
import doctest
import json

class Player:
    """Defines properties of a player object for handling on server"""

    def __init__(self, name, conn):
        self.name = name
        self.conn = conn
        self.game = None

    def send(self, string):
        """Send a string to the players socket.

        Arguments
            string: (str) Message to be sent

        """
        self.conn.sendall(str.encode(string))


class DiceGame:
    """Parent class for all dice game classes"""

    def __init__(self, player_1):
        self.players = [player_1]
        self.active = False
        self.curr_player = None
        self.game_type = 'Generic'

    def get_name(self):
        """Create a name string for the game, with game type and players."""

        game_name = self.game_type + ': ' + \
            ', '.join([player.name for player in self.players])
        return game_name

    def add_player(self, new_player):
        """Add a new player and send notification to all other players."""

        for player in self.players:
            player.send('newplayer:' + new_player.name)
        self.players.append(new_player)

    def remove_player(self, rem_player):
        """Remove a player from the game.

        Remove a player from the game. Check if the removed player is the
        current one, if so, set to next player first.
        Afterwards, send notification to other players.

        """
        if len(self.players) == 1:
            self.players.remove(rem_player)
            return

        if self.players.index(rem_player) == self.curr_player:
            players_turn = True
        else:
            players_turn = False

        self.players.remove(rem_player)
        for player in self.players:
            player.send('remplayer:' + rem_player.name)

        if players_turn and len(self.players) > 1:
            self.first_turn()

    def next_player(self):
        """Set Current Player to next one and send notification."""

        self.curr_player += 1
        if self.curr_player == len(self.players):
            self.curr_player = 0
        self.players[self.curr_player].send('turn')

    def first_turn(self):
        """Send notification about first turn to the second player."""

        self.curr_player = 1
        self.players[self.curr_player].send('firstturn')

    def start_game(self):
        """Start game and send notification to all players."""

        self.active = True
        for player in self.players:
            player.send('startgame')

    def end_game(self):
        """Set game to inactive."""

        self.active = False

    def send_to_players(self, from_player, msg):
        """Send a message to all players, except the origin player."""

        for player in self.players:
            if player == from_player:
                continue
            player.send(msg)


class MaexleGame(DiceGame):
    """Class for a Maexle-Game."""

    def __init__(self, player_1):
        super().__init__(player_1)
        self.hidden_dices = (None, None)
        self.game_type = 'Maexle'

    def pass_dices(self, dice_values):
        self.next_player()
        self.hidden_dices = dice_values

    def get_hidden_dices(self):
        h_d = self.hidden_dices
        self.hidden_dices = (None, None)
        return h_d


def read_dices(string):
    """Read a tuple of dice values from string.

    From a given string, values sepaated by ',', are extracted and returned
    as tuple.

    Arguments:
        string: (str) string with comma separated integer values

    Returns:
        tuple: (tuple) containing read dice values

    Examples:
        >>> read_dices('1,3')
        (1, 3)

        >>> read_dices('3,5,4')
        (3, 5, 4)

        Only strings allowed:

        >>> read_dices((1, 6))
        Traceback (most recent call last):
        TypeError: Only strings allowed to read dice values, not <class 'tuple'>

        Only integer numbers allowed in string:

        >>> read_dices('1.4,3,8')
        Traceback (most recent call last):
        TypeError: Only integers allowed, not 1.4

        Only integer values between 1 and 6 allowed:

        >>> read_dices('3,6,8')
        Traceback (most recent call last):
        ValueError: Only values between 1 and 6 allowed, not 8

    """
    if not type(string) == str:
        raise TypeError('Only strings allowed to read dice values, not ' + str(type(string)))

    string_parts = string.split(',')
    lst = []
    for s in string_parts:
        try:
            number = int(s)
        except ValueError:
            raise TypeError('Only integers allowed, not ' + s)

        if number < 1 or number > 6:
            raise ValueError(f'Only values between 1 and 6 allowed, not {number:d}')

        lst.append(int(number))
    return tuple(lst)


def make_dices(tup):
    """Make a string with comma separated dice values from tuple.

    From a given tuple, dice values are written in a string separated by
    ','

    Arguments:
        tup: (tuple) Tuple with dice values

    Returns:
        string: (str) string with dice values separated by comma

    Examples:
        >>> make_dices((1, 3))
        '1,3'

        >>> make_dices((5, 6))
        '5,6'

        Only tuple allowed:

        >>> make_dices('4,7')
        Traceback (most recent call last):
        TypeError: Only tuples allowed, not <class 'str'>

        Only integer values allowed in tuple:

        >>> make_dices((1.5, 3))
        Traceback (most recent call last):
        TypeError: Only integer values allowed, not 1.5

        Only integer values between 1 and 6 allowed:

        >>> make_dices((3, 5, 8))
        Traceback (most recent call last):
        ValueError: Only values between 1 and 6 allowed, not 8

    """
    if not type(tup) == tuple:
        raise TypeError('Only tuples allowed, not ' + str(type(tup)))

    for number in tup:
        if not type(number) == int:
            raise TypeError('Only integer values allowed, not ' + str(number))

        if number < 1 or number > 6:
            raise ValueError(f'Only values between 1 and 6 allowed, not {number:d}')

    string = ','.join(str(number) for number in tup)
    return string

def dice_to_string(tup):
    """
    Create a string representation from given tuple of dice values

    Inputs:
        tup (tuple): Tuple with dice values between 1 and 6
    """
    if not type(tup) == tuple:
        raise TypeError('Only tuples allowed, not ' + str(type(tup)))

    if tup[0] == tup[1]:
        return f'{tup[0]:d}er Pasch'

    ls = list(tup)
    ls.sort(reverse=True)

    if ls[0] == 2 and ls[1] == 1:
        return 'Mäxle'

    return f'{ls[0]:d}{ls[1]:d}'

def read_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

if __name__ == '__main__':
    doctest.testmod()