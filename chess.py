from itertools import product
import copy, time

inRange = lambda a, b = 0: 0 <= a < 8 and 0 <= b < 8
hMirror = lambda lst: [line + line[::-1] for line in lst]

class Piece:
    weights = [[0] * 8] * 8
    baseCost = 0
    name = "*"
    black, white = -1, 1

    def __init__(self, color = None):
        self.color = color
        self.still = True

    def cost(self, x, y):
        return (self.weights[7-y][x] + self.baseCost if self.color == Piece.white
            else -self.weights[y][7-x] - self.baseCost)

    def doSequenceMoves(self, board, x, y, dx, dy):
        xy1, color = (x + dx, y + dy), None
        while inRange(*xy1) and not color:
            color = board.cells[xy1].color
            if color != self.color:
                yield from board.doMove((x,y), xy1)
            xy1 = xy1[0] + dx, xy1[1] + dy

class Pawn(Piece):
    weights = hMirror([
        [0] * 4,
        [50] * 4,
        [10, 10,  20, 30],
        [5,   5,  10, 25],
        [0,   0,   0, 20],
        [5,  -5, -10,  0],
        [5,  10,  10, -2],
        [0] * 4])
    baseCost = 100
    name = "P"

    def allMoves(self, board, x, y, _):
        y1, y2 = y + self.color, y + 2*self.color
        for dx in (-1, 1, 0):
            xy0, xy1 = (x+dx, y), (x+dx, y1)
            if inRange(*xy1) and board.cells[xy1].color == (-self.color if dx else None):
                if not dx and self.still and not board.cells[(x, y2)].color:
                    yield from board.doMove(xy0, (x, y2))
                for f in [None] if inRange(y2) else [Queen, Rock, Bishop, Knight]:
                    yield from board.doMove((x,y), xy1, None, f)
            if (inRange(*xy0) and board.cells[xy0].color == -self.color
                    and type(board.cells[xy0]) is Pawn and board.move == [(x+dx,y2), xy0]):
                yield from board.doMove((x,y), xy1, [xy0, xy1]) # En passant

class Rock(Piece):
    weights = hMirror([
        [0] * 4,
        [5, 10, 10, 10],
        *([[-5, 0, 0, 0]] * 5),
        [0, 0, 0, 5]])
    baseCost = 500
    name =  "R"

    def allMoves(self, board, x, y, _):
        for delta in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            yield from self.doSequenceMoves(board, x, y, *delta)

class Knight(Piece):
    weights = hMirror([
        [-50, -10, -30, -30],
        [-40, -20,   0,   0],
        [-30,  0,   10,  15],
        [-30,  5,   15,  20],
        [-30,  0,   15,  20],
        [-30,  5,   10,  15],
        [-40, -20,   0,   5],
        [-50, -10, -30, -30]])
    baseCost = 300
    name = "N"

    def allMoves(self, board, x, y, _):
        for dx, dy in [(2, -1), (2, 1), (-2, -1), (-2, 1), (1, -2), (1, 2), (-1, -2), (-1, 2)]:
            xy1 = x + dx, y + dy
            if inRange(*xy1) and board.cells[xy1].color != self.color:
                yield from board.doMove((x,y), xy1)

class Bishop(Piece):
    weights = hMirror([
        [-20, -10, -10, -10],
        [-10,   0,   0,   0],
        [-10,   0,   5,  10],
        [-10,   5,   5,  10],
        [-10,   0,  10,  10],
        [-10,  10,  10,  10],
        [-10,   5,   0,   0],
        [-20, -10, -10, -10]])
    baseCost = 310
    name = "B"

    def allMoves(self, board, x, y, _):
        for delta in product((-1, 1), repeat=2):
            yield from self.doSequenceMoves(board, x, y, *delta)

class Queen(Piece):
    weights = hMirror([
        [-20, -10, -10, -5],
        [-10,   0,   0,  0],
        [-10,   0,   5,  5],
        [ -5,   0,   5,  5]]) + [
        [  0,   0,   5,  5,  5,   5,   0,  -5],
        [-10,   5,   5,  5,  5,   5,   5, -10],
        [-10,   0,   5,  0,  0,   0,   0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20]]
    baseCost = 900
    name = "Q"

    def allMoves(self, board, x, y, _):
        for delta in product(range(-1,2), repeat=2):
            yield from self.doSequenceMoves(board, x, y, *delta)

class King(Piece):
    weights = hMirror([
        *([[-30, -40, -40, -50]] * 4),
        [-20, -30, -30, -40],
        [-10, -20, -20, -20],
        [ 20,  20,   0,   0],
        [ 20,  30,  10,   0]])
    baseCost = 99000
    name = "K"

    def allMoves(self, board, x, y, r):
        for x1, x2, s in [(7,5,1), (0,3,-1)]:
            if (self.still and type(board.cells[x1, y]) is Rock and board.cells[x1, y].still and
                    all(not board.cells[(i, y)].color for i in range(x+s, x1, s)) and
                    all(not board.isUnderAttack((x + s*i, y), -self.color, r) for i in range(3))):
                yield from board.doMove((x,y), (x + 2*s, y), [(x1,y), (x2,y)]) #castle
        for xy1 in product(range(x-1, x+2), range(y-1, y+2)):
            if inRange(*xy1) and board.cells[xy1].color != self.color:
                if not board.isUnderAttack(xy1, -self.color, r):
                    yield from board.doMove((x,y), xy1)

class Board:
    def __init__(self):
        self.cells = {xy: Piece() for xy in product(range(8), repeat=2)}
        for color, y in [(Piece.white, 0), (Piece.black, 7)]:
            for x in range(8): self.cells[x, y+color] = Pawn(color)
            for x, f in enumerate((Rock, Knight, Bishop, Queen)):
                for i in (x, 7-x): self.cells[i, y] = f(color)
            self.cells[4, y] = King(color)
        self.score, self.move = 0, []

    def doMove(self, src, dst, move2 = None, newDst = None):
        score = self.score
        if move2: self.movePiece(*move2)
        pieceFrom, pieceTo = self.movePiece(src, dst, newDst)
        still, pieceFrom.still = pieceFrom.still, False
        move, self.move = self.move, [src, dst]
        try:
            yield self
        finally:
            self.cells[src], self.cells[dst] = pieceFrom, pieceTo
            pieceFrom.still = still
            if move2: self.movePiece(*reversed(move2))
            self.score, self.move = score, move

    def movePiece(self, src, dst, promotion = None):
        pieceFrom, pieceTo = self.cells[src], self.cells[dst]
        self.score -= pieceFrom.cost(*src) + pieceTo.cost(*dst)
        self.cells[dst] = f = promotion(pieceFrom.color) if promotion else pieceFrom
        self.score += f.cost(*dst)
        self.cells[src] = Piece()
        return pieceFrom, pieceTo

    def print(self):
        help = {0: "R - rock", 1: "N - knight", 2: "B - bishop", 3: "Q - queen",
                4: "K - king", 5: "P - pawn", 6: "", 7: ""}
        colors = {Piece.black: '\033[95m', None: "\033[92m", Piece.white: "\033[93m"}
        white = "\033[37m"
        for y,x in sorted(self.cells):
            piece = self.cells[x, 7-y]
            print(f"{colors[piece.color]}{piece.name} ",
                end="" if x < 7 else f"{white} |{8-y}   {help[y]}\n")
        print("-" * 16)
        print("A B C D E F G H")

    def allMoves(self, color, r = None):
        for g in (c.allMoves(self, *xy, r) for xy, c in self.cells.items() if c.color == color):
            yield from g

    def doMinimax(self, color, maxDepth, depth = 0, alphaBeta = None):
        best = -color * King.baseCost
        for b in self.allMoves(color):
            score = b.doMinimax(-color, maxDepth, depth+1, best) if depth < maxDepth else b.score
            if color*score > color*best:
                best = score
                if not depth: board = copy.deepcopy(b)
            if alphaBeta != None and color*score > color*alphaBeta:
                break
        return best if depth else board

    def isUnderAttack(self, xy, color, r = None):
        return not r and any(board.move[1] == xy for board in self.allMoves(color, 1))

    def isCheck(self, color):
        for xy, cell in self.cells.items():
            if cell.color == color and type(cell) is King:
                return self.isUnderAttack(xy, -color)

    def isCheckmate(self, color, check = True):
        return self.isCheck(color) == check and all(b.isCheck(color) for b in self.allMoves(color))

    def isStalemate(self, color): return self.isCheckmate(color, False)

def userMove(color, board):
    while True:
        move = input("Your move? ").lower().split("-")
        move = [tuple(ord(a) - ord(b) for a, b in zip(m, "a1")) for m in move]
        try:
            piece = board.cells[move[0]]
            g = piece.allMoves(board, *move[0], None)
            if piece.color == color and any(move == b.move and not b.isCheck(color) for b in g):
                break
            print("Invalid move.")
        except:
            print("invalid move format. Move example: e2-e4")
    while type(piece) is Pawn and not inRange(move[1][1] + color):
        prompt = input("Promote to (Q/R/B/N)? ").upper()
        for f in [Queen, Rock, Bishop, Knight]:
            if f.name == prompt: return *move, f
    return *move, None

board = Board()
board.print()
userColor = input("Would you like to play white? (y/n)")
userColor = Piece.white if userColor.lower() == "y" else Piece.black
player = Piece.white
while not (board.isCheckmate(player) or board.isStalemate(player)):
    if player != userColor:
        t0 = time.time()
        board = board.doMinimax(player, 3)
        move = '-'.join(chr(ord("a") + m[0]) + str(m[1] + 1) for m in board.move)
        print(f"Time: {round(time.time()-t0, 1)} sec. Move: {move}")
    else:
        src, dst, promotion = userMove(userColor, board)
        piece, to = board.movePiece(src, dst, promotion)
        board.move = [src, dst]
        piece.still = False
        dx = dst[0] - src[0]
        if type(piece) is Pawn and not to.color and dx:
            board.movePiece(src, (dst[0], src[1])) # En passant
        if type(piece) is King and abs(dx) == 2: # Castle, move rock
            board.movePiece(({2:7, -2:0}[dx], src[1]), ({2:5, -2:3}[dx], src[1]))
    board.print()
    player = -player
if board.isStalemate(player):
    print("Stalemate. Draw.")
else:
    print("White" if board.isCheckmate(Piece.black) else "Black", "win.")
