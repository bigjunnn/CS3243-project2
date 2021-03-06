import sys
import time
from collections import defaultdict

# Running script: given code can be run with the command:
# python file.py ./path/to/init_state.txt ./output/output.txt

import collections


class Sudoku(object):
    counter = 0
    adjacency_dict = {}

    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle  # self.puzzle is a list of lists
        # self.ans = copy.deepcopy(puzzle) # self.ans is a list of lists

    def solve(self):
        # TODO: Write your code here
        state = self.puzzle
        self.adjacency_dict = self.get_adjacency_dict(state)
        unassigned_positions = self.get_unassigned_positions(state)
        domains = self.preprocess_domains(state)

        # Preprocess domains with AC3
        deque = self.make_arc_deque(self.get_assigned_positions(state), unassigned_positions)
        domains = self.forward_checking_singleton(deque, domains)
        self.ans = self.backtrack(state, domains, unassigned_positions)
        assert self.ans != [], "Did not solve puzzle."

        print("Backtrack was called {0} times".format(self.counter))

        # self.ans is a list of lists
        return self.ans

    # excludes assigned variables
    def preprocess_domains(self, state):
        initial_domains = {}

        for row in range(9):
            for col in range(9):
                value = state[row][col]
                if value == 0:
                    # initial_domains[(row, col)] = [state[row][col]]
                    initial_domains[(row, col)] = set(range(1,10))
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
    def backtrack(self, state, domains, unassigned_positions):
        self.counter += 1
        if not unassigned_positions:
            return state

        variable = self.most_constrained_variable(unassigned_positions, domains)
        # variable = self.first_unassigned_variable(unassigned_positions)
        row = variable[0]
        col = variable[1]
        removed = defaultdict(set)

        for value in self.least_constraining_value(variable, domains):
            if self.is_value_consistent(value, variable, state):
                state[row][col] = value  # assignment
                original_variable_domain = domains[variable]  # cannot add into `removed` as removed is strictly for inference
                domains[variable] = set([value])

                # `inferences` are reduced domains of variables
                ##### Variant 1 - MAC ######
                # if self.mac(self.make_arc_deque([variable], unassigned_positions), domains, removed):  # not failure
                ##### Variant 2 - FC ######
                if self.forward_checking(domains, variable, value, removed):
                ##### Variant 3 - FC singleton ######
                # if self.forward_checking_singleton(self.make_arc_deque([variable], unassigned_positions), domains, removed):
                    result = self.backtrack(state, domains, unassigned_positions)
                    # successful result is a complete assignment
                    # failure is an empty list
                    if result:  # not failure
                        return result
                # restoring inferences
                self.restore_removed_domains(domains, removed)
                domains[variable] = original_variable_domain
            state[row][col] = 0

        assert type(variable) == tuple, "variable must be tuple"
        unassigned_positions.add(variable)
        return []  # failure

    def restore_removed_domains(self, domains, removed):
        for position in removed:
            domains[position] |= removed[position]

    def first_unassigned_variable(self, unassigned_positions):
        return unassigned_positions.pop()

    # returns the unassigned position (row, col) 
    # that has the fewest allowable values in its domain
    def most_constrained_variable(self,  unassigned_positions, domains):
        # initialise
        smallest_domain_size = 10
        result = ()

        for unassigned_position in unassigned_positions:
            domain_length = len(domains[unassigned_position])
            if domain_length < smallest_domain_size:
                result = unassigned_position
                smallest_domain_size = domain_length
            # elif domain_length == smallest_domain_size:
            #     result = self.compare_degree(unassigned_position, result, unassigned_positions)

        unassigned_positions.remove(result)
        return result

    def compare_degree(self, x, y, unassigned_positions):
        if self.get_degree(x, unassigned_positions) < self.get_degree(y, unassigned_positions):
            return y
        else:
            return x

    # Pops the unassigned position (row, col) that has the highest degree.
    # Intuitively, such a tile has the most empty tiles in its row, column, and small square.
    def most_constraining_variable(self, unassigned_positions):
        # initialise
        max_degree = -1
        result = ()

        for unassigned_position in unassigned_positions:
            current_degree = self.get_degree(unassigned_position, unassigned_positions)
            if current_degree > max_degree:
                result = unassigned_position
                max_degree = current_degree

        unassigned_positions.remove(result)
        return result

    def get_degree(self, position, unassigned_positions):
        degree = 0
        neighbours = self.adjacency_dict[position]
        for neighbour in neighbours:
            if neighbour in unassigned_positions:
                degree += 1
        return degree

    def identity_domain(self, variable, domains):
        # return its domain
        return domains[variable]

    def least_constraining_value(self, variable, domains):
        neighbours = self.adjacency_dict[variable]  # rows, columns, and small square
        value_count_tuples = []

        for value in domains[variable]:
            count = 0
            for neighbour in neighbours:
                if value in domains[neighbour]:
                    count += 1
            value_count_tuples.append((value, count))

        sorted_by_count = sorted(value_count_tuples, key=lambda tup: tup[1])
        result = [value[0] for value in sorted_by_count]
        return result

    # Returns adjacency dictionary of cells (tuple) with its neighbours (array)
    def get_adjacency_dict(self, state):
        adjacency_dict = defaultdict(list)

        for row in range(9):
            for col in range(9):
                position = (row, col)
                adjacency_dict[position] = self.get_neighbours(position)

        return adjacency_dict

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
                if current_col == col or current_row == row:
                    continue  # exclude same row and col
                else:
                    neighbours.append((current_row, current_col))

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
        neighbours = self.adjacency_dict[position]
        result = True

        for neighbour in neighbours:
            (row, col) = neighbour
            if state[row][col] == value:
                result = False

        return result

    def mac(self, deque, domains, removed=defaultdict(set)):
        while deque:  # true if not empty
            (X, Y) = deque.popleft()

            if self.revise(domains, X, Y, removed):
                # add removed
                if len(domains[X]) == 0:
                    return []
                neighbours = self.adjacency_dict[X]
                for Z in neighbours:
                    if neighbours != Y: deque.append((Z, X))
        return domains

    def forward_checking_singleton(self, deque, domains, removed=defaultdict(set)):
        while deque:  # true if not empty
            (X, Y) = deque.popleft()
            y = next(iter(domains[Y]))  # Y is an assigned variable in MAC, thus it has only one value.
            if y in domains[X]:
                domains[X].remove(y)
                removed[X].add(y)
                # add removed
                if len(domains[X]) == 0:
                    return []
                elif len(domains[X]) > 1:
                    continue
                neighbours = self.adjacency_dict[X]
                for Z in neighbours:
                    if neighbours != Y: deque.append((Z, X))
        return domains

    # Maintaining Arc Consistency
    def make_arc_deque(self, assigned_positions, unassigned_positions):
        deque = collections.deque()

        for position in assigned_positions:
            neighbours = self.adjacency_dict[position]
            for neighbour in neighbours:
                if neighbour in unassigned_positions:
                    deque.append((neighbour, position))
        return deque

    # revises domain of X; domain is mutated.
    def revise(self, domains, X, Y, removed):
        revised = False
        for x in set(domains[X]):  # copy domains to prevent set changed size during iteration
            is_satisfied = reduce(lambda prev, y: prev or x != y, domains[Y], False)
            if not is_satisfied:
                removed[X].add(x)
                domains[X].remove(x)
                revised = True
        return revised

    def forward_checking(self, domains, position, value, removed):
        neighbours = self.adjacency_dict[position]
        for neighbour in neighbours:
            if value in domains[neighbour]:
                domains[neighbour].remove(value)
                removed[neighbour].add(value)
                if not domains[neighbour]:
                    return []

        return domains

    def get_unassigned_positions(self, state):
        unassigned_positions = set()
        for row in range(9):
            for col in range(9):
                unassigned_position = (row, col)
                if state[row][col] == 0:
                    unassigned_positions.add(unassigned_position)
        return unassigned_positions

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.


if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
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

    start = time.time()

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    end = time.time()
    print("{0}s".format(end - start))

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")
