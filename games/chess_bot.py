import random

class ChessBot:
    """Chess bot with proper move validation including king safety"""
    
    @staticmethod
    def get_valid_moves(board_state, color):
        """Get all valid moves for a color (filtered for legality)"""
        moves = []
        for pos, piece in board_state.items():
            if piece and piece[0] == color[0]:
                piece_moves = ChessBot.get_piece_moves(pos, piece, board_state, color)
                moves.extend([(pos, target) for target in piece_moves])
        
        # Filter out moves that would leave king in check
        legal_moves = []
        for from_pos, to_pos in moves:
            if ChessBot.is_move_legal(board_state, from_pos, to_pos, color):
                legal_moves.append((from_pos, to_pos))
        
        return legal_moves
    
    @staticmethod
    def is_move_legal(board_state, from_pos, to_pos, color):
        """Check if a move is legal (doesn't leave king in check)"""
        # Simulate the move
        test_board = dict(board_state)
        piece = test_board[from_pos]
        test_board[to_pos] = piece
        del test_board[from_pos]
        
        # Find king position after move
        king_pos = None
        king_piece = f"{color[0]}k"
        for pos, p in test_board.items():
            if p == king_piece:
                king_pos = pos
                break
        
        if not king_pos:
            return False
        
        # Check if king is under attack
        opponent_color = 'white' if color == 'black' else 'black'
        return not ChessBot.is_square_attacked(test_board, king_pos, opponent_color)
    
    @staticmethod
    def is_square_attacked(board_state, square, by_color):
        """Check if a square is attacked by any piece of the given color"""
        col, row = square[0], int(square[1])
        
        # Check for pawn attacks
        pawn_dir = -1 if by_color == 'white' else 1
        for dc in [-1, 1]:
            attack_col = chr(ord(col) + dc)
            attack_row = row + pawn_dir
            if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                attack_pos = f"{attack_col}{attack_row}"
                if attack_pos in board_state:
                    piece = board_state[attack_pos]
                    if piece == f"{by_color[0]}p":
                        return True
        
        # Check for knight attacks
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        for dc, dr in knight_moves:
            attack_col = chr(ord(col) + dc)
            attack_row = row + dr
            if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                attack_pos = f"{attack_col}{attack_row}"
                if attack_pos in board_state:
                    piece = board_state[attack_pos]
                    if piece == f"{by_color[0]}n":
                        return True
        
        # Check for king attacks (adjacent squares)
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                attack_col = chr(ord(col) + dc)
                attack_row = row + dr
                if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                    attack_pos = f"{attack_col}{attack_row}"
                    if attack_pos in board_state:
                        piece = board_state[attack_pos]
                        if piece == f"{by_color[0]}k":
                            return True
        
        # Check for sliding piece attacks (rook, bishop, queen)
        # Rook/Queen directions (horizontal/vertical)
        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if ChessBot.check_sliding_attack(board_state, square, direction, by_color, ['r', 'q']):
                return True
        
        # Bishop/Queen directions (diagonal)
        for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            if ChessBot.check_sliding_attack(board_state, square, direction, by_color, ['b', 'q']):
                return True
        
        return False
    
    @staticmethod
    def check_sliding_attack(board_state, square, direction, by_color, piece_types):
        """Check if square is attacked by sliding pieces in a direction"""
        col, row = square[0], int(square[1])
        dc, dr = direction
        
        for i in range(1, 8):
            new_col = chr(ord(col) + dc * i)
            new_row = row + dr * i
            if not ('a' <= new_col <= 'h' and 1 <= new_row <= 8):
                break
            
            check_pos = f"{new_col}{new_row}"
            if check_pos in board_state:
                piece = board_state[check_pos]
                if piece[0] == by_color[0] and piece[1] in piece_types:
                    return True
                break  # Blocked by any piece
        
        return False
    
    @staticmethod
    def get_piece_moves(pos, piece, board_state, color):
        """Get valid moves for a piece at position (pseudo-legal, needs king check)"""
        moves = []
        col, row = pos[0], int(pos[1])
        piece_type = piece[1]
        piece_color = piece[0]
        
        if piece_type == 'p':  # Pawn
            direction = 1 if piece_color == 'w' else -1
            
            # Forward move
            new_row = row + direction
            if 1 <= new_row <= 8:
                forward = f"{col}{new_row}"
                if forward not in board_state:
                    moves.append(forward)
                    
                    # Double move from starting position
                    if (piece_color == 'w' and row == 2) or (piece_color == 'b' and row == 7):
                        double_row = row + 2 * direction
                        double_forward = f"{col}{double_row}"
                        if double_forward not in board_state:
                            moves.append(double_forward)
            
            # Captures
            for dc in [-1, 1]:
                new_col = chr(ord(col) + dc)
                new_row = row + direction
                if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                    capture_pos = f"{new_col}{new_row}"
                    if capture_pos in board_state and board_state[capture_pos][0] != piece_color:
                        moves.append(capture_pos)
        
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
                    if target not in board_state or board_state[target][0] != piece_color:
                        moves.append(target)
        
        elif piece_type == 'r':  # Rook
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, piece_color))
        
        elif piece_type == 'b':  # Bishop
            for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, piece_color))
        
        elif piece_type == 'q':  # Queen
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                moves.extend(ChessBot.get_line_moves(pos, direction, board_state, piece_color))
        
        elif piece_type == 'k':  # King
            for dc in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if dc == 0 and dr == 0:
                        continue
                    new_col = chr(ord(col) + dc)
                    new_row = row + dr
                    if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                        target = f"{new_col}{new_row}"
                        # King can't move to occupied square by own piece
                        if target not in board_state or board_state[target][0] != piece_color:
                            # Additional check: king can't move adjacent to enemy king
                            if not ChessBot.is_adjacent_to_enemy_king(board_state, target, piece_color):
                                moves.append(target)
        
        return moves
    
    @staticmethod
    def is_adjacent_to_enemy_king(board_state, target_pos, own_color):
        """Check if target position is adjacent to enemy king"""
        col, row = target_pos[0], int(target_pos[1])
        enemy_king = f"{'b' if own_color == 'w' else 'w'}k"
        
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                check_col = chr(ord(col) + dc)
                check_row = row + dr
                if 'a' <= check_col <= 'h' and 1 <= check_row <= 8:
                    check_pos = f"{check_col}{check_row}"
                    if check_pos in board_state and board_state[check_pos] == enemy_king:
                        return True
        return False
    
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
        """Make a random valid legal move"""
        valid_moves = ChessBot.get_valid_moves(board_state, color)
        
        if not valid_moves:
            return None
        
        # Prioritize captures
        captures = [(from_pos, to_pos) for from_pos, to_pos in valid_moves if to_pos in board_state]
        
        if captures:
            # 70% chance to take a capture
            if random.random() < 0.7:
                return random.choice(captures)
        
        # Otherwise random move
        return random.choice(valid_moves)
