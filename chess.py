from itertools import product
import copy, time

inRange = lambda x, y: 0 <= x < 8 and 0 <= y < 8
isLastLine = lambda y: y == 0 or y == 7
hMirror = lambda lst: [sublist + sublist[::-1] for sublist in lst]

class Color:
    black, none, white = -1, 0, 1

class Figure:
    weights = [[0] * 8] * 8
    baseCost = 0
    name = "*"

    def __init__(self, color = Color.none):
        self.color = color
        self.hasMoved = False

    def cost(self, x, y):
        return (self.weights[7-y][x] + self.baseCost if self.color == Color.white
            else -self.weights[y][7-x] - self.baseCost)

    def doSequenceMoves(self, board, x, y, dx, dy):
        xy1, color = (x + dx, y + dy), None
        while inRange(*xy1) and not color:
            color = board.cells[xy1].color
            if color != self.color:
                yield from board.move((x,y), xy1)
            xy1 = xy1[0] + dx, xy1[1] + dy

class Pawn(Figure):
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
        y1 = y + self.color
        for dx in (-1, 1, 0): #take moves first
            if board.hasColorAt((x + dx, y1), -self.color if dx else Color.none):
                if not dx and not self.hasMoved and board.isEmptyAt((x, y1 + self.color)):
                    yield from board.move((x,y), (x, y1 + self.color))
                for f in [Queen, Rock, Bishop, Knight] if isLastLine(y1) else [None]:
                    yield from board.move((x,y), (x + dx, y1), f)

class Rock(Figure):
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

class Knight(Figure):
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
                yield from board.move((x,y), xy1)

class Bishop(Figure):
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

class Queen(Figure):
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

class King(Figure):
    weights = hMirror([
        *([[-30, -40, -40, -50]] * 4),
        [-20, -30, -30, -40],
        [-10, -20, -20, -20],
        [ 20,  20,   0,   0],
        [ 20,  30,  10,   0]])
    baseCost = 99000
    name = "K"

    def canCastleTo(self, x, y, rockX, s):
        rock = board.cells[rockX, y]
        return (not self.hasMoved and isinstance(rock, Rock) and not rock.hasMoved
            and (all(board.isEmptyAt((x1, y)) for x1 in range(x + s, rockX, s))
            and all(not board.isUnderAttack((x + s * dx, y), -self.color) for dx in range(3))))

    def allMoves(self, board, x, y, recursion):
        for rockX, s in [(7,1), (0,-1)]:
            if not recursion and self.canCastleTo(x, y, rockX, s):
                yield from board.move((x,y), (x + 2*s, y), None, rockX)
        for xy1 in product(range(x-1, x+2), range(y-1, y+2)):
            if inRange(*xy1) and board.cells[xy1].color != self.color:
                if recursion or not board.isUnderAttack(xy1, -self.color):
                    yield from board.move((x,y), xy1)

class Board:
    def __init__(self):
        self.cells = {xy: Figure() for xy in product(range(8), repeat=2)}
        for color, y in [(Color.white, 0), (Color.black, 7)]:
            for x in range(8):
                self.cells[x, y+color] = Pawn(color)
            for x, f in enumerate((Rock, Knight, Bishop, Queen)):
                self.cells[x, y] = f(color)
                self.cells[7-x, y] = f(color)
            self.cells[4, y] = King(color)
        self.score = 0

    def hasColorAt(self, xy, color):
        return inRange(*xy) and self.cells[xy].color == color

    def isEmptyAt(self, xy): return self.hasColorAt(xy, Color.none)

    def move(self, src, dst, newDst = None, rockX = None):
        try:
            oldScore = self.score
            figureFrom, figureTo = self.moveFigure(src, dst, newDst)
            hasMoved, figureFrom.hasMoved = figureFrom.hasMoved, True
            if rockX:
                rockDst = {7:5, 0:3}[rockX], dst[1]
                self.moveFigure((rockX, src[1]), rockDst)
            yield self, [src, dst]
        finally:
            self.cells[src], self.cells[dst] = figureFrom, figureTo
            figureFrom.hasMoved = hasMoved
            if rockX:
                self.moveFigure(rockDst, (rockX, dst[1]))
            self.score = oldScore

    def moveFigure(self, src, dst, promotion = None):
            figureFrom, figureTo = self.cells[src], self.cells[dst]
            self.score -= figureFrom.cost(*src) + figureTo.cost(*dst)
            c = self.cells[dst] = promotion(figureFrom.color) if promotion else figureFrom
            self.score += c.cost(*dst)
            self.cells[src] = Figure()
            return figureFrom, figureTo

    def print(self):
        help = {0: "R - rock", 1: "N - knight", 2: "B - bishop", 3: "Q - queen",
                4: "K - king", 5: "P - pawn", 6: "", 7: ""}
        textColors = {Color.black: '\033[95m', Color.none: "\033[92m", Color.white: "\033[93m"}
        whiteText = "\033[37m"
        for y,x in sorted(self.cells):
            figure = self.cells[x, 7-y]
            print(f"{textColors[figure.color]}{figure.name} ",
                  end="" if x < 7 else f"{whiteText} |{8-y}   {help[y]}\n")
        print("-" * 16)
        print("A B C D E F G H")

    def allMoves(self, color, recursion = False):
        for xy, cell in self.cells.items():
            if cell.color == color:
                yield from cell.allMoves(self, *xy, recursion)

    def doMinimax(self, color, maxDepth, depth = 1, alphaBeta = None):
        bestScore = None
        for board, move in self.allMoves(color):
            score = (self.doMinimax(-color, maxDepth, depth+1, bestScore) if depth < maxDepth
                else board.score)
            if not bestScore or color*score > color*bestScore:
                bestScore = score
                if depth == 1:
                    newBoard = copy.deepcopy(board)
                    newBoard.lastMove = move
            if alphaBeta and color*score > color*alphaBeta:
                break
        return newBoard if depth == 1 else bestScore

    def isUnderAttack(self, xy, color):
        return any(move[1] == xy for _, move in self.allMoves(color, True))

    def isCheck(self, color):
        for xy, cell in self.cells.items():
            if cell.color == color and isinstance(cell, King):
                return self.isUnderAttack(xy, -color)

    def isCheckmate(self, color, check = True):
        return (self.isCheck(color) == check and
            all(board.isCheck(color) for board, _ in self.allMoves(color)))

    def isStalemate(self, color): return self.isCheckmate(color, False)

def inputUserMove(color, board):
    while True:
        try:
            moveStr = input("Your move? ").lower().split("-")
            move = [tuple(ord(a) - ord(b) for a, b in zip(m, "a1")) for m in moveStr]
            figure = board.cells[move[0]]
            if (figure.color == color and any(move == m and not board.isCheck(color)
                for _, m in figure.allMoves(board, *move[0], False))):
                break
            print("Invalid move.")
        except:
            print("invalid move format. Move example: e2-e4")
    while isinstance(figure, Pawn) and isLastLine(move[1][1]):
        prompt = input("Promote to (Q/R/B/N)? ").upper()
        for f in [Queen, Rock, Bishop, Knight]:
            if f.name == prompt: return *move, f
    return *move, None

board = Board()
board.print()
userColor = input("Would you like to play white? (y/n)")
userColor = Color.white if userColor.lower() == "y" else Color.black
player = Color.white
while not (board.isCheckmate(player) or board.isStalemate(player)):
    if player != userColor:
        t0 = time.time()
        board = board.doMinimax(player, 4)
        move = '-'.join(chr(ord("a") + m[0]) + str(m[1] + 1) for m in board.lastMove)
        print(f"Time: {round(time.time()-t0, 1)} secs. Move: {move}")
    else:
        src, dst, promotion = inputUserMove(userColor, board)
        figure, _ = board.moveFigure(src, dst, promotion)
        figure.hasMoved = True
        dx = dst[0] - src[0]
        if isinstance(figure, King) and abs(dx) == 2: # Castle move by user, move rock
            board.moveFigure(({2:7, -2:0}[dx], src[1]), ({2:5, -2:3}[dx], src[1]))
    board.print()
    player = -player
if board.isStalemate(player):
    print("Stalemate. Draw.")
else:
    print("White" if board.isCheckmate(Color.black) else "Black", "win.")
