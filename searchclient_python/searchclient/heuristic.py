from abc import ABC, abstractmethod

from searchclient.state import State


class Heuristic(ABC):
    def __init__(self, initial_state: State) -> None:
        # Here's a chance to pre-process the static parts of the level.
        pass

    def h(self, state: State) -> int:
        # h(n)should simply count how many agents or boxes are not at their destination.
        Not_at_goal = 0
        for row in range(len(state.goals)):
            for col in range(len(state.goals[row])):
                goal = state.goals[row][col]

                if "A" <= goal <= "Z" and state.boxes[row][col] != goal:
                    Not_at_goal += 1
                if "0" <= goal <= "9" and not (
                    state.agent_rows[ord(goal) - ord("0")] == row and state.agent_cols[ord(goal) - ord("0")] == col
                ):
                    Not_at_goal += 1

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
