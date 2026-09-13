import bulletchess
import chess
import chess.polyglot
import math
import sys
import time


class TimeoutException(Exception):
    pass

from .base_agent import Base_agent

EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2


class AlphaBeta_agent(Base_agent):
    def __init__(self, depth = 99, name = "AlphaBeta", time_limit = 5.0, book_path = "book.bin"):
        super().__init__(name)
        self.book_path = book_path
        self.depth = depth
        self.time_limit = time_limit
        self.eval_cache = {}
        self.piece_values_mg = {
            bulletchess.PAWN : 124,
            bulletchess.BISHOP : 825,
            bulletchess.ROOK : 1276,
            bulletchess.KNIGHT : 781,
            bulletchess.QUEEN : 2538,
            bulletchess.KING : 0
        }

        self.piece_values_eg = {
            bulletchess.PAWN : 206,
            bulletchess.BISHOP : 915,
            bulletchess.ROOK : 1380,
            bulletchess.KNIGHT : 854,
            bulletchess.QUEEN : 2682,
            bulletchess.KING : 0
        }

        self.phase_weights = {
            bulletchess.PAWN : 0,
            bulletchess.KNIGHT: 1,
            bulletchess.BISHOP : 1,
            bulletchess.ROOK : 2,
            bulletchess.QUEEN : 4,
            bulletchess.KING : 0
        }

        self.max_phase = 24

#https://hxim.github.io/Stockfish-Evaluation-Guide/

        self.pst_mg = {
            bulletchess.PAWN: [
                 0,  0,  0,  0,  0,  0,  0,  0,
                 3,  3, 10, 19, 16, 19,  7, -5,
                -9,-15, 11, 15, 32, 22,  5,-22,
                13,  0,-13,  1, 11, -2,-13,  5,
                -4,-23,  6, 20, 40, 17,  4, -8,
                 5,-12, -7, 22, -8, -5,-15, -8,
                -7,  7, -3,-13,  5,-16, 10, -8,
                 0,  0,  0,  0,  0,  0,  0,  0
            ],
            bulletchess.KNIGHT: [
                -175,-92,-74,-73,-73,-74,-92,-175,
                 -77,-41,-27,-15,-15,-27,-41, -77,
                 -61,-17,  6, 12, 12,  6,-17, -61,
                 -35,  8, 40, 49, 49, 40,  8, -35,
                 -34, 13, 44, 51, 51, 44, 13, -34,
                  -9, 22, 58, 53, 53, 58, 22,  -9,
                 -67,-27,  4, 37, 37,  4,-27, -67,
                -201,-83,-56,-26,-26,-56,-83,-201
            ],
            bulletchess.BISHOP: [
                -53, -5, -8,-23,-23, -8, -5,-53,
                -15,  8, 19,  4,  4, 19,  8,-15,
                 -7, 21, -5, 17, 17, -5, 21, -7,
                 -5, 11, 25, 39, 39, 25, 11, -5,
                -12, 29, 22, 31, 31, 22, 29,-12,
                -16,  6,  1, 11, 11,  1,  6,-16,
                -17,-14,  5,  0,  0,  5,-14,-17,
                -48,  1,-14,-23,-23,-14,  1,-48
            ],
            bulletchess.ROOK: [
                -31,-20,-14, -5, -5,-14,-20,-31,
                -21,-13, -8,  6,  6, -8,-13,-21,
                -25,-11, -1,  3,  3, -1,-11,-25,
                -13, -5, -4, -6, -6, -4, -5,-13,
                -27,-15, -4,  3,  3, -4,-15,-27,
                -22, -2,  6, 12, 12,  6, -2,-22,
                 -2, 12, 16, 18, 18, 16, 12, -2,
                -17,-19, -1,  9,  9, -1,-19,-17
            ],
            bulletchess.QUEEN: [
                 3, -5, -5,  4,  4, -5, -5,  3,
                -3,  5,  8, 12, 12,  8,  5, -3,
                -3,  6, 13,  7,  7, 13,  6, -3,
                 4,  5,  9,  8,  8,  9,  5,  4,
                 0, 14, 12,  5,  5, 12, 14,  0,
                -4, 10,  6,  8,  8,  6, 10, -4,
                -5,  6, 10,  8,  8, 10,  6, -5,
                -2, -2,  1, -2, -2,  1, -2, -2
            ],
            bulletchess.KING: [
                271,327,271,198,198,271,327,271,
                278,303,234,179,179,234,303,278,
                195,258,169,120,120,169,258,195,
                164,190,138, 98, 98,138,190,164,
                154,179,105, 70, 70,105,179,154,
                123,145, 81, 31, 31, 81,145,123,
                 88,120, 65, 33, 33, 65,120, 88,
                 59, 89, 45, -1, -1, 45, 89, 59
            ]
        }

        self.pst_eg = {
            bulletchess.PAWN : [
                  0,  0,  0,  0,  0,  0,  0,  0,
                -10, -6, 10,  0, 14,  7, -5,-19,
                -10,-10,-10,  4,  4,  3, -6, -4,  
                  6, -2, -8, -4,-13,-12,-10, -9,
                 10,  5,  4, -5, -5, -5, 14,  9,
                 28, 20, 21, 28, 30,  7,  6, 13,
                  0,-11, 12, 21, 25, 19,  4,  7, 
                  0,  0,  0,  0,  0,  0,  0,  0
            ],
            bulletchess.KNIGHT : [
                -96,-65,-49,-21,-21,-49,-65,-96,
                -67,-54,-18,  8,  8,-18,-54,-67,
                -40,-27, -8, 29, 29, -8,-27,-40,
                -35, -2, 13, 28, 28, 13, -2,-35,
                -45,-16,  9, 39, 39,  9,-16,-45,
                -51,-44,-16, 17, 17,-16,-44,-51,
                -69,-50,-51, 12, 12,-51,-50,-69,
               -100,-88,-56,-17,-17,-56,-88,-100
            ],
            bulletchess.BISHOP : [
                -57,-30,-37,-12,-12,-37,-30,-57,
                -37,-13,-17,  1,  1,-17,-13,-37,
                -16, -1, -2, 10, 10, -2, -1,-16,
                -20, -6,  0, 17, 17,  0, -6,-20,
                -17, -1,-14, 15, 15,-14, -1,-17,
                -30,  6,  4,  6,  6,  4,  6,-30,
                -31,-20, -1,  1,  1, -1,-20,-31,
                -46,-42,-37,-24,-24,-37,-42,-46
            ],
            bulletchess.ROOK : [
                 -9,-13,-10, -9, -9,-10,-13, -9,
                -12, -9, -1, -2, -2, -1, -9,-12,
                  6, -8, -2, -6, -6, -2, -8,  6,
                 -6,  1, -9,  7,  7, -9,  1, -6,
                 -5,  8,  7, -6, -6,  7,  8, -5,
                  6,  1, -7, 10, 10, -7,  1, -6,
                  4,  5, 20, -5, -5, 20,  5,  4,
                 18,  0, 19, 13, 13, 19,  0, 18
            ],

            bulletchess.QUEEN : [
                -69, -57, -47, -26, -26, -47, -57, -69, 
                -55, -31, -22,  -4,  -4, -22, -31, -55,
                -39, -18,  -9,   3,   3,  -9, -18, -39,
                -23,  -3,  13,  24,  24,  13,  -3, -23,
                -29,  -6,   9,  21,  21,   9,  -6, -29,
                -38, -18, -12,   1,   1, -12, -18, -38,
                -50, -27, -24,  -8,  -8, -24, -27, -50,
                -75, -52, -43, -36, -36, -43, -52, -75 
            ],

            bulletchess.KING : [
                  1,  45,  85,  76,  76,  85,  45,   1, 
                 53, 100, 133, 135, 135, 133, 100,  53, 
                 88, 130, 169, 175, 175, 169, 130,  88, 
                103, 156, 172, 172, 172, 172, 156, 103, 
                 96, 166, 199, 199, 199, 199, 166,  96, 
                 92, 172, 184, 191, 191, 184, 172,  92, 
                 47, 121, 116, 131, 131, 116, 121,  47, 
                 11,  59,  73,  78,  78,  73,  59,  11  
            ]
        }

        self.mobility_mg = {
            bulletchess.KNIGHT : [-62,-53,-12,-4,3,13,22,28,33],
            bulletchess.BISHOP : [-48,-20,16,26,38,51,55,63,63,68,81,81,91,98],
            bulletchess.ROOK : [-60,-20,2,3,3,11,22,31,40,40,41,48,57,57,62],
            bulletchess.QUEEN : [-30,-12,-8,-9,20,23,23,35,38,53,64,65,65,66,67,67,72,72,77,79,93,108,108,108,110,114,114,116]
        }

        self.mobility_eg = {
            bulletchess.KNIGHT :  [-81,-56,-31,-16,5,11,17,20,25],
            bulletchess.BISHOP : [-59,-23,-3,13,24,42,54,57,65,73,78,86,88,97],
            bulletchess.ROOK : [-78,-17,23,39,70,99,103,121,134,139,158,164,168,169,172],
            bulletchess.QUEEN : [-48,-30,-7,19,40,55,59,75,78,96,96,100,121,127,131,133,136,141,147,150,151,168,168,171,182,182,192,219]
        }

        self.passed_pawn_mask = {bulletchess.WHITE: [0]*64, bulletchess.BLACK: [0]*64}
        self.adjacent_files_mask = [0]*8

        # 1. Generate the bitboards for files and ranks mathematically
        # File A is 0x0101010101010101. Shift it left to get B, C, D, etc.
        BB_FILES = [(0x0101010101010101 << i) for i in range(8)]
        
        # Rank 1 is 0xFF. Shift it left by 8 bits for each subsequent rank.
        BB_RANKS = [(0xFF << (i * 8)) for i in range(8)]

        # 2. Build adjacent file masks
        for file in range(8):
            mask = 0
            if file > 0: 
                mask |= BB_FILES[file - 1]
            if file < 7: 
                mask |= BB_FILES[file + 1]
            self.adjacent_files_mask[file] = mask

        # 3. Build passed pawn masks using integer square indexing (0 to 63)
        for square in range(64):
            file = square % 8    # Same as square_file
            rank = square // 8   # Same as square_rank
            
            file_mask = BB_FILES[file]
            adj_mask = self.adjacent_files_mask[file]

            # White pawns move "up" the ranks
            white_front = 0
            for r in range(rank + 1, 8):
                white_front |= BB_RANKS[r]
            self.passed_pawn_mask[bulletchess.WHITE][square] = (file_mask | adj_mask) & white_front

            # Black pawns move "down" the ranks
            black_front = 0
            for r in range(0, rank):
                 black_front |= BB_RANKS[r]
            self.passed_pawn_mask[bulletchess.BLACK][square] = (file_mask | adj_mask) & black_front

        self.transposition_table = {}

    #pour éviter les zugzwang dans le null-move pruning(voir alphabeta), 
    # on regarde si il reste des pièces 
    #(il y a toujours bcp de cas où il y aura de zugzwang, à voir 
    # si c'est intéressant de le garder)
    def _has_non_pawn_material(self, board : bulletchess.Board, color : bool):
        return bool(
            int(board[color, bulletchess.KNIGHT]) |
            int(board[color, bulletchess.BISHOP]) |
            int(board[color, bulletchess.ROOK]) |
            int(board[color, bulletchess.QUEEN])
        )

    def _push(self, board, move):
        board.apply(move)
        self.search_ply_count += 1

    def _push_null(self, board):
        board.apply(None)
        self.search_ply_count += 1

    def _pop(self, board):
        board.undo()
        self.search_ply_count -= 1

    def _compute_mobility_by_square(self, board):
        mobility_by_square = {}

        for move in board.legal_moves():
            origin = move.origin.index()
            mobility_by_square[origin] = mobility_by_square.get(origin, 0) + 1

        original_turn = board.turn
        board.turn = original_turn.opposite
        try:
            for move in board.legal_moves():
                origin = move.origin.index()
                mobility_by_square[origin] = mobility_by_square.get(origin, 0) + 1
        finally:
            board.turn = original_turn

        return mobility_by_square

    def _evaluate_board(self, board : bulletchess.Board):
        if board in bulletchess.CHECKMATE:
            return -99999 if board.turn == bulletchess.WHITE else 99999

        if board in bulletchess.DRAW :
            return 0

        key = hash(board)
        cached = self.eval_cache.get(key)
        if cached is not None :
            return cached

        piece_values_mg = self.piece_values_mg
        piece_values_eg = self.piece_values_eg
        phase_weights = self.phase_weights
        pst_mg = self.pst_mg
        pst_eg = self.pst_eg
        mobility_mg = self.mobility_mg
        mobility_eg = self.mobility_eg
        passed_pawn_mask = self.passed_pawn_mask
        adjacent_files_mask = self.adjacent_files_mask

        mobility_by_square = self._compute_mobility_by_square(board)

        mg_score = 0
        eg_score = 0
        phase = 0

        white_pawns = int(board[bulletchess.WHITE, bulletchess.PAWN])
        black_pawns = int(board[bulletchess.BLACK, bulletchess.PAWN])

        for piece_type in (bulletchess.PAWN, bulletchess.KNIGHT, bulletchess.BISHOP, bulletchess.ROOK, bulletchess.QUEEN, bulletchess.KING):
            val_mg = piece_values_mg[piece_type]
            val_eg = piece_values_eg[piece_type]
            p_weight = phase_weights[piece_type]
            table_mg = mobility_mg.get(piece_type)
            table_eg = mobility_eg.get(piece_type)

            for color in (bulletchess.WHITE, bulletchess.BLACK):
                # Getting the Bitboard for this color and piece
                mask = board[color, piece_type]
                
                # Convert to integer for bitwise math if necessary
                mask_int = int(mask)
                if not mask_int:
                    continue

                friendly_pawns = white_pawns if color == bulletchess.WHITE else black_pawns
                enemy_pawns = black_pawns if color == bulletchess.WHITE else white_pawns

                # bulletchess Bitboards can be iterated over directly to yield squares
                for square in mask:
                    phase += p_weight

                    # If your pst arrays use 0-63, ensure bulletchess square indices match your expected layout. 
                    sq_val = square.index()
                    idx = sq_val if color == bulletchess.WHITE else (sq_val ^ 56)
                    mg_pst = pst_mg[piece_type][idx]
                    eg_pst = pst_eg[piece_type][idx]

                    mob_mg = 0
                    mob_eg = 0
                    struct_mg = 0
                    struct_eg = 0

                    # Mobility evaluation
                    if table_mg is not None:
                        nb_moves = mobility_by_square.get(sq_val, 0)
                        mob_mg = table_mg[min(nb_moves, len(table_mg) - 1)]
                        mob_eg = table_eg[min(nb_moves, len(table_eg) - 1)]

                    # Pawn structure
                    if piece_type == bulletchess.PAWN:
                        file = sq_val % 8
                        file_mask = 0x0101010101010101 << file
                        adj_mask = adjacent_files_mask[file]

                        # Doubled pawns
                        if (friendly_pawns & file_mask).bit_count() > 1:
                            struct_mg -= 11
                            struct_eg -= 11

                        # Isolated pawns
                        if not (friendly_pawns & adj_mask):
                            struct_mg -= 5
                            struct_eg -= 15

                        # Passed pawns
                        if not (enemy_pawns & passed_pawn_mask[color][sq_val]):
                            struct_mg += 20
                            struct_eg += 40

                    if color == bulletchess.WHITE:
                        mg_score += val_mg + mg_pst + mob_mg + struct_mg
                        eg_score += val_eg + eg_pst + mob_eg + struct_eg
                    else:
                        mg_score -= val_mg + mg_pst + mob_mg + struct_mg
                        eg_score -= val_eg + eg_pst + mob_eg + struct_eg

        # 2. Space evaluation
        if phase > 16:
            blocked_pawns = (white_pawns << 8) & black_pawns
            blocked_count = blocked_pawns.bit_count() * 2

            # Sum all occupied squares using bitwise OR across piece types
            piece_count = 0
            for pt in (bulletchess.PAWN, bulletchess.KNIGHT, bulletchess.BISHOP, bulletchess.ROOK, bulletchess.QUEEN, bulletchess.KING):
                piece_count += int(board[bulletchess.WHITE, pt]).bit_count()
                piece_count += int(board[bulletchess.BLACK, pt]).bit_count()

            weight = piece_count - 3 + min(blocked_count, 9)

            white_space_mask = 0x000000003C3C3C00
            black_space_mask = 0x003C3C3C00000000

            # Compute attacks (Assuming A-file is 0x0101010101010101 and H-file is 0x8080808080808080)
            FILE_A = 0x0101010101010101
            FILE_H = 0x8080808080808080

            black_pawn_attacks = ((black_pawns >> 7) & ~FILE_A) | ((black_pawns >> 9) & ~FILE_H)
            white_pawn_attacks = ((white_pawns << 7) & ~FILE_H) | ((white_pawns << 9) & ~FILE_A)

            white_safe_space = white_space_mask & ~white_pawns & ~black_pawn_attacks
            black_safe_space = black_space_mask & ~black_pawns & ~white_pawn_attacks

            white_space_area = white_safe_space.bit_count()
            black_space_area = black_safe_space.bit_count()

            white_space_bonus = int((white_space_area * weight * weight) / 16)
            black_space_bonus = int((black_space_area * weight * weight) / 16)

            mg_score += white_space_bonus
            mg_score -= black_space_bonus

        phase = min(phase, self.max_phase)
        tapered_score = (mg_score * phase + eg_score * (self.max_phase - phase)) / self.max_phase
        self.eval_cache[key] = tapered_score

        return tapered_score

    def _gives_check(self, board, move):
        board.apply(move)
        is_check = board in bulletchess.CHECK
        board.undo()
        return is_check
    
    #pb rencontré : même en augmentant la profondeur, l'algo peut s'arrêter juste avant la fin d'une tactique (ex : il capture un pion avec sa dame mais le fou adverse vient la capturer après)
    # ==> Ajout de fonction pour évaluer si il y a encore des captures possibles. Si oui, on continue de calculer, sinon on peut arrêter
    def _quiescence(self, board : bulletchess.Board, alpha, beta, maximizing_player, qdepth = 0):
        self.nodes += 1
        stand_eval = self._evaluate_board(board)

        if maximizing_player:
            if stand_eval >= beta:
                return beta
            alpha = max(alpha, stand_eval)

        else : 
            if stand_eval <= alpha:
                return alpha
            beta = min(beta, stand_eval)

        if qdepth >= 6 :
            return alpha if maximizing_player else beta

        candidate_moves = [m for m in board.legal_moves() if m.is_capture(board) or (qdepth < 2 and self._gives_check(board, m))]

        legal_moves = self._order_moves(board, candidate_moves)

        DELTA_MARGIN = 200

        for move in legal_moves:
            is_capture = move.is_capture(board)
            is_check = self._gives_check(board, move)

            if not is_capture and not is_check:
                continue

            if is_capture and not is_check :
                victim = board[move.destination]
                victim_type = victim.piece_type if victim else None
                victim_value = self.piece_values_mg[victim_type] if victim_type else 100
                if maximizing_player and stand_eval + victim_value + DELTA_MARGIN < alpha :
                    continue

                if not maximizing_player and stand_eval - victim_value - DELTA_MARGIN > beta:
                    continue

            piece = board[move.origin]
            piece_move_type = piece.piece_type if piece else None

            self._push(board, move)

            is_safe = True

            if is_check :
                for next_move in board.legal_moves():
                    if next_move.destination == move.destination:
                        attacker = board[next_move.origin]
                        attacker_type = attacker.piece_type if attacker else None
                        
                        if attacker_type is not None:
                            if not is_capture:
                                is_safe = False
                                break
                            else:
                                if self.piece_values_mg[attacker_type] <= self.piece_values_mg[piece_move_type]:
                                    is_safe = False
                                    break

            if not is_safe:
                self._pop(board)
                continue
                # sinon, on garde le push actuel, pas besoin de repush plus bas


            score = self._quiescence(board, alpha, beta, not maximizing_player, qdepth + 1)
            self._pop(board)

            if maximizing_player:
                if score > alpha :
                    alpha = score
                if alpha >= beta :
                    return beta

            else : 
                if score < beta :
                    beta = score

                if beta <= alpha:
                    return alpha

        return alpha if maximizing_player else beta


    #pour qu'ils considèrent les captures et les coups qui semblent être les meilleurs avant comme ça il élague plus de coups
    def _order_moves(self, board, moves, ply = -1, tt_move=None):
        color = board.turn
        def score(move):
            if tt_move is not None and move == tt_move:
                return 1 << 24
            
            if move.is_capture(board):
                victim = board[move.destination]
                attacker = board[move.origin]
                v_val = self.piece_values_mg[victim.piece_type] if victim else 100  # en passant
                a_val = self.piece_values_mg[attacker.piece_type] if attacker else 0
                return (1 << 23) + v_val - a_val
            
            if ply < len(self.killer_moves):
                if move == self.killer_moves[ply][0]:
                    return 1 << 22
                elif move == self.killer_moves[ply][1]:
                    return 1 << 21
                
            from_idx = move.origin.index()
            to_idx = move.destination.index()
            return self.history_table[color][from_idx][to_idx]
        
        return sorted(moves, key=score, reverse=True)

    def _alphabeta(self, board : bulletchess.Board, depth : int, alpha : float, beta : float, maximizing_player : bool, ply : int = 0):
        MAX_HISTORY = (1 << 20) - 1

        self.nodes += 1
        if self.nodes % 2048 == 0 :
            if time.time() - self.start_time > self.time_limit:
                raise TimeoutException()

        try:
            if board.is_repetition(2):
                return 0
        except AttributeError:
            if board in bulletchess.DRAW:
                return 0
        
        alpha_orig = alpha
        beta_orig = beta

        key = hash(board)
        tt_entry = self.transposition_table.get(key)
        tt_move = None

        if tt_entry is not None and tt_entry["depth"] >= depth :
            tt_move = tt_entry.get("best_move")
            flag = tt_entry["flag"]
            value = tt_entry["value"]

            if flag == EXACT:
                return value
            elif flag == LOWERBOUND :
                alpha = max(alpha, value)
            elif flag == UPPERBOUND :
                beta = min(beta, value)
            if alpha >= beta:
                return value

        elif tt_entry is not None :
            tt_move = tt_entry.get("best_move")

        #l'idée c'est de se demander si on passe son tour, est ce que la position est toujours bonne
        # si elle l'est alors ça nous permet d'élaguer plus tôt
        R = 3
        NULL_MOVE_MIN_DEPTH = 3
        if (depth >= NULL_MOVE_MIN_DEPTH and not (board in bulletchess.CHECK) and self._has_non_pawn_material(board, board.turn) and beta < math.inf):
            self._push_null(board)
            null_score = self._alphabeta(board, depth - 1 - R,alpha, beta, not maximizing_player, ply + 1)
            self._pop(board)

            if maximizing_player and null_score >= beta:
                return beta
            if not maximizing_player and null_score <= alpha:
                return alpha
        
        if depth <= 0 or board in bulletchess.CHECKMATE or board in bulletchess.DRAW:
            return self._quiescence(board, alpha, beta, maximizing_player)

        best_move_found = None
        legal_moves = self._order_moves(board, board.legal_moves(), ply)

        if maximizing_player:
            max_eval = -math.inf
            for move in legal_moves:
                self._push(board, move)

                extension = 1 if board in bulletchess.CHECK else 0
                if ply <= 50 :
                    extension = 0

                eval_score = self._alphabeta(board, depth - 1 + extension, alpha, beta, False, ply + 1)
                self._pop(board)

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move_found = move
                    
                alpha = max(alpha, eval_score)

                if beta <= alpha :
                    if not move.is_capture(board) :
                        if self.killer_moves[ply][0] != move and ply < len(self.killer_moves) :
                            self.killer_moves[ply][1] = self.killer_moves[ply][0]
                            self.killer_moves[ply][0] = move

                        from_idx = move.origin.index()
                        to_idx = move.destination.index()
                        turn_idx = board.turn

                        self.history_table[turn_idx][from_idx][to_idx] += depth << 2

                        if self.history_table[turn_idx][from_idx][to_idx] > MAX_HISTORY :
                            self.history_table[turn_idx][from_idx][to_idx] >>=1
                    break

            result = max_eval

        else :
            min_eval = math.inf
            for move in legal_moves:
                self._push(board, move)

                extension = 1 if board in bulletchess.CHECK else 0

                if ply <= 50:
                    extension = 0
                eval_score = self._alphabeta(board, depth - 1 + extension, alpha, beta, True, ply + 1)
                self._pop(board)

                if eval_score < min_eval :
                    min_eval = eval_score
                    best_move_found = move

                beta = min(beta, eval_score)

                if beta <= alpha:
                    if not move.is_capture(board) :
                        if self.killer_moves[ply][0] != move and ply < len(self.killer_moves) :
                            self.killer_moves[ply][1] = self.killer_moves[ply][0]
                            self.killer_moves[ply][0] = move

                        from_idx = move.origin.index()
                        to_idx = move.destination.index()
                        turn_idx = board.turn
                        self.history_table[turn_idx][from_idx][to_idx] += depth << 2

                        if self.history_table[turn_idx][from_idx][to_idx] > MAX_HISTORY :
                            self.history_table[turn_idx][from_idx][to_idx] >>=1
                        
                    break
            result = min_eval

        if result <= alpha_orig:
            flag = UPPERBOUND
        elif result >= beta_orig:
            flag = LOWERBOUND
        else:
            flag = EXACT

        self.transposition_table[key] = {
                "value":result,
                "depth":depth,
                "flag":flag,
                "best_move" : best_move_found
            }
        return result


    # Ajout d'une détection de mat en 1 car l'algorithme ne préfère pas forcément le mat en 1 à un mat en 2, les deux ayant 999 en valeur.
    def _checkmate_in_one(self, board : bulletchess.Board):
        for move in board.legal_moves():
            self._push(board, move)
            if board in bulletchess.CHECKMATE:
                self._pop(board)
                return move
            self._pop(board)

    
    def get_move(self, board : bulletchess.Board, time_left : float = None, increment : float = 0.0):
        return_python_chess_move = False
        if isinstance(board, chess.Board):
            board = bulletchess.Board.from_fen(board.fen())
            return_python_chess_move = True

        if self.book_path:
            try:
                temp_board = chess.Board(board.fen())
                with chess.polyglot.open_reader(self.book_path) as reader:
                    # weighted_choice automatically picks a move based on book weights, adding variety
                    entry = reader.weighted_choice(temp_board)
                    move_uci = entry.move.uci()
                    print(f"📖 Livre d'ouverture utilisé : {move_uci}", file=sys.stderr)

                    for m in board.legal_moves():
                        # bulletchess moves usually stringify to their UCI format
                        if str(m) == move_uci:
                            return m

                    return entry.move
            except FileNotFoundError:
                print(f"⚠️ Fichier book introuvable à {self.book_path}, passage à la recherche normale.", file=sys.stderr)
            except IndexError:
                # IndexError is raised if the position is not in the book
                pass

        if time_left is not None :
            self.time_limit = (time_left / 30.0) + (increment / 2.0)
            self.time_limit = min(self.time_limit, max(0.1, time_left - 0.5))
        else :
            self.time_limit = 3.0

        self.start_time = time.time()
        self.nodes = 0
        self.search_ply_count = 0

        self.killer_moves = [[None, None] for _ in range(128)]

        self.history_table = {
            bulletchess.WHITE: [[0]*64 for _ in range(64)],
            bulletchess.BLACK: [[0]*64 for _ in range(64)]
        }

        best_move_overall = None
        best_score_overall = 0 
        is_maximising = (board.turn == bulletchess.WHITE)

        try :
            for current_depth in range(1, self.depth + 1):
                nodes_before = self.nodes
                best_move_depth = None
                alpha = -math.inf
                beta = math.inf
                
                key = hash(board)
                tt_entry = self.transposition_table.get(key)
                tt_move = tt_entry.get("best_move") if tt_entry else None
                if best_move_overall :
                    tt_move = best_move_overall

                legal_moves = self._order_moves(board, list(board.legal_moves()), tt_move=tt_move, ply = 0)

                if is_maximising:
                    best_score = - math.inf
                    
                    for move in legal_moves:
                        self._push(board, move)
                        score = self._alphabeta(board, current_depth - 1, alpha, beta, False, ply = 1)
                        self._pop(board)

                        if score > best_score:
                            best_score = score
                            best_move_depth = move

                        alpha = max(alpha, best_score)

                else : 
                    best_score = math.inf
                    for move in legal_moves:
                        self._push(board, move)
                        score = self._alphabeta(board, current_depth - 1, alpha, beta, True, ply = 1)
                        self._pop(board)
                        
                        if score < best_score:
                            best_score = score
                            best_move_depth = move

                        beta = min(beta, best_score)

                best_move_overall = best_move_depth    
                best_score_overall = best_score
                formatted_score = f"{best_score_overall / 100:+.2f}"
                elapsed_time = time.time() - self.start_time
                print(f"✅ [Profondeur {current_depth}] terminée en {elapsed_time:.2f}s | Éval: {formatted_score} | Coup: {best_move_overall}", file=sys.stderr)
                print(f"depth {current_depth} : {self.nodes - nodes_before} nodes, {elapsed_time:.3f}s", file = sys.stderr)
        except TimeoutException:
            print(f'{self.time_limit} depasse', file = sys.stderr)
            while self.search_ply_count > 0:
                self._pop(board)
        if best_move_overall is None :
            best_move_overall = list(board.legal_moves())[0]

        #Ajout d'une vérification de mat en 1 pour s'assurer que l'IA ne rate pas un mat immédiat
        checkmate_move = self._checkmate_in_one(board)
        if checkmate_move is not None:
            print("✅ Mat en 1 détecté !", file=sys.stderr)
            best_move_overall = checkmate_move

        if return_python_chess_move:
            # Convert the bulletchess move back to a python-chess move for Lichess
            return chess.Move.from_uci(str(best_move_overall))


        return best_move_overall