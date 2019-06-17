from random import randint as rand, random as randf

import pyxel


W = 128
H = 128


pieces = [
    [0x0F00, 0x8E00, 0x2E00, 0x0660, 0x6C00, 0x4E00, 0xC600],
    [0x2222, 0x6440, 0x4460, 0x0660, 0x4620, 0x4640, 0x2640],
    [0x00F0, 0x0E20, 0x0E80, 0x0660, 0x06C0, 0x0E40, 0x0C60],
    [0x4444, 0x44C0, 0xC440, 0x0660, 0x8C40, 0x4C40, 0x4C80],
]


def each_block(x, y, piece_idx, angle):
    piece = pieces[angle][piece_idx]
    for j in range(4):
        for i in range(4):
            mask = 1 << (15 - (i + j * 4))
            if piece & mask == mask:
                yield x + i, y - j


BW = 10
BH = 24
CZ = 4


class Blox:
    def __init__(self):
        pyxel.init(W - 1, H - 1, caption="blox")
        pyxel.load("assets.pyxel")

        self.cx = 0
        self.cy = 0
        self.ct = 0

        self.reset()

    def reset(self):
        self.board = [[None for _ in range(BW)] for _ in range(BH)]
        self.fall_interval = 16
        self.next_fall = rand(0, 6)
        self.new_fall()
        self.score = 0

    def punch(self, mag):
        self.ct = mag

    def punch_down(self):
        self.ct = 0
        self.cy = 1
        self.cx = 0

    def new_fall(self):
        self.falling = self.next_fall
        self.next_fall = rand(0, 6)
        self.fx = BW // 2 - 2
        self.fy = BH + 3
        self.fa = 0
        self.fall_timer = self.fall_interval

    def transform(self, x, y):
        return ((W - BW * CZ) // 2 + x * CZ, (H + BH * CZ) // 2 - y * CZ)

    def get(self, x, y):
        if x < 0 or x >= BW or y < 0 or y >= BH:
            return None
        return self.board[y][x]

    def set(self, x, y, idx):
        if x < 0 or x >= BW or y < 0 or y >= BH:
            return
        self.board[y][x] = idx

    def clear_row(self, row):
        for j in range(row, BH):
            for i in range(0, BW):
                self.set(i, j, self.get(i, j + 1))

    def clear_rows(self):
        cleared = 0
        for j in range(BH - 1, -1, -1):
            for i in range(0, BW):
                if self.get(i, j) is None:
                    break
            else:
                self.clear_row(j)
                cleared += 1
        return cleared

    def place_piece(self):
        for i, j in each_block(self.fx, self.fy, self.falling, self.fa):
            self.set(i, j, self.falling)

        cleared = self.clear_rows()
        self.score += 100 * (cleared + 1) ** 3
        self.new_fall()

        if cleared > 0:
            self.punch(cleared * 2)
        else:
            self.punch_down()

    def in_bounds(self, x, y):
        return x >= 0 and x < BW and y >= 0

    def space_clear(self, x, y):
        return self.in_bounds(x, y) and self.get(x, y) is None

    def rotate(self):
        ang = (self.fa + 1) % 4

        for i, j in each_block(self.fx, self.fy, self.falling, ang):
            if not self.space_clear(i, j):
                break
        else:
            self.fa = ang
            return  # no kick required

        for i, j in each_block(self.fx + 1, self.fy, self.falling, ang):
            if not self.space_clear(i, j):
                break
        else:
            # kick right
            self.fx += 1
            self.fa = ang
            return

        for i, j in each_block(self.fx - 1, self.fy, self.falling, ang):
            if not self.space_clear(i, j):
                break
        else:
            # kick left
            self.fx -= 1
            self.fa = ang
            return

    def try_move(self, x, y):
        for i, j in each_block(x, y, self.falling, self.fa):
            if not self.space_clear(i, j):
                return
        self.fx = x
        self.fy = y

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()

        if self.ct > 0:
            self.cx = -self.ct + randf() * self.ct * 2
            self.cy = -self.ct + randf() * self.ct * 2
            self.ct -= 1
        else:
            self.cx = 0
            self.cy = 0
            self.ct = 0

        self.fall_timer -= 1 + (7 if pyxel.btn(pyxel.KEY_DOWN) else 0)
        if self.fall_timer <= 0:
            self.fy -= 1
            self.fall_timer = self.fall_interval

        if pyxel.btnp(pyxel.KEY_UP):
            self.rotate()

        if pyxel.btnp(pyxel.KEY_LEFT):
            self.try_move(self.fx - 1, self.fy)
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            self.try_move(self.fx + 1, self.fy)

        if self.falling is None or pyxel.btnp(pyxel.KEY_SPACE):
            self.new_fall()

        for i, j in each_block(self.fx, self.fy, self.falling, self.fa):
            if j <= 0 or self.get(i, j - 1) is not None:
                self.place_piece()
                break

    def draw(self):
        pyxel.cls(0)

        def p(x, y):
            return (x + self.cx, y + self.cy)

        for j in range(BH):
            for i in range(BW):
                x, y = self.transform(i, j)
                if self.board[j][i] is not None:
                    pyxel.blt(*p(x, y), 0, 16 + self.board[j][i] * CZ, 0, CZ, CZ)
                else:
                    pyxel.rectb(*p(x, y), *p(CZ, CZ), 1)

        for i, j in each_block(self.fx, self.fy, self.falling, self.fa):
            x, y = self.transform(i, j)
            pyxel.blt(*p(x, y), 0, 16 + self.falling * CZ, 0, CZ, CZ)

        for i, j in each_block(BW + 1, BH - 1, self.next_fall, 0):
            x, y = self.transform(i, j)
            pyxel.blt(*p(x, y), 0, 16 + self.next_fall * CZ, 0, CZ, CZ)

        pyxel.text(*p(4, 4), f"{self.score:09}", 7)


if __name__ == "__main__":
    Blox().run()
