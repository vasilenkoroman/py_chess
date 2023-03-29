from copy import deepcopy
import time

class FigureColor:
    blackFigure = '\033[95m'
    whiteFigure = '\033[93m'
    emptyCell = '\033[92m'
    white = '\033[37m'

class Color:
    none = 0
    black = 1
    white = 2

    def oppositeColor(color):
        return Color.white if color == Color.black else Color.black

class Figure:
    weights = [[0] * 8] * 8
    baseCost = 0

    def __init__(self, color = Color.none):
        self.color = color
        self.hasMoved = False

    def getWeight(self, y, x):
        return self.weights[7-y][x] if self.color == Color.white else -self.weights[y][7 - x]

    def name(self):
        return "*"

    def cost(self):
        return self.baseCost if self.color == Color.white else -self.baseCost

    def oppositeColor(self):
        return Color.oppositeColor(self.color)

    def possibleMoves(self, board, y, x, checkAttack):
        if False:
            yield board

    def doSequenceMoves(self, board, y, x, yDelta, xDelta):
         newY, newX = y + yDelta, x + xDelta
         while ChessBoard.inRange(newY, newX):
            color = board.cells[newY][newX].color
            if color == self.color:
                break # own figure
            yield from board.move(y, x, newY, newX)
            if color != Color.none:
                break # Eat figure
            newY += yDelta
            newX += xDelta

class Pawn(Figure):
    weights = [
        [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
        [0.5,  0.5,  0.5,  0.5,  0.5,  0.5,  0.5,  0.5],
        [0.1,  0.1,  0.2,  0.3,  0.3,  0.2,  0.1,  0.1],
        [0.05, 0.05, 0.1,  0.25, 0.25, 0.1,  0.05, 0.05],
        [0.0,  0.0,  0.0,  0.20, 0.20, 0.0,  0.0,  0.0],
        [0.05,-0.05,-0.1,  0.0,  0.0, -0.1, -0.05, 0.05],
        [0.05, 0.1,  0.1, -0.02,-0.02, 0.1,  0.1,  0.05],
        [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0]]
    baseCost = 1

    def name(self):
        return "P"

    def possibleMoves(self, board, y, x, checkAttack):
        color = self.color
        yDirection = 1 if color == Color.white else -1
        initPos = 1 if color == Color.white else 6
        needPromote = y + yDirection == 7 or y + yDirection == 0
        for xDelta in [-1, 1, 0]: #take moves first
            dstColor = Color.none if xDelta == 0 else self.oppositeColor()
            if board.hasColorAt(y + yDirection, x + xDelta, dstColor):
                if needPromote:
                    for figure in [Queen(color), Rock(color), Bishop(color), Knight(color)]:
                        yield from board.move(y, x, y + yDirection, x + xDelta, figure)
                else:
                    yield from board.move(y, x, y + yDirection, x + xDelta)
        if y == initPos and board.isEmptyAt(y + yDirection, x) and board.isEmptyAt(y + yDirection * 2, x):
            yield from board.move(y, x, y + yDirection * 2, x)

class Rock(Figure):
    weights = [
        [ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
        [ 0.05, 0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.05],
        [-0.05, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.05],
        [-0.05, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.05],
        [-0.05, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.05],
        [-0.05, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.05],
        [-0.05, 0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.05],
        [ 0.0,  0.0,  0.0,  0.05, 0.05, 0.0,  0.0,  0.0]]
    baseCost = 5

    def name(self):
        return "R"

    def possibleMoves(self, board, y, x, checkAttack):
        for direction in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            yield from self.doSequenceMoves(board, y, x, *direction)

class Knight(Figure):
    weights = [
        [-0.5, -0.1,  -0.3,  -0.3,  -0.3, -0.3, -0.1,  -0.5],
        [-0.4, -0.2,  -0.0,  -0.0,   0.0,  0.0, -0.2,  -0.4],
        [-0.3,  0.0,   0.1,   0.15,  0.15, 0.1,  0.0,  -0.3],
        [-0.3,  0.05,  0.15,  0.20,  0.20, 0.15, 0.05, -0.3],
        [-0.3,  0.00,  0.15,  0.20,  0.20, 0.15, 0.00, -0.3],
        [-0.3,  0.05,  0.10,  0.15,  0.15, 0.10, 0.05, -0.3],
        [-0.4, -0.2,   0.0,   0.05,  0.05, 0.0, -0.2,  -0.4],
        [-0.5, -0.1,  -0.3,  -0.3,  -0.3, -0.3, -0.1,  -0.5]]
    baseCost = 3
    deltas = [(2, -1), (2, 1), (-2, -1), (-2, 1), (1, -2), (1, 2), (-1, -2), (-1, 2)]

    def name(self):
        return "N"

    def possibleMoves(self, board, y, x, checkAttack):
        for dy, dx in Knight.deltas:
            y1, x1 = y + dy, x + dx
            if ChessBoard.inRange(y1, x1) and board.cells[y1][x1] != self.color:
                yield from board.move(y, x, y1, x1)

class Bishop(Figure):
    weights = [
        [-0.2, -0.1,  -0.1,  -0.1,  -0.1, -0.1, -0.1,  -0.2],
        [-0.1,  0.0,   0.0,   0.0,   0.0,  0.0,  0.0,  -0.1],
        [-0.1,  0.0,   0.05,  0.1,   0.1,  0.05, 0.0,  -0.1],
        [-0.1,  0.05,  0.05,  0.1,   0.1,  0.05, 0.05, -0.1],
        [-0.1,  0.0,   0.1,   0.1,   0.1,  0.1,  0.0,  -0.1],
        [-0.1,  0.1,   0.1,   0.1,   0.1,  0.1,  0.1,  -0.1],
        [-0.1,  0.05,  0.0,   0.0,   0.0,  0.0,  0.05, -0.1],
        [-0.2, -0.1,  -0.1,  -0.1,  -0.1, -0.1, -0.1,  -0.2]]
    baseCost = 3.1

    def name(self):
        return "B"

    def possibleMoves(self, board, y, x, checkAttack):
        for direction in [(1, 1), (1, -1), (-1, -1), (-1, 1)]:
            yield from self.doSequenceMoves(board, y, x, *direction)

class Queen(Figure):
    weights = [
        [-0.2, -0.1,  -0.1,  -0.05,  -0.05, -0.1,  -0.1,  -0.2],
        [-0.1,  0.0,   0.0,   0.00,   0.0,   0.0,   0.0,  -0.1],
        [-0.1,  0.0,   0.05,  0.05,   0.05,  0.05,  0.0,  -0.1],
        [-0.05, 0.0,   0.05,  0.05,   0.05,  0.05,  0.0,  -0.05],
        [ 0.0,  0.0,   0.05,  0.05,   0.05,  0.05,  0.0,  -0.05],
        [-0.1,  0.05,  0.05,  0.05,   0.05,  0.05,  0.05, -0.1],
        [-0.1,  0.0,   0.05,  0.0,    0.0,   0.0,   0.0,  -0.1],
        [-0.2, -0.1,  -0.1,  -0.05,  -0.05, -0.1,  -0.1,  -0.2]]
    baseCost = 9

    def name(self):
        return "Q"

    def possibleMoves(self, board, y, x, checkAttack):
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                yield from self.doSequenceMoves(board, y, x, dy, dx)

class King(Figure):
    weights = [
        [-0.3, -0.4, -0.4, -0.5, -0.5, -4.0, -4.0, -3.0],
        [-0.3, -0.4, -0.4, -0.5, -0.5, -4.0, -4.0, -3.0],
        [-0.3, -0.4, -0.4, -0.5, -0.5, -4.0, -4.0, -3.0],
        [-0.3, -0.4, -0.4, -0.5, -0.5, -4.0, -4.0, -3.0],
        [-0.2, -0.3, -0.3, -0.4, -0.4, -3.0, -3.0, -2.0],
        [-0.1, -0.2, -0.2, -0.2, -0.2, -2.0, -2.0, -1.0],
        [ 0.2,  0.2,  0.0,  0.0,  0.0,  0.0,  0.2,  0.2],
        [ 0.2,  0.3,  0.1,  0.0,  0.0,  0.1,  0.3,  0.2]]
    baseCost = 1000

    def name(self):
        return "K"

    def canCastleTo(self, y, x, rockX):
        rock = board.cells[y][rockX]
        if self.hasMoved or not isinstance(rock, Rock) or rock.hasMoved:
            return False
        sign = 1 if rockX > x else -1
        color = self.oppositeColor()
        return all(board.isEmptyAt(y, x2) for x2 in range(x + sign, rockX, sign))\
            and all(not board.isUnderAttack(y, x2, color) for x2 in range(x, x + 3 * sign, sign))

    def possibleMoves(self, board, y, x, checkAttack):
        for x1 in [0, 7]:
            if checkAttack and self.canCastleTo(y, x, x1):
                yield from board.castleMove(y, x, x1)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if ChessBoard.inRange(y + dy, x + dx):
                    if board.cells[y + dy][x + dx].color == self.color:
                        continue # own figure
                    if not checkAttack or not board.isUnderAttack(y + dy, x + dx, self.oppositeColor()):
                        yield from board.move(y, x, y + dy, x + dx)

class ChessBoard:
    def __init__(self):
        self.cells = [[Figure()] * 8 for y in range(8)]
        for x in range(8):
            self.cells[1][x] = Pawn(Color.white)
            self.cells[6][x] = Pawn(Color.black)
        for color in [Color.white, Color.black]:
            y = 0 if color == Color.white else 7
            for x, f in enumerate((Rock, Knight, Bishop)):
                self.cells[y][x] = f(color)
                self.cells[y][7-x] = f(color)
            self.cells[y][3] = Queen(color)
            self.cells[y][4] = King(color)
        self.score = 0

    def isEmptyAt(self, y, x):
        return self.hasColorAt(y, x, Color.none)

    def inRange(y, x):
        return 0 <= y < 8 and 0 <= x < 8

    def hasColorAt(self, y, x, color):
        return ChessBoard.inRange(y, x) and self.cells[y][x].color == color

    def isValidMove(self, moveFrom, moveTo, color):
        figure = self.cells[moveFrom[0]][moveFrom[1]]
        if figure.color == color:
            for newBoard, lastMove in figure.possibleMoves(self, *moveFrom, True):
                if lastMove[1] == moveTo and not self.isKingUnderAttack(color):
                    return True
        return False

    def move(self, fromY, fromX, toY, toX, newDst = None):
        try:
            oldScore = self.score
            figureTo = self.cells[toY][toX]
            figureFrom = self.cells[fromY][fromX]
            hasMoved = figureFrom.hasMoved
            self.moveFigure(fromY, fromX, toY, toX, newDst)
            yield self, [[fromY, fromX],[toY, toX]]
        finally:
            self.cells[fromY][fromX] = figureFrom
            self.cells[toY][toX] = figureTo
            figureFrom.hasMoved = hasMoved
            self.score = oldScore

    def castleMove(self, y, x, rockX):
        try:
            oldScore = self.score
            direction = 1 if rockX == 7 else -1
            king = self.cells[y][x]
            rock = self.cells[y][rockX]
            self.moveFigure(y, x, y, x + direction * 2)
            self.moveFigure(y, rockX, y, x + direction)
            yield self, [[y, x],[y, x + direction * 2]]
        finally:
            self.cells[y][x + direction * 2] = self.cells[y][x + direction] = Figure()
            self.cells[y][x] = king
            self.cells[y][rockX] = rock
            self.score = oldScore
            king.hasMoved = rock.hasMoved = False

    def moveFigure(self, fromY, fromX, toY, toX, promotion = None):
            figureTo = self.cells[toY][toX]
            figureFrom = self.cells[fromY][fromX]
            self.score -= figureTo.getWeight(toY, toX) + figureTo.cost()
            self.score -= figureFrom.getWeight(fromY, fromX)
            if promotion != None:
                self.score += promotion.cost() - figureFrom.cost()
                figureFrom = promotion
            self.score += figureFrom.getWeight(toY, toX)
            self.cells[toY][toX] = figureFrom
            self.cells[fromY][fromX] = Figure()
            figureFrom.hasMoved = True

    def print(self):
        help = {0: "R - rock", 1: "N - knight", 2: "B - bishop", 3: "Q - queen",
                4: "K - king", 5: "P - pawn", 6: "", 7: ""}
        for y, row in enumerate(reversed(self.cells)):
            for figure in row:
                color = FigureColor.emptyCell
                if figure.color == Color.white:
                    color = FigureColor.whiteFigure
                elif figure.color == Color.black:
                    color = FigureColor.blackFigure
                print("" + color + figure.name() + " ", end="")
            print(FigureColor.white + " |", 8 - y, "   ", help[y])
        print("-" * 16)
        print("A B C D E F G H")

    def isUnderAttack(self, y, x, color):
        return any(move[1] == [y,x] for _, move in self.possibleMoves(color, False))

    def possibleMoves(self, color, checkAttack = True):
        for y, row in enumerate(self.cells):
            for x, figure in enumerate(row):
                if figure.color == color:
                    yield from figure.possibleMoves(self, y, x, checkAttack)

    def doMinimax(self, color, maxDepth, depth = 1, alphaBeta = None):
        bestScore = None
        newBoard = None
        compare = lambda c, s, l: c == Color.white and s > l or c == Color.black and s < l
        for board, lastMove in self.possibleMoves(color):
            score = board.score if depth == maxDepth \
                else self.doMinimax(Color.oppositeColor(color), maxDepth, depth + 1, bestScore)
            if bestScore == None or compare(color, score, bestScore):
                bestScore = score
                if depth == 1:
                    newBoard = deepcopy(board)
                    newBoard.lastMove = lastMove
            if alphaBeta != None and compare(color, score, alphaBeta):
                break
        return newBoard if depth == 1 else bestScore

    def isCheckmate(self, color):
        y, x, king = self.findKing(color)
        isUnderAttack = self.isUnderAttack(y, x, Color.oppositeColor(color))
        return isUnderAttack and len(list(king.possibleMoves(self, y, x))) == 0

    def isKingUnderAttack(self, color):
        y, x, king = self.findKing(color)
        return self.isUnderAttack(y, x, Color.oppositeColor(color))

    def findKing(self, color):
        for y, row in enumerate(self.cells):
            for x, figure in enumerate(row):
                if figure.color == color and isinstance(figure, King):
                    return y, x, figure
        return None

def toString(move):
    return chr(ord("a") + move[1]) + chr(move[0] + ord("1"))

def inputUserMove(userColor):
    while True:
        moveStr = input("Your move? ").lower().split("-")
        if len(moveStr) != 2 or len(moveStr[0]) != 2 or len(moveStr[1]) != 2:
            print("invalid move format. Move example: e2-e4")
            continue
        move = []
        for m in moveStr:
            x = ord(m[0]) - ord("a")
            y = ord(m[1]) - ord("1")
            if ChessBoard.inRange(y, x):
                move.append([y,x])
        if len(move) != 2 or not board.isValidMove(*move, userColor):
            print("Invalid move.")
            continue
        promotion = None
        figure = board.cells[move[0][0]][move[0][1]]
        toY = move[1][0]
        if isinstance(figure, Pawn) and (toY == 7 or toY == 0):
            prompt = input("Promote to (Q/R/B/N)? ")
            for f in [Queen(figure.color), Rock(figure.color), Bishop(figure.color), Knight(figure.color)]:
                if f.name == prompt:
                    promotion = f
        return move, promotion

board = ChessBoard()
board.print()
userColor = input("Would you like to play white? (y/n)")
userColor = Color.white if userColor.lower() == "y" else Color.black
#main game loop
currentColor = Color.white
while True:
    if currentColor != userColor:
        start_time = time.time()
        board = board.doMinimax(currentColor, 4)
        print("Time to think ", round(time.time()-start_time, 1), "secs. Move:", \
          toString(board.lastMove[0]) + '-' + toString(board.lastMove[1]))
        if board == None:
            print("Stalemate. Draw.")
            break
    else:
        move, promotion = inputUserMove(userColor)
        board.moveFigure(*move[0], *move[1], promotion)
        y, x, king = board.findKing(currentColor)
        dx = move[1][1] - move[0][1]
        if move[1] == [y, x] and abs(dx) == 2:
            # Castle move by user, move rock as well.
            rockX = 7 if dx > 0 else 0
            newX = x - (1 if dx > 0 else -1)
            board.moveFigure(y, rockX, y, newX)

    board.print()
    if board.isCheckmate(Color.black):
        print("White win.")
        break
    elif board.isCheckmate(Color.white):
        print ("black win.")
        break
    currentColor = Color.oppositeColor(currentColor)
