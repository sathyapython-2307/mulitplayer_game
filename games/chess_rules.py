"""
Comprehensive Chess Rules Engine
Validates all moves for both human and bot players
"""

class ChessRules:
    """Complete chess rules validation engine"""
    
    @staticmethod
    def is_valid_move(board_state, from_pos, to_pos, current_turn):
        """
        Main validation function - checks if a move is legal
        Returns (is_valid, error_message)
        """
        # Basic validation
        if from_pos not in board_state:
            return False, "No piece at starting position"
        
        piece = board_state[from_pos]
        piece_color = 'white' if piece[0] == 'w' else 'black'
        
        # Normalize current_turn for comparison
        turn_color = current_turn if current_turn in ['white', 'black'] else ('white' if current_turn == 'w' else 'black')
        
        # Check if it's the correct player's turn
        if piece_color != turn_color:
            return False, "Not your piece"
        
        # Check if destination is valid
        if to_pos == from_pos:
            return False, "Must move to different square"
        
        # Check if capturing own piece
        if to_pos in board_state and board_state[to_pos][0] == piece[0]:
            return False, "Cannot capture your own piece"
        
        # Check if move is pseudo-legal for this piece type
        if not ChessRules.is_pseudo_legal_move(board_state, from_pos, to_pos, piece):
            return False, "Illegal move for this piece"
        
        # Check if move leaves king in check (most important check)
        if not ChessRules.is_move_legal_king_safety(board_state, from_pos, to_pos, piece_color):
            return False, "Move leaves king in check"
        
        return True, "Valid move"
    
    @staticmethod
    def is_pseudo_legal_move(board_state, from_pos, to_pos, piece):
        """Check if move follows piece movement rules (doesn't check king safety yet)"""
        piece_type = piece[1]
        piece_color = piece[0]
        
        if piece_type == 'p':
            return ChessRules.is_valid_pawn_move(board_state, from_pos, to_pos, piece_color)
        elif piece_type == 'n':
            return ChessRules.is_valid_knight_move(board_state, from_pos, to_pos, piece_color)
        elif piece_type == 'b':
            return ChessRules.is_valid_bishop_move(board_state, from_pos, to_pos, piece_color)
        elif piece_type == 'r':
            return ChessRules.is_valid_rook_move(board_state, from_pos, to_pos, piece_color)
        elif piece_type == 'q':
            return ChessRules.is_valid_queen_move(board_state, from_pos, to_pos, piece_color)
        elif piece_type == 'k':
            return ChessRules.is_valid_king_move(board_state, from_pos, to_pos, piece_color)
        
        return False
    
    @staticmethod
    def is_valid_pawn_move(board_state, from_pos, to_pos, color):
        """Validate pawn moves"""
        from_col, from_row = from_pos[0], int(from_pos[1])
        to_col, to_row = to_pos[0], int(to_pos[1])
        
        direction = 1 if color == 'w' else -1
        start_row = 2 if color == 'w' else 7
        
        # Forward move
        if from_col == to_col:
            # Single forward
            if to_row == from_row + direction:
                return to_pos not in board_state
            # Double forward from start
            if from_row == start_row and to_row == from_row + 2 * direction:
                middle = f"{from_col}{from_row + direction}"
                return to_pos not in board_state and middle not in board_state
            return False
        
        # Diagonal capture
        if abs(ord(to_col) - ord(from_col)) == 1 and to_row == from_row + direction:
            return to_pos in board_state and board_state[to_pos][0] != color
        
        return False
    
    @staticmethod
    def is_valid_knight_move(board_state, from_pos, to_pos, color):
        """Validate knight moves"""
        from_col, from_row = from_pos[0], int(from_pos[1])
        to_col, to_row = to_pos[0], int(to_pos[1])
        
        dc = abs(ord(to_col) - ord(from_col))
        dr = abs(to_row - from_row)
        
        # L-shape: 2+1 or 1+2
        return (dc == 2 and dr == 1) or (dc == 1 and dr == 2)
    
    @staticmethod
    def is_valid_bishop_move(board_state, from_pos, to_pos, color):
        """Validate bishop moves"""
        return ChessRules.is_diagonal_clear(board_state, from_pos, to_pos)
    
    @staticmethod
    def is_valid_rook_move(board_state, from_pos, to_pos, color):
        """Validate rook moves"""
        return ChessRules.is_straight_clear(board_state, from_pos, to_pos)
    
    @staticmethod
    def is_valid_queen_move(board_state, from_pos, to_pos, color):
        """Validate queen moves (rook + bishop)"""
        return (ChessRules.is_straight_clear(board_state, from_pos, to_pos) or
                ChessRules.is_diagonal_clear(board_state, from_pos, to_pos))
    
    @staticmethod
    def is_valid_king_move(board_state, from_pos, to_pos, color):
        """Validate king moves"""
        from_col, from_row = from_pos[0], int(from_pos[1])
        to_col, to_row = to_pos[0], int(to_pos[1])
        
        dc = abs(ord(to_col) - ord(from_col))
        dr = abs(to_row - from_row)
        
        # King moves one square in any direction
        if dc <= 1 and dr <= 1:
            # Check if destination is adjacent to enemy king
            enemy_color = 'b' if color == 'w' else 'w'
            enemy_king = f"{enemy_color}k"
            
            # Check all squares around destination
            for ddc in [-1, 0, 1]:
                for ddr in [-1, 0, 1]:
                    if ddc == 0 and ddr == 0:
                        continue
                    check_col = chr(ord(to_col) + ddc)
                    check_row = to_row + ddr
                    if 'a' <= check_col <= 'h' and 1 <= check_row <= 8:
                        check_pos = f"{check_col}{check_row}"
                        if check_pos in board_state and board_state[check_pos] == enemy_king:
                            return False  # Can't move adjacent to enemy king
            
            return True
        
        # TODO: Castling (for future enhancement)
        return False
    
    @staticmethod
    def is_straight_clear(board_state, from_pos, to_pos):
        """Check if path is clear for rook-like movement"""
        from_col, from_row = from_pos[0], int(from_pos[1])
        to_col, to_row = to_pos[0], int(to_pos[1])
        
        # Must be same row or same column
        if from_col != to_col and from_row != to_row:
            return False
        
        # Check path is clear
        if from_col == to_col:  # Vertical
            step = 1 if to_row > from_row else -1
            for row in range(from_row + step, to_row, step):
                if f"{from_col}{row}" in board_state:
                    return False
        else:  # Horizontal
            step = 1 if ord(to_col) > ord(from_col) else -1
            col = ord(from_col) + step
            while col != ord(to_col):
                if f"{chr(col)}{from_row}" in board_state:
                    return False
                col += step
        
        return True
    
    @staticmethod
    def is_diagonal_clear(board_state, from_pos, to_pos):
        """Check if path is clear for bishop-like movement"""
        from_col, from_row = from_pos[0], int(from_pos[1])
        to_col, to_row = to_pos[0], int(to_pos[1])
        
        dc = ord(to_col) - ord(from_col)
        dr = to_row - from_row
        
        # Must be diagonal
        if abs(dc) != abs(dr):
            return False
        
        # Check path is clear
        col_step = 1 if dc > 0 else -1
        row_step = 1 if dr > 0 else -1
        
        steps = abs(dc)
        for i in range(1, steps):
            check_col = chr(ord(from_col) + i * col_step)
            check_row = from_row + i * row_step
            if f"{check_col}{check_row}" in board_state:
                return False
        
        return True
    
    @staticmethod
    def is_move_legal_king_safety(board_state, from_pos, to_pos, color):
        """
        Check if move is legal considering king safety
        Simulates move and checks if king is in check
        """
        # Simulate the move
        test_board = dict(board_state)
        piece = test_board[from_pos]
        test_board[to_pos] = piece
        del test_board[from_pos]
        
        # Normalize color
        color_code = color[0] if len(color) > 1 else color
        
        # Find king position after move
        king_piece = f"{color_code}k"
        king_pos = None
        for pos, p in test_board.items():
            if p == king_piece:
                king_pos = pos
                break
        
        if not king_pos:
            return False  # King not found (shouldn't happen)
        
        # Check if king is under attack
        opponent_color = 'black' if color_code == 'w' else 'white'
        return not ChessRules.is_square_under_attack(test_board, king_pos, opponent_color)
    
    @staticmethod
    def is_square_under_attack(board_state, square, by_color):
        """Check if a square is attacked by any piece of the given color"""
        col, row = square[0], int(square[1])
        by_color_code = by_color[0] if len(by_color) > 1 else by_color
        
        # Check for pawn attacks
        # White pawns attack upward (from lower rows), black pawns attack downward
        pawn_dir = -1 if by_color_code == 'w' else 1
        for dc in [-1, 1]:
            attack_col = chr(ord(col) + dc)
            attack_row = row + pawn_dir
            if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                attack_pos = f"{attack_col}{attack_row}"
                if attack_pos in board_state and board_state[attack_pos] == f"{by_color_code}p":
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
                if attack_pos in board_state and board_state[attack_pos] == f"{by_color_code}n":
                    return True
        
        # Check for king attacks
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                attack_col = chr(ord(col) + dc)
                attack_row = row + dr
                if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                    attack_pos = f"{attack_col}{attack_row}"
                    if attack_pos in board_state and board_state[attack_pos] == f"{by_color_code}k":
                        return True
        
        # Check for sliding piece attacks
        # Rook/Queen (straight lines)
        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if ChessRules.check_sliding_attack(board_state, square, direction, by_color_code, ['r', 'q']):
                return True
        
        # Bishop/Queen (diagonals)
        for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            if ChessRules.check_sliding_attack(board_state, square, direction, by_color_code, ['b', 'q']):
                return True
        
        return False
    
    @staticmethod
    def check_sliding_attack(board_state, square, direction, by_color_code, piece_types):
        """Check for sliding piece attacks in a direction"""
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
                if piece[0] == by_color_code and piece[1] in piece_types:
                    return True
                break  # Path blocked
        
        return False
    
    @staticmethod
    def is_in_check(board_state, color):
        """Check if the given color's king is in check"""
        # Normalize color
        color_code = color[0] if len(color) > 1 else color
        
        # Find king
        king_piece = f"{color_code}k"
        king_pos = None
        for pos, piece in board_state.items():
            if piece == king_piece:
                king_pos = pos
                break
        
        if not king_pos:
            return False
        
        opponent_color = 'black' if color_code == 'w' else 'white'
        return ChessRules.is_square_under_attack(board_state, king_pos, opponent_color)
    
    @staticmethod
    def has_legal_moves(board_state, color):
        """Check if color has any legal moves (for checkmate/stalemate detection)"""
        color_code = color[0] if len(color) > 1 else color
        
        for pos, piece in board_state.items():
            if piece and piece[0] == color_code:
                # Try all possible destinations
                for file in 'abcdefgh':
                    for rank in range(1, 9):
                        to_pos = f"{file}{rank}"
                        if to_pos != pos:  # Skip same square
                            is_valid, _ = ChessRules.is_valid_move(board_state, pos, to_pos, color)
                            if is_valid:
                                return True
        return False
    
    @staticmethod
    def check_game_status(board_state, current_turn):
        """
        Check game status after a move
        Returns: (status, winner, reason)
        status: 'playing', 'checkmate', 'stalemate', 'draw'
        winner: 'white', 'black', or None
        reason: description of end condition
        """
        in_check = ChessRules.is_in_check(board_state, current_turn)
        has_moves = ChessRules.has_legal_moves(board_state, current_turn)
        
        if not has_moves:
            if in_check:
                # Checkmate - opponent wins
                winner = 'black' if current_turn == 'white' else 'white'
                return 'checkmate', winner, 'Checkmate'
            else:
                # Stalemate - draw
                return 'stalemate', None, 'Stalemate - No legal moves'
        
        # Check for insufficient material (basic check)
        if ChessRules.is_insufficient_material(board_state):
            return 'draw', None, 'Draw - Insufficient material'
        
        # Game continues
        if in_check:
            return 'check', None, 'Check'
        
        return 'playing', None, None
    
    @staticmethod
    def is_insufficient_material(board_state):
        """Check for insufficient material to checkmate"""
        pieces = list(board_state.values())
        
        # Only kings left
        if len(pieces) == 2:
            return True
        
        # King + minor piece vs King
        if len(pieces) == 3:
            piece_types = [p[1] for p in pieces]
            if 'n' in piece_types or 'b' in piece_types:
                return True
        
        return False
