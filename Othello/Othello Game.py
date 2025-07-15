import sys
import math
import time
import re
import random

# --- Othello Interface with Enhanced AI ---

class OthelloGame:
    def __init__(self, board_str=None, current_token=None, history=None, ai_difficulty="hard", verbose=False, human_token="X"):
        self.board_size = 8
        self.board = self._initialize_board(board_str)
        self.human_token = human_token.upper()
        self.ai_token = "O" if self.human_token == "X" else "X"
        self.current_token = current_token if current_token else self._get_starting_token(board_str)
        self.history = history if history else []
        self.ai_difficulty = ai_difficulty.lower()
        self.verbose = verbose
        self.alphabet_list = [*"ABCDEFGH"]
        self.ind_to_ainote = {}
        self.ainote_to_ind = {}
        self.pos_to_move = {}
        self._initialize_lookup_tables()
        self.hl = 11 # Default horizon limit

    def _initialize_lookup_tables(self):
        for i in range(self.board_size * self.board_size):
            self.ind_to_ainote[i] = self.alphabet_list[i % self.board_size] + str(i // self.board_size + 1)
            self.ainote_to_ind[self.ind_to_ainote[i]] = i
            self.pos_to_move[i] = self._get_possible_capture_sets(i)

    def _get_possible_capture_sets(self, pos):
        capture_sets = []
        row, col = divmod(pos, self.board_size)

        # Horizontal
        left = [i for i in range(pos - 1, row * self.board_size - 1, -1)]
        if left: capture_sets.append(left)
        right = [i for i in range(pos + 1, (row + 1) * self.board_size)]
        if right: capture_sets.append(right)

        # Vertical
        up = [i for i in range(pos - self.board_size, -1, -self.board_size)]
        if up: capture_sets.append(up)
        down = [i for i in range(pos + self.board_size, self.board_size * self.board_size, self.board_size)]
        if down: capture_sets.append(down)

        # Diagonals
        ul = [pos - 9 * i for i in range(1, min(row, col) + 1)]
        if ul: capture_sets.append(ul)
        ur = [pos - 7 * i for i in range(1, min(row, self.board_size - 1 - col) + 1)]
        if ur: capture_sets.append(ur)
        dl = [pos + 7 * i for i in range(1, min(self.board_size - 1 - row, col) + 1)]
        if dl: capture_sets.append(dl)
        dr = [pos + 9 * i for i in range(1, min(self.board_size - 1 - row, self.board_size - 1 - col) + 1)]
        if dr: capture_sets.append(dr)

        return capture_sets

    def _initialize_board(self, board_str=None):
        if board_str and len(board_str) == self.board_size * self.board_size and all(c in "XO." for c in board_str.upper()):
            return [list(board_str[i:i + self.board_size]) for i in range(0, self.board_size * self.board_size, self.board_size)]
        else:
            initial_board = [["." for _ in range(self.board_size)] for _ in range(self.board_size)]
            mid = self.board_size // 2
            initial_board[mid - 1][mid - 1] = "O"
            initial_board[mid - 1][mid] = "X"
            initial_board[mid][mid - 1] = "X"
            initial_board[mid][mid] = "O"
            return initial_board

    def _get_starting_token(self, board_str=None):
        if board_str:
            return "XO"[board_str.upper().count(".") % 2]
        else:
            return "X"

    def algebraic_to_coords(self, move_str):
        if len(move_str) == 2 and 'A' <= move_str[0] <= 'H' and '1' <= move_str[1] <= '8':
            col = ord(move_str[0]) - ord('A')
            row = int(move_str[1]) - 1
            return row, col
        return None, None

    def coords_to_algebraic(self, row, col):
        return self.alphabet_list[col] + str(row + 1)

    def get_possible_moves(self, player_token):
        possible_moves = set()
        opponent_token = "X" if player_token == "O" else "O"
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r][c] == ".":
                    if self._can_flip(r, c, player_token, opponent_token):
                        possible_moves.add(self.coords_to_algebraic(r, c))
        return sorted(list(possible_moves))

    def _can_flip(self, r_move, c_move, player_token, opponent_token):
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            r, c = r_move + dr, c_move + dc
            flipped = []
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == opponent_token:
                flipped.append((r, c))
                r += dr
                c += dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player_token and flipped:
                return True
        return False

    def make_move(self, move_str, player_token):
        row, col = self.algebraic_to_coords(move_str)
        if row is None or not self._can_flip(row, col, player_token, "X" if player_token == "O" else "O"):
            return False

        opponent_token = "X" if player_token == "O" else "O"
        self.board[row][col] = player_token
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            r, c = row + dr, col + dc
            flipped = []
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == opponent_token:
                flipped.append((r, c))
                r += dr
                c += dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player_token:
                for flip_r, flip_c in flipped:
                    self.board[flip_r][flip_c] = player_token
        self.history.append((player_token, move_str, [list(row) for row in self.board]))
        self.current_token = opponent_token
        return True

    def display_board(self, possible_moves=None):
        header = "  " + " ".join(self.alphabet_list)
        print(header)
        for r in range(self.board_size):
            row_str = f"{r + 1} "
            for c in range(self.board_size):
                piece = self.board[r][c]
                if possible_moves and self.coords_to_algebraic(r, c) in possible_moves:
                    row_str += "* "
                else:
                    row_str += f"{piece} "
            print(row_str)
        x_count = sum(row.count("X") for row in self.board)
        o_count = sum(row.count("O") for row in self.board)
        print(f"Score: X - {x_count}, O - {o_count}")

    def check_game_over(self):
        player1_moves = self.get_possible_moves("X")
        player2_moves = self.get_possible_moves("O")
        return not player1_moves and not player2_moves

    def get_winner(self):
        x_count = sum(row.count("X") for row in self.board)
        o_count = sum(row.count("O") for row in self.board)
        if x_count > o_count:
            return "X"
        elif o_count > x_count:
            return "O"
        else:
            return "Tie"

    def play_human_turn(self):
        possible_moves = self.get_possible_moves(self.human_token)
        if not possible_moves:
            print(f"No valid moves for {self.human_token}. Skipping turn.")
            self.current_token = self.ai_token
            return True # Indicate turn skipped

        while True:
            print(f"Possible moves for {self.human_token}: {possible_moves}")
            move_str = input(f"Your turn ({self.human_token}). Enter your move (e.g., A1): ").upper()
            if move_str in possible_moves:
                if self.make_move(move_str, self.human_token):
                    return False
            else:
                print("Invalid move. Please choose from the possible moves.")

    def play_ai_turn(self):
        possible_moves = self.get_possible_moves(self.ai_token)
        if not possible_moves:
            print(f"No valid moves for AI ({self.ai_token}). Skipping turn.")
            self.current_token = self.human_token
            return True # Indicate turn skipped

        print(f"AI ({self.ai_token}) is thinking...")
        if self.ai_difficulty == "easy":
            ai_move = self._ai_easy(possible_moves)
        elif self.ai_difficulty == "medium":
            ai_move = self._ai_medium(possible_moves)
        elif self.ai_difficulty == "hard":
            ai_move = self._ai_hard(possible_moves)
        else:
            print("Invalid AI difficulty. Making a random move.")
            ai_move = self._ai_easy(possible_moves)

        if ai_move:
            print(f"AI ({self.ai_token}) plays: {ai_move}")
            self.make_move(ai_move, self.ai_token)
            return False
        else:
            print("AI could not find a valid move (this should not happen).")
            return True

    def _ai_easy(self, possible_moves):
        return random.choice(possible_moves) if possible_moves else None

    def _ai_medium(self, possible_moves):
        best_move = None
        max_flips = -1
        opponent_token = self.human_token

        for move_str in possible_moves:
            row, col = self.algebraic_to_coords(move_str)
            temp_board = [list(r) for r in self.board]
            flips = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                r, c = row + dr, col + dc
                flipped_in_dir = []
                while 0 <= r < self.board_size and 0 <= c < self.board_size and temp_board[r][c] == opponent_token:
                    flipped_in_dir.append((r, c))
                    r += dr
                    c += dc
                if 0 <= r < self.board_size and 0 <= c < self.board_size and temp_board[r][c] == self.ai_token:
                    flips += len(flipped_in_dir)

            if flips > max_flips:
                max_flips = flips
                best_move = move_str
            elif flips == max_flips and random.random() < 0.5:
                best_move = move_str

        return best_move if possible_moves else None

    def _ai_hard(self, possible_moves):
        if not possible_moves:
            return None

        best_move = None
        best_score = -float('inf')

        for move in possible_moves:
            temp_game = OthelloGame(
                board_str="".join("".join(row) for row in self.board),
                current_token=self.ai_token,
                history=[item[:] for item in self.history],
                ai_difficulty=self.ai_difficulty,
                verbose=False,
                human_token=self.human_token
            )
            if temp_game.make_move(move, self.ai_token):
                score = self._minimax(temp_game, 5, -float('inf'), float('inf'), False) # Depth 5 for example
                if score > best_score:
                    best_score = score
                    best_move = move
                elif score == best_score and random.random() < 0.5:
                    best_move = move
        return best_move

    def _evaluate_board(self, board_state, player_token):
        opponent_token = self.human_token if player_token == self.ai_token else self.ai_token
        player_count = sum(row.count(player_token) for row in board_state.board)
        opponent_count = sum(row.count(opponent_token) for row in board_state.board)
        return player_count - opponent_count

    def _minimax(self, game_state, depth, alpha, beta, maximizing_player):
        if depth == 0 or game_state.check_game_over():
            return self._evaluate_board(game_state, self.ai_token if maximizing_player else self.human_token)

        current_player = game_state.current_token
        possible_moves = game_state.get_possible_moves(current_player)

        if not possible_moves:
            # No moves for current player, try the other player
            opponent_token = self.human_token if current_player == self.ai_token else self.ai_token
            opponent_moves = game_state.get_possible_moves(opponent_token)
            if not opponent_moves:
                return self._evaluate_board(game_state, self.ai_token if maximizing_player else self.human_token) # No moves for either
            else:
                # Switch player and recurse
                temp_game = OthelloGame(
                    board_str="".join("".join(row) for row in game_state.board),
                    current_token=opponent_token,
                    history=[item[:] for item in game_state.history],
                    ai_difficulty=self.ai_difficulty,
                    verbose=False,
                    human_token=self.human_token
                )
                return self._minimax(temp_game, depth - 1, alpha, beta, not maximizing_player)

        if maximizing_player:
            max_eval = -float('inf')
            for move in possible_moves:
                temp_game = OthelloGame(
                    board_str="".join("".join(row) for row in game_state.board),
                    current_token=current_player,
                    history=[item[:] for item in game_state.history],
                    ai_difficulty=self.ai_difficulty,
                    verbose=False,
                    human_token=self.human_token
                )
                if temp_game.make_move(move, current_player):
                    eval = self._minimax(temp_game, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for move in possible_moves:
                temp_game = OthelloGame(
                    board_str="".join("".join(row) for row in game_state.board),
                    current_token=current_player,
                    history=[item[:] for item in game_state.history],
                    ai_difficulty=self.ai_difficulty,
                    verbose=False,
                    human_token=self.human_token
                )
                if temp_game.make_move(move, current_player):
                    eval = self._minimax(temp_game, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval

def main():
    board_str_arg = None
    player_token_arg = None
    ai_difficulty_arg = "hard"
    verbose_arg = False
    moves_arg = []

    if sys.argv[1:]:
        arg_str = " ".join(sys.argv[1:])
        board_match = re.search(r"([XO\.]){64}", arg_str.upper())
        if board_match:
            board_str_arg = board_match.group(0)
            arg_str = arg_str.replace(board_match.group(0), "").strip()

        token_match = re.search(r"[XO]", arg_str.upper())
        if token_match:
            player_token_arg = token_match.group(0)
            arg_str = arg_str.replace(token_match.group(0), "").strip()

        difficulty_match = re.search(r"(EASY|MEDIUM|HARD)", arg_str.upper())
        if difficulty_match:
            ai_difficulty_arg = difficulty_match.group(0).lower()
            arg_str = arg_str.replace(difficulty_match.group(0), "").strip()

        if re.search(r"[Vv]", arg_str):
            verbose_arg = True
            arg_str = re.sub(r"[Vv]", "", arg_str).strip()

        move_matches = re.findall(r"[A-H][1-8]", arg_str.upper())
        if move_matches:
            moves_arg.extend(move_matches)

    human_token = input("Choose your token (X or O): ").upper()
    while human_token not in ["X", "O"]:
        print("Invalid token. Please choose X or O.")
        human_token = input("Choose your token (X or O): ").upper()

    difficulty = input("Choose AI difficulty (easy, medium, hard): ").lower()
    while difficulty not in ["easy", "medium", "hard"]:
        print("Invalid difficulty. Please choose easy, medium, or hard.")
        difficulty = input("Choose AI difficulty (easy, medium, hard): ").lower()

    game = OthelloGame(board_str=board_str_arg, current_token="X", ai_difficulty=difficulty, verbose=verbose_arg, human_token=human_token)

    print("Starting Othello Game:")
    game.display_board(game.get_possible_moves(game.current_token))

    for move in moves_arg:
        if game.current_token == game.human_token:
            player = "Human"
        else:
            player = "AI"
        print(f"\nPre-set move: {player} ({game.current_token}) plays {move}")
        if game.make_move(move, game.current_token):
            game.display_board(game.get_possible_moves(game.current_token))
            if game.check_game_over():
                print("\nGame Over!")
                print(f"Winner: {game.get_winner()}")
                return
            game.current_token = game.ai_token if game.current_token == game.human_token else game.human_token
        else:
            print("Invalid pre-set move.")
            return

    while not game.check_game_over():
        if game.current_token == game.human_token:
            if game.play_human_turn():
                continue # Turn skipped
        else:
            if game.play_ai_turn():
                continue # Turn skipped
        game.display_board(game.get_possible_moves(game.current_token))

    print("\nGame Over!")
    print(f"Winner: {game.get_winner()}")

if __name__ == "__main__":
    main()