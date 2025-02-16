from abc import ABC, abstractmethod

from searchclient.state import State


class Heuristic(ABC):
    def __init__(self, initial_state: State) -> None:
        # Here's a chance to pre-process the static parts of the level.
        pass

    def h(self, state: State) -> int:
        not_at_goal = 0
        for row in range(len(state.goals)):
            for col in range(len(state.goals[row])):
                goal = state.goals[row][col]

                if "A" <= goal <= "Z" and state.boxes[row][col] != goal:
                    not_at_goal += 1
                if "0" <= goal <= "9" and not state.agent_at(row, col) == goal:
                    not_at_goal += 1
        return not_at_goal
    
    # Making my own improved heuristic function, uncomment to use, and commet out the above h function
    # def h(self, state: State) -> int:
    #     total_distance = 0

    #     # Compute Manhattan distance for boxes to their goal positions
    #     for row in range(len(state.goals)):
    #         for col in range(len(state.goals[row])):
    #             goal = state.goals[row][col]

    #             # If the goal is for a box (A-Z)
    #             if "A" <= goal <= "Z":
    #                 # Find the position of the box that should be here
    #                 for box_row in range(len(state.boxes)):
    #                     for box_col in range(len(state.boxes[box_row])):
    #                         if state.boxes[box_row][box_col] == goal:
    #                             # Manhattan distance = |x1 - x2| + |y1 - y2|
    #                             total_distance += abs(box_row - row) + abs(box_col - col)

    #             # If the goal is for an agent (0-9)
    #             elif "0" <= goal <= "9":
    #                 agent_id = ord(goal) - ord("0")  # Convert agent char to index
    #                 agent_row, agent_col = state.agent_rows[agent_id], state.agent_cols[agent_id]
    #                 total_distance += abs(agent_row - row) + abs(agent_col - col)

    #     return total_distance



    @abstractmethod
    def f(self, state: State) -> int: ...

    @abstractmethod
    def __repr__(self) -> str: ...


class HeuristicAStar(Heuristic):
    def __init__(self, initial_state: State) -> None:
        super().__init__(initial_state)

    def f(self, state: State) -> int:
        return state.g + self.h(state)

    def __repr__(self) -> str:
        return "A* evaluation"


class HeuristicWeightedAStar(Heuristic):
    def __init__(self, initial_state: State, w: int) -> None:
        super().__init__(initial_state)
        self.w = w

    def f(self, state: State) -> int:
        return state.g + self.w * self.h(state)

    def __repr__(self) -> str:
        return f"WA*({self.w}) evaluation"


class HeuristicGreedy(Heuristic):
    def __init__(self, initial_state: State) -> None:
        super().__init__(initial_state)

    def f(self, state: State) -> int:
        return self.h(state)

    def __repr__(self) -> str:
        return "greedy evaluation"
    
class HeuristicGoalCount(Heuristic):
    def __init__(self, initial_state: State) -> None:
        super().__init__(initial_state)

    def f(self, state: State) -> int:
        return state.g + self.h(state)

    def __repr__(self) -> str:
        return "Goal count evaluation"

