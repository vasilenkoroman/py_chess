from itertools import product
import copy, time

sign = lambda x: 1 if x > 0 else -1
inRange = lambda x, y: 0 <= y < 8 and 0 <= x < 8
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
        x1, y1 = x + dx, y + dy
        while inRange(x1, y1):
            color = board.cells[x1,y1].color
            if color != self.color:
                yield from board.move((x, y), (x1, y1))
            if color != Color.none:
                break
            x1, y1 = x1 + dx, y1 + dy

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

    def allMoves(self, board, x, y, opaque):
        y1 = y + self.color
        for dx in (-1, 1, 0): #take moves first
            if board.hasColorAt(x + dx, y1, Color.none if dx == 0 else -self.color):
                if dx == 0 and not self.hasMoved and board.isEmptyAt(x, y1 + self.color):
                    yield from board.move((x, y), (x, y1 + self.color))
                for f in [Queen, Rock, Bishop, Knight] if isLastLine(y1) else [None]:
                    yield from board.move((x, y), (x + dx, y1), f)

class Rock(Figure):
    weights = hMirror([
        [0] * 4,
        [5, 10, 10, 10],
        *([[-5, 0, 0, 0]] * 5),
        [0, 0, 0, 5]])
    baseCost = 500
    name =  "R"

    def allMoves(self, board, x, y, opaque):
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            yield from self.doSequenceMoves(board, x, y, dx, dy)

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

    def allMoves(self, board, x, y, opaque):
        for dx, dy in [(2, -1), (2, 1), (-2, -1), (-2, 1), (1, -2), (1, 2), (-1, -2), (-1, 2)]:
            xy1 = x + dx, y + dy
            if inRange(*xy1) and board.cells[xy1].color != self.color:
                yield from board.move((x, y), xy1)

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

    def allMoves(self, board, x, y, opaque):
        for dx, dy in product((-1, 1), repeat=2):
            yield from self.doSequenceMoves(board, x, y, dx, dy)

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

    def allMoves(self, board, x, y, opaque):
        for dx, dy in product(range(-1,2), repeat=2):
            yield from self.doSequenceMoves(board, x, y, dx, dy)

class King(Figure):
    weights = hMirror([
        *([[-30, -40, -40, -50]] * 4),
        [-20, -30, -30, -40],
        [-10, -20, -20, -20],
        [ 20,  20,   0,   0],
        [ 20,  30,  10,   0]])
    baseCost = 99000
    name = "K"

    def canCastleTo(self, x, y, rockX):
        rock = board.cells[rockX,y]
        s = sign(rockX - 1)
        return (not self.hasMoved and isinstance(rock, Rock) and not rock.hasMoved
            and (all(board.isEmptyAt(x1, y) for x1 in range(x + s, rockX, s))
            and all(not board.isUnderAttack(x + s * dx, y, -self.color) for dx in range(3))))

    def allMoves(self, board, x, y, recursion):
        for kingX, rockX in [(6,7), (2,0)]:
            if not recursion and self.canCastleTo(x, y, rockX):
                yield from board.move((x, y), (kingX, y), None, rockX)
        for dx, dy in product(range(-1,2), repeat=2):
            xy1 = x + dx, y + dy
            if inRange(*xy1) and board.cells[xy1].color != self.color:
                if recursion or not board.isUnderAttack(*xy1, -self.color):
                    yield from board.move((x, y), xy1)

class ChessBoard:
    def __init__(self):
        self.cells = {}
        for xy in product(range(8), repeat=2):
            self.cells[xy] = Figure()
        for color, y in [(Color.white, 0), (Color.black, 7)]:
            for x in range(8):
                self.cells[x, y + color] = Pawn(color)
            for x, f in enumerate((Rock, Knight, Bishop, Queen)):
                self.cells[x,y] = f(color)
                self.cells[7-x,y] = f(color)
            self.cells[4,y] = King(color)
        self.score = 0

    def hasColorAt(self, x, y, color):
        return inRange(x, y) and self.cells[x,y].color == color

    def isEmptyAt(self, x, y): return self.hasColorAt(x, y, Color.none)

    def isValidMove(self, src, dst, color):
        return (self.hasColorAt(*src, color) and
            any(move[1] == dst and not board.isKingUnderAttack(color)
            for _, move in self.cells[tuple(src)].allMoves(self, *src, False)))

    def move(self, src, dst, newDst = None, rockX = None):
        try:
            oldScore = self.score
            figureFrom, figureTo = self.moveFigure(src, dst, newDst)
            hasMoved, figureFrom.hasMoved = figureFrom.hasMoved, True
            if rockX:
                rockDstX = {7:5, 0:3}[rockX]
                self.moveFigure((rockX, src[1]), (rockDstX, dst[1]))
            yield self, [src, dst]
        finally:
            self.cells[src] = figureFrom
            self.cells[dst] = figureTo
            figureFrom.hasMoved = hasMoved
            if rockX:
                self.moveFigure((rockDstX, src[1]), (rockX, dst[1]))
            self.score = oldScore

    def moveFigure(self, src, dst, promotion = None):
            figureTo = self.cells[dst]
            figureFrom = self.cells[src]
            self.score -= figureTo.cost(*dst) + figureFrom.cost(*src)
            self.cells[dst] = promotion(figureFrom.color) if promotion else figureFrom
            self.score += self.cells[dst].cost(*dst)
            self.cells[src] = Figure()
            return figureFrom, figureTo

    def print(self):
        help = {0: "R - rock", 1: "N - knight", 2: "B - bishop", 3: "Q - queen",
                4: "K - king", 5: "P - pawn", 6: "", 7: ""}
        textColors = {Color.black: '\033[95m', Color.none: "\033[92m", Color.white: "\033[93m"}
        whiteText = "\033[37m"
        for y,x in sorted(self.cells):
            figure = self.cells[x, 7-y]
            print(f"{textColors[figure.color]}{figure.name} ", end="")
            if x == 7:
                print(f"{whiteText} |{8-y}   {help[y]}")
        print("-" * 16)
        print("A B C D E F G H")

    def isUnderAttack(self, x, y, color):
        return any(move[1] == [x, y] for _, move in self.allMoves(color, True))

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

    def isCheckmate(self, color, check = True):
        return (self.isKingUnderAttack(color) == check and
            all(board.isKingUnderAttack(color) for board, _ in self.allMoves(color)))

    def isStalemate(self, color): return self.isCheckmate(color, False)

    def isKingUnderAttack(self, color):
        return self.isUnderAttack(*self.findKing(color)[:2], -color)

    def findKing(self, color):
        for x, y in product(range(8), repeat=2):
            king = board.cells[x,y]
            if king.color == color and isinstance(king, King):
                return x, y, king

def inputUserMove(color):
    while True:
        try:
            moveStr = input("Your move? ").lower().split("-")
            move = [tuple(ord(a) - ord(b) for a, b in zip(m, "a1")) for m in moveStr]
            if board.isValidMove(*move, color):
                break
            print("Invalid move.")
        except:
            print("invalid move format. Move example: e2-e4")
    figure = board.cells[tuple(move[0])]
    while isinstance(figure, Pawn) and isLastLine(move[1][1]):
        prompt = input("Promote to (Q/R/B/N)? ").upper()
        for f in [Queen, Rock, Bishop, Knight]:
            if f.name == prompt: return *move, f
    return *move, None

board = ChessBoard()
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
        src, dst, promotion = inputUserMove(userColor)
        x, y, dx = *src, dst[0] - src[0]
        figure, _ = board.moveFigure(src, dst, promotion)
        figure.hasMoved = True
        if isinstance(figure, King) and abs(dx) == 2: # Castle move by user, move rock
            board.moveFigure(({2:7, -2:0}[dx], y), (x - sign(dx), y))
    board.print()
    player = -player
if board.isStalemate(player):
    print("Stalemate. Draw.")
else:
    print("White" if board.isCheckmate(Color.black) else "Black", "win.")
