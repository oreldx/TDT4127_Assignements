"""
Requirements :
    - The players must give the program their moves (text based) : done
    - The program must prevent players from making illegal moves : done
    - The program must detect and signal when a player is in check : done
    - The program must detect and signal it is checkmate : done
    - If a pawn reaches the other side of the board, it will be promoted to an officer : done
Not needed :
    - stalemate
    - draw
    - en passant
    - castling
    - time control.

Piece absolute value translation :
    - blank --> 0
    - pawn ---> 1
    - knight -> 2
    - bishop -> 3
    - rook ---> 4
    - queen --> 5
    - king ---> 6

The board can be manually initialize so quickly test some scenario in the self.init_board()
A debug function is still implemented, allows you to print more clearly cases in on the self.board print_debug_board(l)
"""


class ChessGame:
    def __init__(self):
        self.pieces = ['', '♟', '♞', '♝', '♜', '♛', '♚',  '♔', '♕', '♖', '♗', '♘', '♙']
        self.players = {-1: '□ White □', 1: '■ Black ■'}
        self.board = self.init_board()

        self.display_board()
        self.player = -1
        self.game = True
        self.check_state = False

        self.launch_game()

    def launch_game(self):
        while self.game:
            # Ask for the player move
            move = self.ask_move()
            print(f"You asked for a move {move[0]} -> {move[1]}")
            # Verify if the move is legal, if not the user has to re-enter one
            while not self.check_move(move):
                print("!!!! YOUR MOVE IS ILLEGAL !!!!")
                move = self.ask_move()
            # Do the move now it's validated
            self.do_move(move)

            # If the player was in check, the only move available allowed him to get out of it
            if self.check_state:
                self.check_state = False

            # Check if the player has moved a pawn
            if abs(self.board[self.board_translator(move)[2]][self.board_translator(move)[3]]) == 1:
                # If Black (bottom side) or White (top side) available for promotion
                if (self.player == 1 and self.board_translator(move)[2] == 7) \
                        or (self.player == -1 and self.board_translator(move)[2] == 0):
                    self.do_pawn_promotion(self.board_translator(move)[2], self.board_translator(move)[3])

            # Display the board
            self.display_board()

            # Check : if the opposite king is now in some issues (in the controlled areas of the player)
            if self.get_king_position() in self.check(self.player):
                # Check if the king as any opportunity (if not any move possible, the king is trapped)
                if not self.filter_defense(self.king_move(self.get_king_position()[0], self.get_king_position()[1])):
                    print(f"The player {self.players[self.player*-1]} is in checkmate")
                    print(f"The player {self.players[self.player]} win")
                    self.game = False
                # If there is a possibility to escape during the next turn
                else:
                    print(f"The player {self.players[self.player*-1]} is in check")
                    self.check_state = True

            # Switching of player for the next round
            self.player *= -1
            print('-------------------------------------------------------')

    def ask_move(self):
        """
        Print the information for the user and retrieve input
        """
        print(f"Player team {self.players[self.player]}, it's your turn")
        print("Enter a move (first your piece, then it destination) [A2 -> A4]")
        piece = self.get_input_board('Piece :')
        destination = self.get_input_board('Destination :')
        return piece, destination

    @staticmethod
    def get_input_board(goal):
        """
        Only retrieve the user input of the correct form (letter + number)
        """
        while True:
            string = input(goal)
            # If the input respect the right conditions, it is correct : we leave the loop
            if len(string) == 2 and string[0].isalpha() and string[1].isdigit():
                break
            else:
                print('Wrong input, check format')
        return string.upper()

    def check_move(self, move):
        """
        Verify the legality of the move
            - Player move a piece
            - Player move his piece
            - If the destination is available for the piece selected
                - with the right form
                - not blocked by any piece
                - without knocking out a piece of his color
            - If the player in check, he can only move a piece that remove the current check

        """
        index = self.board_translator(move)
        piece = self.board[index[0]][index[1]]
        # exist AND player's piece
        if piece*self.player > 0:
            # If player in check, can only move his king
            # Get the piece available destinations
            possibilities = self.piece_move(piece, index[0], index[1])
            # Filter the destination to get the only valid destination
            possibilities = self.filter_attack(possibilities)
            destination = (index[2], index[3])
            # The move is correct
            if destination in possibilities:
                # If the player in check, the player should do a move to cancel it
                if self.check_state:
                    # when king move, should use the future position
                    if abs(piece) == 6:
                        x, y = index[2], index[3]
                    # else find the current position of the king
                    else:
                        x, y = 0, 0
                        for i in range(8):
                            for j in range(8):
                                if self.board[i][j]*self.player == 6:
                                    x, y = i, j
                                    break
                    # Save to reverse the temporary change to check
                    prev_p = self.board[index[0]][index[1]]
                    prev_d = self.board[destination[0]][destination[1]]
                    self.do_move(move)
                    king_still_check = (x, y) in self.check(self.player*-1)
                    self.board[index[0]][index[1]] = prev_p
                    self.board[destination[0]][destination[1]] = prev_d
                    if king_still_check:
                        return False
                return True
            # The destination for the piece is impossible
            else:
                return False
        # Player took a piece of the adversary
        else:
            return False

    def do_move(self, move):
        """
        Update the board with the move done
        """
        index = self.board_translator(move)
        self.board[index[2]][index[3]] = self.board[index[0]][index[1]]
        self.board[index[0]][index[1]] = 0

    def filter_attack(self, possibilities):
        """
        Remove the possibilities where the piece is your own piece, but keep where you can
        """
        # Adding the piece value, to get the minus or positive sign
        test_possibilites = [i + (self.board[i[0]][i[1]],) for i in possibilities]
        # Only keep the move where the target case is a ennemy or a free one
        return [(possibilitie[0], possibilitie[1]) for possibilitie in test_possibilites
                if possibilitie[2]*self.player <= 0]

    def filter_defense(self, possibilities):
        """
        Remove the possibilities where the case is not empty
        """
        test_possibilites = [i + (self.board[i[0]][i[1]],) for i in possibilities]
        return [(possibilitie[0], possibilitie[1]) for possibilitie in test_possibilites
                if possibilitie[2]*self.player == 0 or possibilitie[2] == self.player * 6 * -1]

    def piece_move(self, piece, x, y):
        """
        Return the possible cases for a type of piece
        """
        if abs(piece) == 1:
            return self.pawn_move(x, y)
        elif abs(piece) == 2:
            return self.knight_move(x, y)
        elif abs(piece) == 3:
            return self.bishop_move(x, y)
        elif abs(piece) == 4:
            return self.rook_move(x, y)
        elif abs(piece) == 5:
            return self.queen_move(x, y)
        elif abs(piece) == 6:
            return self.king_move(x, y)

    def pawn_move(self, x, y):
        """
        Return all the possible cases for the pawn selected
        """
        possibles_cases = []
        # Black
        if self.board[x][y] > 0:
            # Check if pawn not at the opposite side (need to add promotion so you can remove this cause impossible)
            # if x < 7:
            possibles_cases += [(x+1, y+1), (x+1, y-1)]
            # 2 cases move possible
            if x == 1:
                possibles_cases = [(x+1, y), (x+2,y)]
            # 1 case move
            else:
                possibles_cases = [(x+1, y)]
        # White
        if self.board[x][y] < 0:
            possibles_cases += [(x + 1, y + 1), (x + 1, y - 1)]
            if x == 6:
                possibles_cases = [(x-1, y), (x-2, y)]
            else:
                possibles_cases = [(x-1, y)]

        # Checking if the piece is out of bounds
        return [possibility for possibility in possibles_cases if 0 <= possibility[1] <= 7]

    def bishop_move(self, x, y):
        """
        Return all the possible cases for the bishop selected
        """
        possibles_cases = []
        # Get first diagonal UL to DR
        for i in range(1, 9):
            if x - i < 0 or y - i < 0:
                break
            possibles_cases.append((x - i, y - i))
            if self.board[x - i][y - i] != 0:
                break
        for i in range(1, 9):
            if x + i > 7 or y + i > 7:
                break
            possibles_cases.append((x + i, y + i))
            if self.board[x + i][y + i] != 0:
                break
        # Get second diagonal DL to DR
        for i in range(1, 9):
            if x - i < 0 or y + i > 7:
                break
            possibles_cases.append((x - i, y + i))
            if self.board[x - i][y + i] != 0:
                break
        for i in range(1, 9):
            if x + i > 7 or y - i < 0:
                break
            possibles_cases.append((x + i, y - i))
            if self.board[x + i][y - i] != 0:
                break
        return possibles_cases

    def rook_move(self, x, y):
        """
        Return all the possible cases for the rook selected
        """
        # Creating 2 array in 1 array, the first one contain the cases of the first axe and the second one...
        # zip contains an 2D-array (row + column) and the second array contains the position in the row + column
        possibles_x_y = [self.check_axe(axe, pos) for axe, pos in zip(
                                                            [
                                                                self.board[x],
                                                                [self.board[i][y] for i in range(8)]
                                                            ],
                                                            [y, x])]
        possibles_cases = []
        # Merging the 2 axes possibilities in 1 array as tuple of indexes
        for element in possibles_x_y[1]:
            possibles_cases.append((element, y))
        for element in possibles_x_y[0]:
            possibles_cases.append((x, element))
        return possibles_cases

    @staticmethod
    def check_axe(array, idx):
        """
        Return the possible index of a rook axe
        """
        cases = []
        # Take from the origin piece, until the left and right the available cases until first piece
        for left_to_right in [(idx - 1, -1, -1), (idx + 1, len(array), 1)]:
            for i in range(left_to_right[0], left_to_right[1], left_to_right[2]):
                cases.append(i)
                if array[i] != 0:
                    break
        return sorted(cases)

    def queen_move(self, x, y):
        """
        Return all the possible cases for the queen selected
        """
        return self.rook_move(x, y) + self.bishop_move(x, y)

    @staticmethod
    def knight_move(x, y):
        """
        Return all the possible cases for the knight selected
        """
        possibles_cases = []
        for i in [(x-1, y+2), (x+1, y+2), (x-1, y-2), (x+1, y-2), (x+2, y-1), (x+2, y+1), (x-2, y-1), (x-2, y+1)]:
            if 0 <= i[0] <= 7 and 0 <= i[1] <= 7:
                possibles_cases.append(i)
        return possibles_cases

    def king_move(self, x, y):
        """
        Return all the possible cases for the king selected
        """
        possibles_cases = []
        for i in [(x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1), (x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]:
            if 0 <= i[0] <= 7 and 0 <= i[1] <= 7:
                possibles_cases.append(i)
        possibles_cases = list(set(possibles_cases) - set(self.check(self.board[x][y]*-1)))
        return possibles_cases

    def check(self, player):
        """
        Return all the cases controlled by the player
        """
        possibilities = []
        for i, row in enumerate(self.board):
            for j, piece in enumerate(row):
                # Taking the opposite player pieces
                if piece*player > 0:
                    # Not the move function cause the pawn only attack != movement
                    if abs(piece) == 1:
                        # Black
                        if player > 0:
                            possibilities += [(i+1, j-1), (i+1, j+1)]
                        # White
                        else:
                            possibilities += [(i-1, j-1), (i-1, j+1)]
                        possibilities = [possibility for possibility in possibilities if 0 <= possibility[1] <= 7]
                    # the king function is calling the checkmate
                    elif abs(piece) == 6:
                        for h in [(i-1, j-1), (i+1, j-1), (i-1, j+1), (i+1, j+1), (i, j-1), (i, j+1), (i-1, j), (i+1, j)]:
                            if 0 <= h[0] <= 7 and 0 <= h[1] <= 7 and self.board[h[0]][h[1]] == 0:
                                possibilities += [h]
                    else:
                        possibilities += self.piece_move(piece, i, j)
                    possibilities = self.filter_defense(possibilities)
        return list(set(possibilities))

    def get_king_position(self):
        """
        Find the king of the opposite current player
        """
        for i in range(8):
            for j in range(8):
                if self.board[i][j] * self.player * -1 == 6:
                    return i, j

    def do_pawn_promotion(self, x, y):
        print("Pawn promotion available\n1: knight\n2: bishop\n3: rook\n4: queen")
        new_piece = int(input("Choose the upgrade (enter the number): "))
        while 0 >= new_piece or new_piece >= 5:
            new_piece = int(input("Choose the upgrade (enter the number): "))
        self.board[x][y] = (new_piece+1)*self.player

    def display_board(self):
        """
        Print the current board with the chess chars
        """
        display = ""
        for num, row in enumerate(self.board):
            line = str(8-num) + '  '
            for piece in row:
                if piece != 0:
                    line += f"[{self.pieces[piece]}]"
                else:
                    line += '[ ]'
            display += line + '\n'
        display += "  [A] [B] [C] [D] [E] [F] [G] [H]"
        print(display)

    @staticmethod
    def board_translator(positions):
        """
        Convert a couple string LETTER + NUMBER into the real index of the board
        """
        index = ()
        for position in positions:
            col = ord(position[0]) - 65
            row = 8 - int(position[1])
            index += (row, col)
        return index

    @staticmethod
    def init_board():
        """
        Initialize the board 2D-array, can be used to manually configure the board for special tests
        """
        board = [[4, 2, 3, 5, 6, 3, 2, 4], [1 for _ in range(8)]]
        for i in range(2):
            board.append([0 for _ in range(8)])
        board += [[board[i][j]*-1 for j in range(8)] for i in range(3, -1, -1)]

        # Input a specific board configuration here
        # board = [
        #     [0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 0, -6, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 4, 0, 0, 0, 0, 0],
        #     [0, 0, 1, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0],
        # ]

        return board

    @staticmethod
    def print_debug_board(board):
        """
        By passing in the input a list of cases, you can print them into a board shape to easily understand it
        """
        for i in range(8):
            line = ''
            for j in range(8):
                if (i, j) in board:
                    line += ' ■ '
                else:
                    line += ' □ '
            print(line)


if __name__ == '__main__':
    ChessGame()
