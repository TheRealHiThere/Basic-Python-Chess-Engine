# Storing all the information about the current state of the chess game. As well
# as determine the valid moves as well
# keeping take of the move logs


position = tuple[int, int]

class Move():
    # Map the keys to a value
    # key : value

    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                  "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}

    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}


    def __init__(self, 
            startSq: position, endSq: position, 
            board, 
            isEnpassantMove = False, 
            pawnPromotion = False,
            castle = False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]

        self.endRow = endSq[0]
        self.endCol = endSq[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]

        # Pawn Promotion
        self.isPawnPromotion = pawnPromotion
        if (self.pieceMoved == 'wp' and self.endRow == 0)or (self.pieceMoved == 'bp' and self.endRow == 7):
            self.isPawnPromotion = True

        # Enpassant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'

        # Castling
        self.castle = castle

        self.isCapture = self.pieceCaptured != '--'
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self) -> str:
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r: int, c: int) -> str:
        return self.colsToFiles[c] + self.rowsToRanks[r]

    # Overriding the string function
    def __str__(self):
        #Castle Move
        if self.castle:
            return "O-O" if self.endCol == 6 else "O-O-O"
        end_square = self.getRankFile(self.endRow, self.endCol)

        # Piece Moves
        move_string = self.pieceMoved[1]
        if self.isCapture:
            move_string += "x"
        return move_string + end_square
        return self.getChessNotation()

class GameState():
    def __init__(self):
        # Board is a 8x8 two dimensional plane

        # The plane has a list of characters the first character represents the color while the color 'b' or 'w'
        # While the secound character represents the type of the piece 'K' 'Q' 'B' 'N' 'R' or 'p'
        # "--" represents an empty space with no pieces
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        self.moveLog: list[Move] = []
        self.whiteToMove: bool = True

        # Keep track of the kings position
        self.white_king_to_move: position = (7,4)
        self.black_king_to_move: position = (0,4)

        # CheckMate and Stalemate Varuables
        self.checkmate: bool = False
        self.stalemate: bool = False

        # Enpassant
        self.enpassantPossible: list[Move] = []
        self.enpassantMoveLog = [self.enpassantPossible]

        #Castling Rights
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]


    def make_move(self, move: Move):
        self.moveLog.append(move) # log the move in order to undo it
        self.set_cell(move.startRow, move.startCol, '--') # Erase the piece from the board
        self.set_cell(move.endRow, move.endCol, move.pieceMoved) # Place the piece on the board

        # Keep track of the kings position
        if move.pieceMoved == 'wK':
            self.white_king_to_move = (move.endRow, move.endCol)
        if move.pieceMoved == 'bK':
            self.black_king_to_move = (move.endRow, move.endCol)

        # Pawn Promotion
        if move.isPawnPromotion:
            # promotedPiece = input("Promote to Q, R, B, or N:")
            self.set_cell(move.endRow, move.endCol, move.pieceMoved[0] + 'Q')

        # Enpassant
        if move.isEnpassantMove:
            self.set_cell(move.startRow, move.endCol, '--') # Erase the pawn from the board
        # Update enpassantPossible
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enpassantPossible = None

        # Castle Move
        if move.castle:
            if move.endCol - move.startCol == 2: # Kings side castle
                self.set_cell(move.endRow, move.endCol - 1, self.get_cell(move.endRow, move.endCol + 1))
                self.set_cell(move.endRow, move.endCol+1, '--')
            else: # Queen side castle
                self.set_cell(move.endRow, move.endCol + 1, self.get_cell(move.endRow, move.endCol - 2))
                self.set_cell(move.endRow, move.endCol - 2, '--')

        self.enpassantMoveLog.append(self.enpassantPossible)

        # Update Castling Rights
        self.update_castle_rights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                                 self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

        self.whiteToMove = not self.whiteToMove # Swap the players
        return True


    def undo_move(self):
        if len(self.moveLog) != 0: # Make sure there is a move to undo
            move = self.moveLog.pop()
            self.set_cell(move.startRow, move.startCol, move.pieceMoved)
            self.set_cell(move.endRow, move.endCol, move.pieceCaptured)
            self.whiteToMove = not self.whiteToMove

        # Keep track of the kings position
        if move.pieceMoved == 'wK':
            self.white_king_to_move = (move.startRow, move.startCol)
        if move.pieceMoved == 'bK':
            self.black_king_to_move = (move.startRow, move.startCol)

        #Undo enpassant
        if move.isEnpassantMove:
            self.set_cell(move.endRow, move.endCol, '--')
            self.set_cell(move.endRow, move.endCol, move.pieceCaptured)
        
        self.enpassantMoveLog.pop()
        self.enpassantPossible = self.enpassantMoveLog[-1]

        # Undo Castle Rights
        self.castleRightsLog.pop()
        newRights = self.castleRightsLog[-1]
        self.currentCastlingRight = CastleRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)

        # Undo the castle move
        if move.castle:
            if move.endCol - move.startCol == 2: # Kings side castle
                self.set_cell(move.endRow, move.endCol+1, self.get_cell(move.endRow, move.endCol-1))
                self.set_cell(move.endRow, move.endCol-1, '--')
            else: # Queen side castle
                self.set_cell(move.endRow, move.endCol-2, self.get_cell(move.endRow, move.endCol+1))
                self.set_cell(move.endRow, move.endCol+1, '--')

        # Undo checkmate and stalemate
        self.checkmate = False
        self.stalemate = False
        

    def update_castle_rights(self, move: Move):
        if move.pieceMoved == 'wk':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bk':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False

        # If a Rook is moved, update the castle rights
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.bks = False

        # If a rook is captured, then the castling rights are no longer valid
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False
        


    def valid_moves(self) -> list[Move]:
        # This handles Enpassant
        tempEnpasantPossible = self.enpassantPossible
        # Copy the current castling rights
        tempCastleRights = CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                        self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        moves = self.get_all_possible_moves()
        
        if self.whiteToMove:
            self.get_castle_moves(self.white_king_to_move, moves)
        else:
            self.get_castle_moves(self.black_king_to_move, moves)

        for i in range(len(moves)-1,-1,-1): # When removing from a list go backwards through it
            self.make_move(moves[i])

            #Generate all oppent's moves
            self.whiteToMove = not self.whiteToMove
            if self.in_check():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undo_move()

        if len(moves) == 0:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False
        
        self.enpassantPossible = tempEnpasantPossible
        self.currentCastlingRight = tempCastleRights
        return moves

    
    def in_check(self):
        return self.is_square_under_attack(self.white_king_to_move if self.whiteToMove else self.black_king_to_move)

    def is_square_under_attack(self, pos: position) -> bool:
        self.whiteToMove = not self.whiteToMove # switch the opponent's turn
        oppsMoves = self.get_all_possible_moves()
        self.whiteToMove = not self.whiteToMove # switch turns back

        for move in oppsMoves:
            if move.endRow == pos[0] and move.endCol == pos[1]: # The square is under attack
                return True
        return False 


    def get_all_possible_moves(self) -> list[Move]:
        moves: list[Move] = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]

                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    if piece == 'p':
                        self.get_pawn_moves(r, c, moves)
                    elif piece == 'R':
                        self.get_rook_moves(r, c, moves)
                    elif piece == 'N':
                        self.get_knight_moves(r, c, moves)
                    elif piece == 'B':
                        self.get_bishop_moves(r, c, moves)
                    elif piece == 'Q':
                        self.get_queen_moves(r, c, moves)
                    elif piece == 'K':
                        self.get_king_moves(r, c, moves)
                        
        return moves


    def get_pawn_moves(self, r, c, moves):
        if self.whiteToMove: #White Pawn move
            if self.board[r-1][c] == "--": # 1 Square pawn advance
                moves.append(Move((r, c), (r-1, c), self.board))
                if r == 6 and self.board[r-2][c] == "--":# 2 square pawn advance
                    moves.append(Move((r, c), (r-2, c), self.board))

            if c-1 > len(self.board[r][0]): # Capture to the left
                if self.board[r-1][c-1][0] == 'b': # enemy piece to capture
                    moves.append(Move((r, c), (r-1, c-1), self.board))
                # Enpassant Move
                elif (r-1, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c-1), self.board, isEnpassantMove=True))

            if c+1 < len(self.board[r]): # Capture to the right
                if self.board[r-1][c+1][0] == 'b': # enemy piece to capture
                    moves.append(Move((r, c), (r-1, c+1), self.board))
                # Enpassant Move
                elif (r-1, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c+1), self.board, isEnpassantMove=True))

        else: # Black to move
            if not self.whiteToMove:
                if self.board[r+1][c] == "--": # 1 Square pawn advance
                    moves.append(Move((r, c), (r+1, c), self.board))
                    if r == 1 and self.board[r+2][c] == "--":# 2 square pawn advance
                        moves.append(Move((r, c), (r+2, c), self.board))

                if c+1 > len(self.board[r][0]): # Capture to the left
                    if self.board[r+1][c-1][0] == 'w': # enemy piece to capture
                        moves.append(Move((r, c), (r+1, c-1), self.board))
                    # Enpassant Move
                    elif (r+1, c-1) == self.enpassantPossible:
                        moves.append(Move((r, c), (r+1, c-1), self.board, isEnpassantMove=True))

                if c+1 < len(self.board[r]): # Capture to the right
                    if self.board[r+1][c+1][0] == 'w': # enemy piece to capture
                        moves.append(Move((r, c), (r+1, c+1), self.board))
                    # Enpassant Move
                    elif (r+1, c+1) == self.enpassantPossible:
                        moves.append(Move((r, c), (r+1, c+1), self.board, isEnpassantMove=True))

    def get_rook_moves(self, r: int, c: int, moves: list[Move]):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'
            
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8: # on the board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor: # enemy piece is valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else: # friendly piece invalid
                        break
                else: # off board
                    break

    def get_knight_moves(self, r: int, c: int, moves: list[Move]):
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = 'w' if self.whiteToMove else 'b'

        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]

            if 0 <= endRow < 8 and 0 <= endCol < 8: # on the board
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: # not an ally piece (empty or enemy piece)
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    def get_bishop_moves(self, r: int, c: int, moves: list[Move]):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'

        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                
                if 0 <= endRow < 8 and 0 <= endCol < 8: # on the board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor: # enemy piece is valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else: # friendly piece invalid
                        break
                else: # off board
                    break

    def get_queen_moves(self, r: int, c: int, moves: list[Move]):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r: int, c: int, moves: list[Move]):
        kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        allyColor = 'w' if self.whiteToMove else 'b'

        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]

            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))


    def get_castle_moves(self, pos: position, moves: list[Move]):
        if self.is_square_under_attack(pos):
            return # Can't castle while in check

        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.get_king_side_castle(pos, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.get_queen_side_castle(pos, moves)

    
    def get_king_side_castle(self, pos: position, moves: list[Move]):
        r, c = pos
        if self.get_cell(r, c+1) == '--' and self.get_cell(r, c+2) == '--':
            if not self.is_square_under_attack((r, c+1)) and not self.is_square_under_attack((r, c+2)):
                moves.append(Move((r, c), (r, c+2), self.board, castle=True))


    def get_queen_side_castle(self, pos: position, moves: list[Move]):
        r, c = pos
        if self.get_cell(r, c-1) == '--' and self.get_cell(r, c-2) == '--' and self.get_cell(r, c-3) == '--':
            if not self.is_square_under_attack((r, c-1)) and not self.is_square_under_attack((r, c-2)):
                moves.append(Move((r, c), (r, c-2), self.board, castle=True))

    
    def get_cell(self, r: int, c: int) -> str | None:
        if r < 0 or r >= 8 or c < 0 or c >= 8:
            return None

        return self.board[r][c]

    def set_cell(self, r:int, c:int, piece:str) -> None:
        if r < 0 or r >= 8 or c < 0 or c >= 8:
            raise Exception("Can't set cell")

        self.board[r][c] = piece

class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.wqs = wqs

        self.bks = bks
        self.bqs = bqs


