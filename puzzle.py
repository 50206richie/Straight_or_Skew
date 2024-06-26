"""
This is the module that contains objects for the puzzle
"""
import os
from collections import Counter
from typing import Union, List, Tuple
import random
import json

Shape = int
SHAPES = [EMPTY, SQUARE, DIAMOND, CIRCLE] = range(4)
# SHAP = [■⬩⬥, SQUARE, DIAMOND, CIRCLE] = range(4)
SHAPE_SYMBOL = ['_', '▪', '⬩', '●']  # https://www.alt-codes.net/
# SHAPE_SYMBOL = ['_', 'S', 'D', 'C']
STRAIGHTS = [VERTICAL, HORIZONTAL] = range(2)
DIRECTIONS = [N, E, S, W] = range(4)  # Used in determine oblique clue directions


# OBLIQUES = [NW, NE, SE, SW] = range(4, 8)  # heading direction (from cell)


def get_shape_str(shape: Shape) -> str:
    """Returns the symbol of the shape"""
    return SHAPE_SYMBOL[shape]


class Cell:
    """Cell
    >>> c = Cell(shape=SQUARE)
    >>> print(f'{c}')
    ▪
    """

    def __init__(self, row=None, col=None, shape=EMPTY):
        self.row = row
        self.col = col
        self.shape = shape

    def __str__(self):
        return get_shape_str(self.shape)


class Board:
    """This is a board class
    >>> b = Board(counter={SQUARE: 5, DIAMOND: 3, CIRCLE: 1})
    >>> print(b)
    This is a size 3 board:
    COUNTER: Square: 5, Diamond: 3, Circle: 1
    0000000
    0_ _ _0
    0     0
    0_ _ _0
    0     0
    0_ _ _0
    0000000
    <BLANKLINE>
    """

    def __init__(self, counter: dict | None, straight_clues, oblique_clues, size=3):
        self.size = size
        self.grid = [[Cell(row=row, col=col, shape=EMPTY) for col in range(size)] for row in range(size)]
        self.counter = counter
        self.straight = [[0 for _ in range(size)] for _ in range(2)]  # [VERTICAL, HORIZONTAL]
        self.oblique = [[0 for _ in range(size)] for _ in range(4)]
        self.straight_clues = straight_clues
        self.oblique_clues = oblique_clues
        if self.counter is None and self.straight_clues is None and self.oblique_clues is None:
            # Generation
            self.counter = {SQUARE: 0, DIAMOND: 0, CIRCLE: 0}
            self.straight_clues = [[0 for _ in range(size)] for _ in range(2)]
            self.oblique_clues = [[0 for _ in range(size)] for _ in range(4)]
        # elif self.counter or self.straight_clues is None or self.oblique_clues is None:
        #     raise ValueError('Clues Missing')
        """
        oblique is the diagonals which separated into 4 sides
        xxxo
        a  o
        a  o
        abbb
        """

    def __str__(self):
        header = f'This is a size {self.size} board:\n'
        shape_counts = (f'COUNTER: Square: {self.counter[SQUARE]}, '
                        f'Diamond: {self.counter[DIAMOND]}, '
                        f'Circle: {self.counter[CIRCLE]}\n')
        grid_str = ''
        for i in range(self.size):
            grid_str += f'{self.oblique_clues[N][i]} {self.straight_clues[VERTICAL][i]} '
        grid_str += f'{self.oblique_clues[E][0]}\n'
        for i in range(self.size):
            grid_str += f'{self.straight_clues[HORIZONTAL][i]} '
            for j in range(self.size):
                if j < self.size - 1:
                    grid_str += f'{self.grid[i][j]}   '
                else:
                    grid_str += f'{self.grid[i][j]}'
            grid_str += f' {self.straight_clues[HORIZONTAL][i]}\n'
            if i < self.size - 1:
                grid_str += (f'{self.oblique_clues[W][(self.size - 1) - i]}'
                             f'{" " * ((self.size * 2 - 1) * 2 + 1)}{self.oblique_clues[E][i + 1]}\n')
        grid_str += f'{self.oblique_clues[W][0]}'
        for i in range(self.size):
            grid_str += f' {self.straight_clues[VERTICAL][i]} {self.oblique_clues[S][(self.size - 1) - i]}'
        board_str = header + shape_counts + grid_str + '\n'
        return board_str

    def is_full(self) -> bool:
        """Check if grid is full"""
        for r in range(len(self.grid)-1, -1, -1):
            for c in range(len(self.grid)-1, -1, -1):
                if self.grid[r][c].shape == EMPTY:
                    return False
        return True

    def get_next_empty_cell(self) -> Union[Cell, None]:
        """As title"""
        for ci in self.grid:
            for cj in ci:
                if cj.shape == EMPTY:
                    return cj
        return None

    def modify_oblique_clue(self, di_list: List[Tuple], mode: str) -> None:
        """
        As title
        :param di_list: A list of direction and index of oblique clues, e.g., [(N, 0), (E, 0), (S, 0), (W, 0)]
        :param mode: to add (fill puzzle) or subtract (backtrack)
        """
        for d, i in di_list:
            match mode:
                case '+':
                    self.oblique[d][i] += 1
                case '-':
                    self.oblique[d][i] -= 1

    def find_cell_obliques(self, cell: Cell) -> List[Tuple]:
        """As title"""
        rc_diff = cell.row - cell.col
        rc_sum = cell.row + cell.col
        c1 = abs(rc_diff)
        c2 = self.size - c1
        c3 = abs(rc_sum - (self.size - 1))
        c4 = self.size - c3
        obliques = None
        # Antidiag is adding, Diagonal is subtracting
        if rc_diff > 0:
            # In SW corner
            if rc_sum < self.size - 1:
                # W
                obliques = [(N, c4), (S, c1), (W, c3), (W, c2)]
            elif rc_sum > self.size - 1:
                # S
                obliques = [(E, c3), (S, c1), (S, c4), (W, c2)]
            elif rc_sum == self.size - 1:
                # On antidiag line
                obliques = [(E, 0), (S, c1), (W, 0), (W, c2)]
        elif rc_diff < 0:
            # In NE corner
            if rc_sum < self.size - 1:
                # N
                obliques = [(N, c1), (N, c4), (E, c2), (W, c3)]
            elif rc_sum > self.size - 1:
                # E
                obliques = [(N, c1), (E, c3), (E, c2), (S, c4)]
            elif rc_sum == self.size - 1:
                # On antidiag line
                obliques = [(N, c1), (E, 0), (E, c2), (W, 0)]
        elif rc_diff == 0:
            # On Diagonal Line
            if rc_sum < self.size - 1:
                # NW
                obliques = [(N, 0), (N, c4), (S, 0), (W, c3)]
            elif rc_sum > self.size - 1:
                # SE
                obliques = [(N, 0), (E, c3), (S, 0), (S, c4)]
            elif rc_sum == self.size - 1:
                # Mid
                obliques = [(N, 0), (E, 0), (S, 0), (W, 0)]
        return obliques

    def count_straight_shapes(self, vertical: bool, line: int) -> int:
        """NOT USED Count the shapes in a straight line
        :param vertical: True if counting in a vertical direction, else false
        :param line: the nth line that would be counted
        """
        shapes = 0
        if vertical:
            for i in range(self.size):
                if self.grid[i][line].shape == SQUARE or self.grid[i][line].shape == CIRCLE:
                    shapes += 1
        elif not vertical:
            for i in range(self.size):
                if self.grid[line][i].shape == SQUARE or self.grid[line][i].shape == CIRCLE:
                    shapes += 1
        return shapes

    def check_straight_line_shapes(self, cell: Cell) -> bool:
        """As title"""
        cell_shape_straight: int = 0 if cell.shape == DIAMOND else 1
        line_valid = True
        if cell.col == self.size - 1:
            if self.straight[HORIZONTAL][cell.row] + cell_shape_straight != self.straight_clues[HORIZONTAL][cell.row]:
                line_valid = False
        if cell.row == self.size - 1:
            if self.straight[VERTICAL][cell.col] + cell_shape_straight != self.straight_clues[VERTICAL][cell.col]:
                line_valid = False
        return line_valid

    def is_valid_puzzle(self, cell: Cell) -> bool:
        """
        Let shape radiate to the edge to add, if invalid, subtract and return False
        :param cell:
        :return:
        """
        # Check if cell is last cell in row or col, and see if clue matches
        if cell.col == self.size - 1 or cell.row == self.size - 1:
            clues_match: bool = self.check_straight_line_shapes(cell=cell)
            if clues_match is False:
                return False

        if cell.shape == SQUARE or cell.shape == CIRCLE:
            if self.straight[VERTICAL][cell.col] + 1 > self.straight_clues[VERTICAL][cell.col]:
                return False
            if self.straight[HORIZONTAL][cell.row] + 1 > self.straight_clues[HORIZONTAL][cell.row]:
                return False

        if cell.shape == DIAMOND or cell.shape == CIRCLE:
            result_oblique = True
            obliques_list: List[Tuple] = self.find_cell_obliques(cell=cell)  # e.g., [(N, 0), (E, 0), (S, 0), (W, 0)]
            if obliques_list is None:
                raise ValueError('obliques_list is None')
            for d, i in obliques_list:
                result_oblique &= (self.oblique[d][i] + 1 <= self.oblique_clues[d][i])
                if not result_oblique:
                    return False
            self.modify_oblique_clue(di_list=obliques_list, mode='+')

        # If valid, add to edge numbers
        if cell.shape == SQUARE or cell.shape == CIRCLE:
            self.straight[VERTICAL][cell.col] += 1
            self.straight[HORIZONTAL][cell.row] += 1
        return True

    def place_shape(self, cell: Cell):
        """Place a shape into the given cell"""
        self.grid[cell.row][cell.col] = cell

        if not self.is_valid_puzzle(cell=cell):
            # self.grid[cell.row][cell.col].shape = EMPTY  THIS LINE WRONG, CAUSES BACKTRACK MALFUNCTION
            return False

        self.counter[cell.shape] -= 1
        return True


class Solver(Board):
    """Solver"""

    def __init__(self, counter: dict, straight_clues, oblique_clues, size=3):
        super().__init__(counter, straight_clues, oblique_clues, size)
        self.solutions: List = []
        self.moves: List[Cell] = []

    def backtrack(self) -> None:
        """backtrack"""
        last_cell: Cell | None = self.moves.pop() if len(self.moves) else None
        if last_cell is None:
            # print('Backtracked all the way to beginning. No more solutions.')
            raise ValueError('Backtracked all the way to beginning. No more solutions.')
        self.counter[last_cell.shape] += 1
        # print(f'Popped last cell is: {last_cell} at ({last_cell.row}, {last_cell.col}), now board:')

        # Subtract edge numbers
        if last_cell.shape == SQUARE or last_cell.shape == CIRCLE:
            self.straight[VERTICAL][last_cell.col] -= 1
            self.straight[HORIZONTAL][last_cell.row] -= 1
        if last_cell.shape == DIAMOND or last_cell.shape == CIRCLE:
            obliques_list: List[Tuple] = self.find_cell_obliques(cell=last_cell)
            self.modify_oblique_clue(di_list=obliques_list, mode='-')

        # Set last cell shape to EMPTY
        tmp = self.grid[last_cell.row][last_cell.col].shape
        self.grid[last_cell.row][last_cell.col].shape = EMPTY
        # print(self)
        self.grid[last_cell.row][last_cell.col].shape = tmp

        # Try placing a shape
        while True:
            if last_cell.shape in SHAPES[SQUARE:-1] and self.counter[last_cell.shape + 1]:
                last_cell.shape += 1
                placed = self.place_shape(cell=last_cell)
                if placed:
                    self.moves.append(last_cell)
                    # if not len(self.solutions):
                    #     print(f'Backtracked and Placed move {len(self.moves)}: {last_cell.shape}\n{self}\n')
                    break
                else:
                    continue
            elif last_cell.shape in SHAPES[SQUARE:-2] and self.counter[last_cell.shape + 2]:  # Square to Circle
                last_cell.shape += 2
                placed = self.place_shape(cell=last_cell)
                if placed:
                    self.moves.append(last_cell)
                    # if not len(self.solutions):
                    #     print(f'Backtracked and Placed move {len(self.moves)}: {last_cell.shape}\n{self}\n')
                    break
                else:
                    continue
            else:
                last_cell.shape = EMPTY
                self.backtrack()
                break
        return

    def find_solutions(self) -> int:
        """
        The method to solve the puzzle
        :return: The number of solutions
        """
        while not self.is_full():
            try:
                cell = self.get_next_empty_cell()
                if cell is None:
                    print("Didn't get the next cell")
                    break

                placed = False
                for s in SHAPES[SQUARE:]:
                    if self.counter[s]:
                        cell.shape = s
                        placed = self.place_shape(cell=cell)
                        if placed:
                            self.moves.append(cell)
                            # if not len(self.solutions):
                            #     print(f'Placed move {len(self.moves)}: {cell.shape}\n{self}\n')
                            break
                if not placed:
                    cell.shape = EMPTY
                    self.backtrack()

                if self.is_full():
                    # Solved
                    solution = str(self)
                    self.solutions.append(solution)
                    print(f'\nGOT SOLUTION #{len(self.solutions)}:\n {solution}')
                    if len(self.solutions) > 1:
                        # Multiple Solutions
                        break
                    # Backtrack to see if there are multiple answers
                    self.backtrack()
            except ValueError as ex:
                if ex.args[0] == 'Backtracked all the way to beginning. No more solutions.':
                    break
                else:
                    raise ex  # something unexpected happened.
        return len(self.solutions)


class Generator(Solver):
    """Generator"""

    def __init__(self, counter=None, straight_clues=None, oblique_clues=None, size=3):
        super().__init__(counter, straight_clues, oblique_clues, size)
        self.answer_grid: list[list] = [[0 for _ in range(self.size)] for _ in range(self.size)]

    def generate_seq(self) -> list[int]:
        """
        >>> g = Generator()
        >>> s = g.generate_seq()
        >>> len(s) == g.size*g.size
        True
        """
        # todo: change weights for different difficulties
        # Ensure every shape exists
        while True:
            seq = random.choices(population=range(1, 4), weights=[0.35, 0.35, 0.3], k=self.size * self.size)
            if len(Counter(seq)) == 3:
                break
        return seq

    def generate_shape_counter(self, seq: list):
        """As title
        >>> g = Generator()
        >>> g.generate_shape_counter([3, 3, 2, 1, 2, 2, 3, 3, 3])
        >>> g.counter == {CIRCLE: 5, DIAMOND: 3, SQUARE: 1}
        True
        """
        self.counter = dict(Counter(seq))

    def generate_grid_and_counter(self):
        """
        As title
        """
        seq = self.generate_seq()
        # seq = [1, 2, 2, 2, 1, 3, 3, 3, 3]
        self.generate_shape_counter(seq=seq)
        for r in range(self.size):
            for c in range(self.size):
                self.answer_grid[r][c] = seq[r * self.size + c]
                self.grid[r][c].shape = seq[r * self.size + c]

    def generate_clues(self):
        """Counts the total number of shapes of the clue number position"""
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c].shape == SQUARE or self.grid[r][c].shape == CIRCLE:
                    self.straight_clues[VERTICAL][c] += 1
                    self.straight_clues[HORIZONTAL][r] += 1

                if self.grid[r][c].shape == DIAMOND or self.grid[r][c].shape == CIRCLE:
                    obliques_list: List[Tuple] = self.find_cell_obliques(cell=self.grid[r][c])
                    # print(f'oblique_list is {obliques_list}')
                    for d, i in obliques_list:
                        self.oblique_clues[d][i] += 1

    def generate_board(self) -> bool:
        """As title"""
        self.generate_grid_and_counter()
        # initalize grid clues
        self.generate_clues()
        # Find Solutions
        # answer = self.__str__()
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c].shape = EMPTY

        print(f'Generated grid!\n{self}\n Finding solutions...')
        solutions = self.find_solutions()

        if solutions != 1:
            print(f'Have mutliple ({solutions}) solutions, regenerating new puzzle!\n')
        else:
            print(f'Found the only {solutions} solution!\n')
        return True if solutions == 1 else False


def generate_valid_puzzle(size=3) -> Generator:
    """Generates a valid board"""
    while True:
        generator = Generator(size=size)
        generated: bool = generator.generate_board()
        if generated:
            return generator


def store_board_to_json(gen_puzzle: Generator):
    """As title"""
    if os.path.exists('puzzle_data.json'):
        with open('puzzle_data.json', 'r') as file:
            data = json.load(file)
    else:
        data = {}

    puzzle_size_str = str(gen_puzzle.size)
    # Add new puzzle to file
    puzzle_id = len(data[puzzle_size_str]) if puzzle_size_str in data else 0
    new_puzzle = {
        'id': puzzle_id,
        'data': {
            'size': gen_puzzle.size,
            'counter': gen_puzzle.counter,
            'clue_s': {
                VERTICAL: gen_puzzle.straight_clues[VERTICAL],
                HORIZONTAL: gen_puzzle.straight_clues[HORIZONTAL]
            },
            'clue_o': {
                N: gen_puzzle.oblique_clues[N],
                E: gen_puzzle.oblique_clues[E],
                S: gen_puzzle.oblique_clues[S],
                W: gen_puzzle.oblique_clues[W]
            },
            'answer': gen_puzzle.answer_grid
        }
    }
    if puzzle_size_str not in data:
        data[puzzle_size_str] = []
    data[puzzle_size_str].append(new_puzzle)

    # Store it back to json
    with open('puzzle_data.json', 'w') as file:
        json.dump(data, file, indent=4)


if __name__ == '__main__':
    """For generating and storing new puzzles to json"""
    generated_puzzle: Generator = generate_valid_puzzle(size=5)
    store_board_to_json(generated_puzzle)
    print(f'Generated valid puzzle:\n{generated_puzzle}')
    # todo: try multithread?
    # todo: gui
