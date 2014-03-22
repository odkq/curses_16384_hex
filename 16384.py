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
        if (value >= 128):
            cattr = self._get_color_pair(0)
        else:
            cattr = attr
        self.screen.addstr(y+1, x , str(value).center(6), cattr)
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
        self.screen.addstr(4, 72, str(self.score).center(6))

    def check_win(self, some_movement):
        ''' Check for winning/loosing condition, returning a string to
            show the user in either case. If '' is returned, the game
            continues '''
        blanks = []
        # check for win
        for y in range(5):
            for x in range(self.width[y]):
                if self.board[y][x] == 16384:
                    return 'You won!'
        # check for loose (no 0es) while filling an array of blanks
        # to put a 2 in the next turn
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
            # TODO: use new conditions
            #for y in range(4):
            #    for x in range(3):
            #        if self.board[y][x + 1] == self.board[y][x]:
            #            lost = False
            #for x in range(4):
            #    for y in range(3):
            #        if self.board[y + 1][x] == self.board[y][x]:
            #            lost = False
            if lost:
                return 'You loose!'
        return ''

    def _get_color_pair(self, value):
        ''' Return the allocated color pair for a certain power of 2
            (it's exponent from 0 to 14) '''
        for i in reversed(range(14)):
            if (value >> i) > 0:
                return (i + 1)
        return 1

    def move_row(self, row, width):
        ''' Try to move elements from left to right, return true if a
            movement happened '''
        moved = False
        for x in range(width - 1):
            t = self.board[row][x]
            if t == 0:
                continue
            if self.board[row][x + 1] == 0:
                self.board[row][x] = 0
                self.board[row][x + 1] = t
                moved = True
        return moved

    def add_row(self, row, width):
        ''' Try to add elements right-to-left, return true if an addition
            happened '''
        added = False
        x = width - 1
        while x > 0:
            if self.board[row][x] == 0:
                x -= 1
                continue
            if self.board[row][x - 1] == self.board[row][x]:
                self.board[row][x] = (self.board[row][x]) * 2
                self.board[row][x - 1] = 0
                self.score += self.board[row][x]
                added = True
            x -= 1
        return added

    def move_right(self):
        ''' Perform a right movement. The rest of movements end up
            doing this after transposing the board '''
        some_movement = False
        for y in range(5):
            added = False
            moved = True
            while (moved and not added):
                added = self.add_row(y, self.width[y])
                moved = self.move_row(y, self.width[y])
                if added or moved:
                    some_movement = True
            if added:
                moved = self.move_row(y, self.width[y])
        return some_movement

    def horizontal_transpose(self):
        ''' Transpose all rows left->right right->left '''
        ''' TODO: Horizontal transposition is the same as three rotations in
            any direction '''
        for y in range(5):
            width = self.width[y]
            for x in range(width / 2):
                ax = x
                bx = width - (x + 1)
                self.exchange(ax, y, bx, y)

    def exchange(self, ax, ay, bx, by):
        t = self.board[ay][ax]
        self.board[ay][ax] = self.board[by][bx]
        self.board[by][bx] = t

    def rotate(self, counterclockwise=False):
        ''' Transpose rotating to the right '''
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
                last_value = self.board[last_element[0]][last_element[1]]
                for i in reversed(range((len(coords)))):
                    if i == 0:
                        value = last_value
                    else:
                        value = self.board[coords[i - 1][0]][coords[i - 1][1]]
                    self.board[coords[i][0]][coords[i][1]] = value

    def move_left(self):
        ''' Transpose horizontally, move and retranspose '''
        self.horizontal_transpose()
        ret = self.move_right()
        self.horizontal_transpose()
        return ret

    def move_upright(self):
        self.rotate(counterclockwise=False)
        ret = self.move_right()
        self.rotate(counterclockwise=True)
        return ret

    def move_upleft(self):
        for i in range(2):
            self.rotate(counterclockwise=False)
        ret = self.move_right()
        for i in range(2):
            self.rotate(counterclockwise=True)
        return ''

    def move_downright(self):
        self.rotate(counterclockwise=True)
        ret = self.move_right()
        self.rotate(counterclockwise=False)
        return ret

    def move_downleft(self):
        for i in range(2):
            self.rotate(counterclockwise=True)
        ret = self.move_right()
        for i in range(2):
            self.rotate(counterclockwise=False)
        return ret

    def exit(self):
        raise ExitException('quiting')


def curses_main(stdscr):
    ''' Main function called by curses_wrapper once in curses mode '''
    board = Board(stdscr)

    # Bind keys with the Board methods for them
    keys = {119: Board.move_upleft,         # w
            101: Board.move_upright,        # e
            97: Board.move_left,            # a
            102: Board.move_right,          # f
            120: Board.move_downleft,       # x
            99: Board.move_downright,       # c
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
    stdscr.addstr(0, 73, '======')
    stdscr.addstr(1, 73, ' 16384')
    stdscr.addstr(2, 73, '======')
    stdscr.addstr(3, 73, 'SCORE:')
    stdscr.addstr(4, 73, '      ')

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
    s = ('curses-16834 <pablo@odkq.com> JS Original: ' +
         '<>')
    stdscr.addstr(23, 1, s)
    # Wait for a 'q' to be pressed
    while(stdscr.getch() != 113):
        pass
    return

curses.wrapper(curses_main)
