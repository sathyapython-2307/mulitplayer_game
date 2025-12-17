import random

class ChessBot:
    """Simple chess bot that makes random valid moves"""
    
    @staticmethod
    def get_valid_moves(board_state, color):
        """Get all valid moves for a color"""
        moves = []
        for pos, piece in board_state.items():
            if piece and piece[0] == color[0]:
                piece_moves = ChessBot.get_piece_moves(pos, piece, board_state)
                moves.extend([(pos, target) for target in piece_moves])
        return moves
    
    @staticmethod
    def get_piece_moves(pos, piece, board_state):
        """Get valid moves for a piece at position"""
        moves = []
        col, row = pos[0], int(pos[1])
        piece_type = piece[1]
        color = piece[0]
        
        if piece_type == 'p':  # Pawn
            direction = 1 if color == 'w' else -1
            new_row = row + direction
            if 1 <= new_row <= 8:
                forward = f"{col}{new_row}"
                if forward not in board_state:
                    moves.append(forward)
        
        elif piece_type == 'n':  # Knight
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            for dc, dr in knight_moves:
                new_col = chr(ord(col) + dc)
                new_row = row + dr
                if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                    target = f"{new_col}{new_row}"
                    if target not in board_state or board_state[target][0] != color:
                        moves.append(target)
        
        elif piece_type == 'r':  # Rook
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, color))
        
        elif piece_type == 'b':  # Bishop
            for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, color))
        
        elif piece_type == 'q':  # Queen
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, color))
        
        elif piece_type == 'k':  # King
            for dc in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if dc == 0 and dr == 0:
                        continue
                    new_col = chr(ord(col) + dc)
                    new_row = row + dr
                    if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                        target = f"{new_col}{new_row}"
                        if target not in board_state or board_state[target][0] != color:
                            moves.append(target)
        
        return moves
    
    @staticmethod
    def get_line_moves(pos, direction, board_state, color):
        """Get moves in a line (for rook, bishop, queen)"""
        moves = []
        col, row = pos[0], int(pos[1])
        dc, dr = direction
        
        for i in range(1, 8):
            new_col = chr(ord(col) + dc * i)
            new_row = row + dr * i
            if not ('a' <= new_col <= 'h' and 1 <= new_row <= 8):
                break
            target = f"{new_col}{new_row}"
            if target in board_state:
                if board_state[target][0] != color:
                    moves.append(target)
                break
            moves.append(target)
        
        return moves
    
    @staticmethod
    def make_move(board_state, color):
        """Make a random valid move"""
        valid_moves = ChessBot.get_valid_moves(board_state, color)
        if not valid_moves:
            return None
        
        # Prioritize captures
        captures = [(from_pos, to_pos) for from_pos, to_pos in valid_moves if to_pos in board_state]
        if captures:
            return random.choice(captures)
        
        return random.choice(valid_moves)
