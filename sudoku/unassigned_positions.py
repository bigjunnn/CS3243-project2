import sys
import copy
from collections import defaultdict

# Running script: given code can be run with the command:
# python file.py ./path/to/init_state.txt ./output/output.txt

import collections

class Sudoku(object):
    counter = 0

    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = copy.deepcopy(puzzle) # self.ans is a list of lists

    def solve(self):
        # TODO: Write your code here
        state = self.puzzle
        unassigned_positions = self.get_unassigned_positions(state)
        domains = self.get_initial_domains(state)
        deque = self.make_arc_deque(self.get_assigned_positions(state))
        domains = self.arc_consistency(deque, domains)
        if self.backtrack(domains, unassigned_positions):
            self.ans = self.get_state_from_domain(domains)

        print("Backtrack was called {} times".format(self.counter))

        # self.ans is a list of lists
        return self.ans

    # excludes assigned variables
    def get_initial_domains(self, state):
        initial_domains = {}

        for row in range(9):
            for col in range(9):
                value = state[row][col]
                if value == 0:
                    # initial_domains[(row, col)] = [state[row][col]]
                    initial_domains[(row, col)] = set([1, 2, 3, 4, 5, 6, 7, 8, 9])
                else:
                    initial_domains[(row, col)] = set([value])
        return initial_domains

    def get_assigned_positions(self, state):
        assigned_positions = []

        for row in range(9):
            for col in range(9):
                position = (row, col)
                value = state[row][col]
                if value != 0:
                    assigned_positions.append(position)

        return assigned_positions

    # `assignment` is the same as state, as it is represented as a 9x9 2D matrix
    # `domains` is a dictionary. Key is position. Value is a set of allowable sudoku values.
    def backtrack(self, domains, unassigned_positions):
        self.counter += 1
        if not unassigned_positions:
            return True

        position = unassigned_positions.pop() # position is a tuple of (row, col)

        for value in self.identity_domain(position, domains):
            # if self.is_value_consistent(value, position, state):
            # state[row][col] = value # assignment
            removed = defaultdict(set)
            original_position_domain = domains[position] # cannot add into `removed` as removed is strictly for inference
            domains[position] = set([value])
            # `inferences` are reduced domains of positions
            inferences = self.arc_consistency(self.make_arc_deque([position]), domains, removed)
            if inferences != []: # not failure
                new_domains = inferences
                result = self.backtrack(new_domains, unassigned_positions)
                # successful result is a complete assignment
                # failure is an empty list
                if result != False: # not failure
                    return result
            # restoring inferences
            self.restore_removed_domains(domains, removed)
            domains[position] = original_position_domain
        # state[row][col] = 0
        unassigned_positions.append(position)
        return False # failure

    def restore_removed_domains(self, domains, removed):
        for position in removed:
            domains[(position)] |= removed[(position)]

    def is_assignment_complete(self, assignment):
        is_complete = True
        for row in range(0, 9):
            for col in range(0, 9):
                if assignment[row][col] == 0:
                    is_complete = False

        return is_complete

    def first_unassigned_variable(self, state):
        for row in range(9):
            for col in range(9):
                if state[row][col] == 0:
                    return (row, col)

    # returns the unassigned position (row, col)
    # that has the fewest allowable values in its domain
    def most_constrained_variable(self, state, domains):
        # initialise
        smallest_domain_size = 10
        position = (0, 0)

        # unassigned_positions = self.get_unassigned_positions(state)
        # for position in unassigned_positions:

        for row in range(0, 9):
            for col in range(0, 9):
                other_position = (row, col)
                if state[row][col] == 0:
                    domain_length = len(domains[(row, col)])
                    if domain_length < smallest_domain_size:
                        smallest_domain_size = domain_length
                        position = other_position
                    # elif domain_length == smallest_domain_size:
                    #     # most constraining variable as tie breaker
                    #     if self.get_degree(state, position) < self.get_degree(state, other_position):
                    #         position = other_position
        return position

    # returns the unassigned position (row, col) that has the highest degree.
    # Intuitively, such a tile has the most empty tiles in its row, column, and small square.
    def most_constraining_variable(self, state):
        # initialise
        position = (-1, -1)
        max_degree = -1

        for row in range(9):
            for col in range(9):
                if (state[row][col] == 0):
                    current_degree = self.get_degree(state, (row, col))
                    if current_degree > max_degree:
                        position = (row, col)
                        max_degree = current_degree
        return position

    def get_degree(self, state, variable):
        return len(self.get_unassigned_neighbours(state, variable))

    def get_unassigned_neighbours(self, state, variable):
        unassigned_neighbours = []
        neighbours = self.get_neighbours(variable)
        for neighbour in neighbours:
            if state[neighbour[0]][neighbour[1]] == 0:
                unassigned_neighbours.append(neighbour)
        return unassigned_neighbours

    def identity_domain(self, variable, domains):
        # return its domain
        row = variable[0]
        col = variable[1]
        return domains[(row, col)]

    def least_constraining_value(self, variable, domains):
        # initialise
        neighbours = self.get_neighbours(variable)  # rows, columns, and small square
        value_count_tuples = []
        (row, col) = variable
        values = domains[(row, col)]

        for value in values:
            count = 0
            for neighbour in neighbours:
                if value in domains[neighbour]:
                    count += 1
                # count += self.count_valid_values(neighbour_domain, value)
            value_count_tuples.append((value, count))

        sorted_by_count = sorted(value_count_tuples, key=lambda tup: tup[1])
        result = [value[0] for value in sorted_by_count]
        return result

    # returns a list of the variable's neighbours (assigned or not).
    def get_neighbours(self, variable):
        neighbours = []
        (row, col) = variable

        for i in range(0, 9):
            if i != row:
                neighbours.append((i, col))
            if i != col:
                neighbours.append((row, i))

        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for current_row in range(start_row, start_row + 3):
            for current_col in range(start_col, start_col + 3):
                if (current_col == col or current_row == row): continue # exclude same row and col
                else: neighbours.append((current_row, current_col))

        return neighbours

    def count_valid_values(self, neighbour_domain, value):
        count = 0
        for val in neighbour_domain:
            if val != value:
                count += 1
        return count

    # checks whether a variable-value assignment is consistent with the current state
    # position is a tuple (row, col)
    def is_value_consistent(self, value, position, state):
        (row, col) = position

        for i in range(0, 9):
            if i != row and state[i][col] == value:
                return False
            if i != col and state[row][i] == value:
                return False

        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for current_row in range(start_row, start_row + 3):
            for current_col in range(start_col, start_col + 3):
                if current_col == col or current_row == row: continue # exclude same row and col
                elif state[current_row][current_col] == value:
                    return False
        return True

    def arc_consistency(self, deque, domains, removed = defaultdict(set)):
        while deque: # true if not empty
            (X, Y) = deque.popleft()
            if self.revise(domains, X, Y, removed):
                if len(domains[X]) == 0: return []
                neighbours = self.get_neighbours(X)
                neighbours.remove(Y)
                for Z in neighbours:
                    deque.append((Z, X))
        return domains

    # Important: The only constraints relevant are the ones FROM the assigned variables to its neighbours
    # (ie the neighbour's domain will be revised). The assigning of the value to a variable will only limit
    # it's neighbours' domain.
    # This criteria is not the same as the constraints from unassigned variables to its neighbours.
    def make_arc_deque(self, assigned_positions):
        deque = collections.deque()

        for position in assigned_positions:
            neighbours = self.get_neighbours(position)
            for neighbour in neighbours:
                deque.append((neighbour, position))
        return deque

    # revises domain of X; domain is mutated.
    def revise(self, domains, X, Y, removed):
        revised = False
        # removed = [] # dictionary-set

        for x in set(domains[X]): # copy domains to prevent set changed size during iteration
            for y in domains[Y]:
                is_satisfied = reduce(lambda prev, y: prev or x != y, domains[Y], False)
                if not is_satisfied:
                    removed[X].add(x)
                    domains[X].remove(x)
                    revised = True

        # for x in removed[X]: # prevent set from changing size during iteration
        #     domains[X].remove(x)
        return revised

    def forward_checking(self, domains, position, value):
        domains = self.reduce_vertical_cells_domains(domains, position, value)
        if domains == []:
            return []
        domains = self.reduce_horizontal_cells_domains(domains, position, value)
        if domains == []:
            return []
        domains = self.reduce_small_square_domains(domains, position, value)
        if domains == []:
            return []
        else:
            return domains

    # remove `value` from all domains of the column of `position`, except at `position` itself
    def reduce_vertical_cells_domains(self, domains, position, value):
        row_number = position[0]
        column_number = position[1]
        for row in range(0, 9):
            if row != row_number and value in domains[row][column_number]:
                domains[(row, column_number)].remove(value)
                if domains[(row, column_number)] == []:
                    return [] # failure
        return domains

    # remove `value` from all domains of the row of `position`, except at `position` itself
    def reduce_horizontal_cells_domains(self, domains, position, value):
        row_number = position[0]
        column_number = position[1]
        for col in range(0, 9):
            if col != column_number and value in domains[(row_number, col)]:
                domains[(row_number, col)].remove(value)
                if domains[(row_number, col)] == []:
                    return [] #failure
        return domains

    # remove `value` from all domains of cells in the 3x3 square containing `position`,
    # except at `position` itself
    def reduce_small_square_domains(self, domains, position, value):
        start_row = (position[0] // 3) * 3
        start_col = (position[1] // 3) * 3
        for row in range(start_row, start_row + 3):
            for col in range(start_col, start_col + 3):
                if (not (row, col) == position) and value in domains[(row, col)]:
                    domains[(row, col)].remove(value)
                    if domains[(row, col)] == []:
                        return [] # failure
        return domains

    # UTILS
    def create_2D_array(self, row, col):
        return [[0 for x in range(col)] for y in range(row)]

    def get_start_row_col(self, row, col):
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        return start_row, start_col

    def get_unassigned_positions(self, state):
        unassigned_positions = []
        for row in range(9):
            for col in range(9):
                unassigned_position = (row, col)
                if state[row][col] == 0:
                    unassigned_positions.append(unassigned_position)
        return unassigned_positions

    def get_state_from_domain(self, domains):
        final_state = self.create_2D_array(9, 9)

        for position in domains:
            (row, col) = position
            domain = domains[position]
            assert len(domain) == 1, "size of domain must be 1"
            final_state[row][col] = domain.pop()

        return final_state

    # Returns a list of tuples which specify 1) which cell wherein x and y differs
    # 2) elements of x in the cell and 3) elements of y in the cell.
    # If debug mode is on, prints 1), 2), and 3).
    def debug_arrays(self, x, y):
        result = []
        for i in range(9):
            for j in range(9):
                if x[i][j] != y[i][j]:
                    # if debug:
                    #     print("Cell differs at {} {}".format(i, j))
                    #     print("Array x: {}".format(x[i][j]))
                    #     print("Array y: {}".format(y[i][j]))
                    result.append(((i, j),
                                   x[i][j],
                                   y[i][j]))
        return result

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")
