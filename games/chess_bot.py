"""
Chess Bot Engine with Mandatory Rule Enforcement
Priority-based decision making with full legal move validation
"""
import random


class ChessBot:
    """
    Chess bot with mandatory rule enforcement
    
    Priority Order:
    1. Resolve check (capture attacker, block, or move king)
    2. Detect checkmate/stalemate and end game
    3. Prefer safe moves that don't expose king
    4. Make strategic moves (captures, center control)
    """
    
    @staticmethod
    def make_move(board_state, color):
        """
        Main entry point - generates a legal move with priority enforcement
        Returns: (from_pos, to_pos) tuple or None if no legal moves
        """
        from .chess_rules import ChessRules
        
        # Step 1: Calculate ALL legal moves (filtered for king safety)
        legal_moves = ChessBot.get_all_legal_moves(board_state, color)
        
        # Step 2: If no legal moves, return None (checkmate or stalemate)
        if not legal_moves:
            return None
        
        # Step 3: Check if currently in check
        in_check = ChessRules.is_in_check(board_state, color)
        
        if in_check:
            # PRIORITY 1: Must resolve check immediately
            return ChessBot.select_check_escape_move(board_state, legal_moves, color)
        
        # PRIORITY 3 & 4: Select safe strategic move
        return ChessBot.select_strategic_move(board_state, legal_moves, color)
    
    @staticmethod
    def get_all_legal_moves(board_state, color):
        """
        Generate complete list of legal moves
        Every move is validated to ensure king is not left in check
        """
        legal_moves = []
        color_code = color[0] if len(color) > 1 else color
        
        for pos, piece in board_state.items():
            if piece and piece[0] == color_code:
                # Get pseudo-legal moves for this piece
                piece_moves = ChessBot.get_piece_pseudo_moves(pos, piece, board_state)
                
                # Filter: only keep moves that don't leave king in check
                for target in piece_moves:
                    if ChessBot.is_move_safe_for_king(board_state, pos, target, color):
                        legal_moves.append((pos, target))
        
        return legal_moves
    
    @staticmethod
    def is_move_safe_for_king(board_state, from_pos, to_pos, color):
        """
        Validate that a move doesn't leave the king in check
        Simulates the move and checks king safety
        """
        # Simulate move
        test_board = dict(board_state)
        piece = test_board[from_pos]
        test_board[to_pos] = piece
        del test_board[from_pos]
        
        # Find king position
        color_code = color[0] if len(color) > 1 else color
        king_piece = f"{color_code}k"
        king_pos = None
        
        for pos, p in test_board.items():
            if p == king_piece:
                king_pos = pos
                break
        
        if not king_pos:
            return False
        
        # Check if king is under attack
        opponent = 'white' if color in ['black', 'b'] else 'black'
        return not ChessBot.is_square_under_attack(test_board, king_pos, opponent)
    
    @staticmethod
    def select_check_escape_move(board_state, legal_moves, color):
        """
        Select best move to escape check
        Priority: Capture attacker > Block > Move king
        """
        capture_moves = []
        block_moves = []
        king_moves = []
        
        color_code = color[0] if len(color) > 1 else color
        
        for from_pos, to_pos in legal_moves:
            piece = board_state[from_pos]
            
            # Categorize moves
            if piece[1] == 'k':
                # King move
                king_moves.append((from_pos, to_pos))
            elif to_pos in board_state:
                # Capture (might capture the attacker)
                capture_moves.append((from_pos, to_pos))
            else:
                # Block move
                block_moves.append((from_pos, to_pos))
        
        # Priority: Capture > Block > King move
        if capture_moves:
            return random.choice(capture_moves)
        if block_moves:
            return random.choice(block_moves)
        if king_moves:
            return random.choice(king_moves)
        
        # Fallback: any legal move
        return random.choice(legal_moves)
    
    @staticmethod
    def select_strategic_move(board_state, legal_moves, color):
        """
        Select strategic move when not in check
        Prioritizes safe moves that don't expose king
        """
        # Categorize moves by safety and value
        safe_captures = []
        safe_moves = []
        risky_captures = []
        risky_moves = []
        
        for from_pos, to_pos in legal_moves:
            is_capture = to_pos in board_state
            is_safe = ChessBot.is_move_safe_position(board_state, from_pos, to_pos, color)
            
            if is_capture:
                if is_safe:
                    safe_captures.append((from_pos, to_pos))
                else:
                    risky_captures.append((from_pos, to_pos))
            else:
                if is_safe:
                    safe_moves.append((from_pos, to_pos))
                else:
                    risky_moves.append((from_pos, to_pos))
        
        # Priority: Safe captures > Safe moves > Risky captures > Risky moves
        if safe_captures:
            return random.choice(safe_captures)
        if safe_moves:
            return random.choice(safe_moves)
        if risky_captures:
            return random.choice(risky_captures)
        if risky_moves:
            return random.choice(risky_moves)
        
        # Fallback
        return random.choice(legal_moves)
    
    @staticmethod
    def is_move_safe_position(board_state, from_pos, to_pos, color):
        """
        Check if the destination square is safe (not under attack after move)
        """
        # Simulate move
        test_board = dict(board_state)
        piece = test_board[from_pos]
        test_board[to_pos] = piece
        del test_board[from_pos]
        
        # Check if destination is under attack
        opponent = 'white' if color in ['black', 'b'] else 'black'
        return not ChessBot.is_square_under_attack(test_board, to_pos, opponent)
    
    @staticmethod
    def get_piece_pseudo_moves(pos, piece, board_state):
        """Get pseudo-legal moves for a piece (doesn't check king safety)"""
        moves = []
        col, row = pos[0], int(pos[1])
        piece_type = piece[1]
        piece_color = piece[0]
        
        if piece_type == 'p':
            moves = ChessBot.get_pawn_moves(pos, piece_color, board_state)
        elif piece_type == 'n':
            moves = ChessBot.get_knight_moves(pos, piece_color, board_state)
        elif piece_type == 'b':
            moves = ChessBot.get_bishop_moves(pos, piece_color, board_state)
        elif piece_type == 'r':
            moves = ChessBot.get_rook_moves(pos, piece_color, board_state)
        elif piece_type == 'q':
            moves = ChessBot.get_queen_moves(pos, piece_color, board_state)
        elif piece_type == 'k':
            moves = ChessBot.get_king_moves(pos, piece_color, board_state)
        
        return moves
    
    @staticmethod
    def get_pawn_moves(pos, color, board_state):
        """Get pawn moves"""
        moves = []
        col, row = pos[0], int(pos[1])
        direction = 1 if color == 'w' else -1
        start_row = 2 if color == 'w' else 7
        
        # Forward move
        new_row = row + direction
        if 1 <= new_row <= 8:
            forward = f"{col}{new_row}"
            if forward not in board_state:
                moves.append(forward)
                
                # Double move from start
                if row == start_row:
                    double = f"{col}{row + 2 * direction}"
                    middle = f"{col}{row + direction}"
                    if double not in board_state and middle not in board_state:
                        moves.append(double)
        
        # Diagonal captures
        for dc in [-1, 1]:
            new_col = chr(ord(col) + dc)
            new_row = row + direction
            if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                capture = f"{new_col}{new_row}"
                if capture in board_state and board_state[capture][0] != color:
                    moves.append(capture)
        
        return moves
    
    @staticmethod
    def get_knight_moves(pos, color, board_state):
        """Get knight moves"""
        moves = []
        col, row = pos[0], int(pos[1])
        
        knight_offsets = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        
        for dc, dr in knight_offsets:
            new_col = chr(ord(col) + dc)
            new_row = row + dr
            if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                target = f"{new_col}{new_row}"
                if target not in board_state or board_state[target][0] != color:
                    moves.append(target)
        
        return moves
    
    @staticmethod
    def get_bishop_moves(pos, color, board_state):
        """Get bishop moves (diagonals)"""
        moves = []
        for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            moves.extend(ChessBot.get_sliding_moves(pos, direction, color, board_state))
        return moves
    
    @staticmethod
    def get_rook_moves(pos, color, board_state):
        """Get rook moves (straight lines)"""
        moves = []
        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            moves.extend(ChessBot.get_sliding_moves(pos, direction, color, board_state))
        return moves
    
    @staticmethod
    def get_queen_moves(pos, color, board_state):
        """Get queen moves (all directions)"""
        moves = []
        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            moves.extend(ChessBot.get_sliding_moves(pos, direction, color, board_state))
        return moves
    
    @staticmethod
    def get_king_moves(pos, color, board_state):
        """Get king moves (one square any direction)"""
        moves = []
        col, row = pos[0], int(pos[1])
        
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                new_col = chr(ord(col) + dc)
                new_row = row + dr
                if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                    target = f"{new_col}{new_row}"
                    if target not in board_state or board_state[target][0] != color:
                        # Check not adjacent to enemy king
                        if not ChessBot.is_adjacent_to_enemy_king(board_state, target, color):
                            moves.append(target)
        
        return moves
    
    @staticmethod
    def get_sliding_moves(pos, direction, color, board_state):
        """Get moves for sliding pieces (bishop, rook, queen)"""
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
                    moves.append(target)  # Capture
                break  # Blocked
            
            moves.append(target)
        
        return moves
    
    @staticmethod
    def is_adjacent_to_enemy_king(board_state, target, color):
        """Check if target is adjacent to enemy king"""
        col, row = target[0], int(target[1])
        enemy_king = f"{'b' if color == 'w' else 'w'}k"
        
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
    def is_square_under_attack(board_state, square, by_color):
        """Check if square is attacked by any piece of given color"""
        col, row = square[0], int(square[1])
        by_code = by_color[0] if len(by_color) > 1 else by_color
        
        # Pawn attacks
        pawn_dir = -1 if by_color in ['white', 'w'] else 1
        for dc in [-1, 1]:
            attack_col = chr(ord(col) + dc)
            attack_row = row + pawn_dir
            if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                pos = f"{attack_col}{attack_row}"
                if pos in board_state and board_state[pos] == f"{by_code}p":
                    return True
        
        # Knight attacks
        for dc, dr in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
            attack_col = chr(ord(col) + dc)
            attack_row = row + dr
            if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                pos = f"{attack_col}{attack_row}"
                if pos in board_state and board_state[pos] == f"{by_code}n":
                    return True
        
        # King attacks
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                attack_col = chr(ord(col) + dc)
                attack_row = row + dr
                if 'a' <= attack_col <= 'h' and 1 <= attack_row <= 8:
                    pos = f"{attack_col}{attack_row}"
                    if pos in board_state and board_state[pos] == f"{by_code}k":
                        return True
        
        # Sliding attacks (rook/queen - straight)
        for direction in [(0,1), (0,-1), (1,0), (-1,0)]:
            if ChessBot.check_sliding_attack(board_state, square, direction, by_code, ['r', 'q']):
                return True
        
        # Sliding attacks (bishop/queen - diagonal)
        for direction in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            if ChessBot.check_sliding_attack(board_state, square, direction, by_code, ['b', 'q']):
                return True
        
        return False
    
    @staticmethod
    def check_sliding_attack(board_state, square, direction, by_code, piece_types):
        """Check for sliding piece attack in a direction"""
        col, row = square[0], int(square[1])
        dc, dr = direction
        
        for i in range(1, 8):
            new_col = chr(ord(col) + dc * i)
            new_row = row + dr * i
            
            if not ('a' <= new_col <= 'h' and 1 <= new_row <= 8):
                break
            
            pos = f"{new_col}{new_row}"
            if pos in board_state:
                piece = board_state[pos]
                if piece[0] == by_code and piece[1] in piece_types:
                    return True
                break  # Blocked
        
        return False
