#!/usr/bin/env python
"""
 16384.py - Minimal implementation of 2048 game with python/ncurses
            See http://rudradevbasak.github.io/16384_hex/ for the original
            game in js

 Copyright (C) 2014 Pablo Martin <pablo@odkq.com>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import copy
import curses
import random


class ExitException(Exception):
    pass

class Board:
    def __init__(self, screen):
        self.screen = screen
        self.score = 0
        self.board = self._blank_board()
        self.width = [3, 4, 5, 4, 3]

    def _blank_board(self):
        ''' Handy allocator used twice '''
        return [[0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0],
                [0, 0, 0, 0], [0, 0, 0]]

    def draw_tile(self, x, y, value):
        ''' Draw a tile '''
        attr = self.attribs[self._get_color_pair(value)]
        self.screen.addstr(y, x + 1, '    ', attr)
        self.screen.addstr(y+1, x , '      ', attr)
        if (value >= 128):
            cattr = self._get_color_pair(0)
        else:
            cattr = attr
        if len(str(value)) > 4:
            centerin = 6
            offset = 0
        else:
            centerin = 4
            offset = 1
        self.screen.addstr(y+1, x + offset, str(value).center(centerin), cattr)
        self.screen.addstr(y+2, x + 1, '    ', attr)
        # chars = str(value).center(4)
        # draw the last row
        # dx = x + 16
        #for dy in range(y, y + 3):
        #    self.screen.addstr(dy, dx, '*', attr)

    def draw(self):
        ''' Draw all the tiles in the board and print the score '''
        for y in range(5):
            for x in range(self.width[y]):
                value = self.board[y][x]
                px = (x * 8) + 1 + ((5 - self.width[y])*4)
                py = (y * 4) + 1
                self.draw_tile(px, py, value)
        self.screen.addstr(5, 72, str(self.score).center(6))

    def check_win(self, some_movement):
        ''' Check for winning/loosing condition, returning a string to
            show the user in either case. If '' is returned, the game
            continues '''
        blanks = []
        # check for win
        for y in range(5):
            for x in range(self.width[y]):
                if self.board[y][x] == 16384:
                    return 'You won! Press q to exit'
        # fill an array with the blanks found
        for y in range(5):
            for x in range(self.width[y]):
                if self.board[y][x] == 0:
                    blanks.append([y, x])
        # Now put a '2' or a '4' with 10% probability
        # randomly in any of the blanks, but only if a movement was reported
        if some_movement:
            choosen = random.randrange(len(blanks))
            y, x = blanks[choosen]
            randvalue = random.choice([2, 2, 2, 2, 2, 2, 2, 2, 2, 4])
            self.board[y][x] = randvalue  # Allow for one 4 in ten
            del blanks[choosen]     # Remove element for next check 
        if len(blanks) == 0:
            # If an addition can be made, then it is not a loose yet
            lost = True
            testboard = copy.deepcopy(self.board)   # Make a copy for testing
            # Simulate all movements over the temp board
            # and see if there is any addition
            for move_function in [self.move_right, self.move_left,
                                  self.move_upleft, self.move_upright,
                                  self.move_downleft, self.move_downright]:
                if move_function(testboard):
                    lost = False
                    break
            if lost:
                return 'You loose! Press q to exit'
        return ''

    def _get_color_pair(self, value):
        ''' Return the allocated color pair for a certain power of 2
            (it's exponent from 0 to 14) '''
        for i in reversed(range(14)):
            if (value >> i) > 0:
                return (i + 1)
        return 1

    def move_row(self, row, width, board):
        ''' Try to move elements from left to right, return true if a
            movement happened '''
        moved = False
        for x in range(width - 1):
            t = board[row][x]
            if t == 0:
                continue
            if board[row][x + 1] == 0:
                board[row][x] = 0
                board[row][x + 1] = t
                moved = True
        return moved

    def add_row(self, row, width, board):
        ''' Try to add elements right-to-left, return true if an addition
            happened '''
        added = False
        x = width - 1
        while x > 0:
            if board[row][x] == 0:
                x -= 1
                continue
            if board[row][x - 1] == board[row][x]:
                board[row][x] = (board[row][x]) * 2
                board[row][x - 1] = 0
                if id(board) == id(self.board):
                    self.score += board[row][x]
                added = True
            x -= 1
        return added

    def move_right(self, board=None):
        ''' Perform a right movement. The rest of movements end up
            doing this after rotating the board '''
        if board is None:
            board = self.board
        some_movement = False
        for y in range(5):
            added = False
            moved = True
            while (moved and not added):
                added = self.add_row(y, self.width[y], board)
                moved = self.move_row(y, self.width[y], board)
                if added or moved:
                    some_movement = True
            if added:
                moved = self.move_row(y, self.width[y], board)
        return some_movement

    def rotate(self, board=None, counterclockwise=False):
        ''' Transpose rotating to the right '''
        if board is None:
            board = self.board
        clockwise_outer_coords = [[0, 0], [0, 1], [0, 2], [1, 3],
                                  [2, 4], [3, 3], [4, 2], [4, 1],
                                  [4, 0], [3, 0], [2, 0], [1, 0]]
        clockwise_inner_coords = [[1, 1], [1, 2], [2, 3], [3, 2],
                                  [3, 1], [2, 1]]
        if counterclockwise:
            outer_coords = [x for x in reversed(clockwise_outer_coords)]
            inner_coords = [x for x in reversed(clockwise_inner_coords)]
        else:
            outer_coords = clockwise_outer_coords
            inner_coords = clockwise_inner_coords
        for coords, times in [[outer_coords, 2], [inner_coords, 1]]:
            # Rotate three times the outer ring and two times the inner ring
            for t in range(times):
                last_element = coords[len(coords) - 1]
                last_value = board[last_element[0]][last_element[1]]
                for i in reversed(range((len(coords)))):
                    if i == 0:
                        value = last_value
                    else:
                        value = board[coords[i - 1][0]][coords[i - 1][1]]
                    board[coords[i][0]][coords[i][1]] = value

    def move_left(self, board=None):
        ''' Transpose horizontally by rotating 3 times left and retranspose '''
        if board is None:
            board = self.board
        for i in range(3):
            self.rotate(board, counterclockwise=False)
        ret = self.move_right(board)
        for i in range(3):
            self.rotate(board, counterclockwise=True)
        return ret

    def move_upright(self, board=None):
        if board is None:
            board = self.board
        self.rotate(board, counterclockwise=False)
        ret = self.move_right(board)
        self.rotate(board, counterclockwise=True)
        return ret

    def move_upleft(self, board=None):
        if board is None:
            board = self.board
        for i in range(2):
            self.rotate(board, counterclockwise=False)
        ret = self.move_right(board)
        for i in range(2):
            self.rotate(board, counterclockwise=True)
        return ret

    def move_downright(self, board=None):
        if board is None:
            board = self.board
        self.rotate(board, counterclockwise=True)
        ret = self.move_right(board)
        self.rotate(board, counterclockwise=False)
        return ret

    def move_downleft(self, board=None):
        if board is None:
            board = self.board
        for i in range(2):
            self.rotate(board, counterclockwise=True)
        ret = self.move_right(board)
        for i in range(2):
            self.rotate(board, counterclockwise=False)
        return ret

    def exit(self):
        raise ExitException('quiting')

    def print_help(self): 
        message = '''
 Join the numbers and
 get to the 16384 tile!

  W               E
    .           .
      .       . 
        .   .
A . . . . . . . . . D
        .   .
      .       .
    .           .
  Z               X

 HOW TO PLAY: Use the keys W, E,
 A, D, Z, X to move the tiles in
 the six possible directions.
 When two tiles with the same
 number touch, they merge into
 one!

 Press q at anytime to exit'''
        y = 1
        for line in message.split('\n'):
            self.screen.addstr(y, 43, line)
            y += 1
            

def curses_main(stdscr):
    ''' Main function called by curses_wrapper once in curses mode '''
    board = Board(stdscr)

    # Bind keys with the Board methods for them
    keys = {119: Board.move_upleft,         # w
            101: Board.move_upright,        # e
            97: Board.move_left,            # a
            100: Board.move_right,          # f
            122: Board.move_downleft,       # x
            120: Board.move_downright,       # c
            114: Board.rotate,
            113: Board.exit}

    if curses.has_colors():
        color = [[curses.COLOR_BLACK, curses.COLOR_BLACK],
                 [curses.COLOR_BLACK, curses.COLOR_WHITE],
                 [curses.COLOR_BLACK, curses.COLOR_CYAN],
                 [curses.COLOR_BLACK, curses.COLOR_BLUE],
                 [curses.COLOR_BLACK, curses.COLOR_GREEN],
                 [curses.COLOR_BLACK, curses.COLOR_YELLOW],
                 [curses.COLOR_BLACK, curses.COLOR_MAGENTA],
                 [curses.COLOR_BLACK, curses.COLOR_RED],
                 [curses.COLOR_BLACK, curses.COLOR_CYAN],
                 [curses.COLOR_BLACK, curses.COLOR_BLUE],
                 [curses.COLOR_BLACK, curses.COLOR_GREEN],
                 [curses.COLOR_BLACK, curses.COLOR_YELLOW],
                 [curses.COLOR_BLACK, curses.COLOR_MAGENTA],
                 [curses.COLOR_BLACK, curses.COLOR_RED],
                 [curses.COLOR_BLACK, curses.COLOR_RED]]
        for i in range(1, 15):
            curses.init_pair(i, color[i][0], color[i][1])

    # Setup attributes array with colors if the terminal have them, or
    # just as NORMAL/INVERSE if it has not
    board.attribs = []
    for i in range(15):
        if curses.has_colors():
            attr = curses.color_pair(i)
        else:
            if i == 0:
                attr = curses.A_NORMAL
            else:
                attr = curses.A_REVERSE
        board.attribs.append(attr)

    # Print the text on the right
    stdscr.addstr(0, 72, '=====')
    stdscr.addstr(1, 72, '16384')
    stdscr.addstr(2, 72, '=====')
    stdscr.addstr(4, 72, 'SCORE:')
    stdscr.addstr(5, 72, '      ')
    board.print_help()
    board.check_win(True)    # Put the first 2 2/4 in place
    board.check_win(True)
    while True:
        board.draw()
        try:
            some_movement = keys[stdscr.getch()](board)
        except KeyError:
            some_movement = False   # Wrong key, do not add anything in check_
            pass
        except ExitException:
            return
        s = board.check_win(some_movement)
        if len(s) != 0:
            break
    # Redraw board (in case of a win show the 2048)
    board.draw()
    # Draw endgame string
    s = '| ' + s + ' |'
    frame = '+' + ('-' * (len(s) - 2)) + '+'
    stdscr.addstr(11, 40 - (len(s) / 2), frame)
    stdscr.addstr(12, 40 - (len(s) / 2), s)
    stdscr.addstr(13, 40 - (len(s) / 2), frame)
    s = ('curses_16834_hex,  <pablo@odkq.com>')
    stdscr.addstr(22, 1, s)
    s = ('JS Original: http://rudradevbasak.github.io/16384_hex/')
    stdscr.addstr(23, 1, s)
    # Wait for a 'q' to be pressed
    while(stdscr.getch() != 113):
        pass
    return

curses.wrapper(curses_main)
