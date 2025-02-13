import random
from typing import ClassVar

from searchclient.action import Action, ActionType
from searchclient.color import Color


class State:
    _RNG = random.Random(1)

    agent_colors: ClassVar[list[Color | None]]
    walls: ClassVar[list[list[bool]]]
    box_colors: ClassVar[list[Color | None]]
    goals: ClassVar[list[list[str]]]

    def __init__(self, agent_rows: list[int], agent_cols: list[int], boxes: list[list[str]]) -> None:
        """
        Constructs an initial state.
        Arguments are not copied, and therefore should not be modified after being passed in.

        The lists walls, boxes, and goals are indexed from top-left of the level, row-major order (row, col).
               Col 0  Col 1  Col 2  Col 3
        Row 0: (0,0)  (0,1)  (0,2)  (0,3)  ...
        Row 1: (1,0)  (1,1)  (1,2)  (1,3)  ...
        Row 2: (2,0)  (2,1)  (2,2)  (2,3)  ...
        ...

        For example, State.walls[2] is a list of booleans for the third row.
        State.walls[row][col] is True if there's a wall at (row, col).

        The agent rows and columns are indexed by the agent number.
        For example, State.agent_rows[0] is the row location of agent '0'.

        Note: The state should be considered immutable after it has been hashed, e.g. added to a dictionary or set.
        """
        self.agent_rows = agent_rows
        self.agent_cols = agent_cols
        self.boxes = boxes
        self.parent: State | None = None
        self.joint_action: list[Action] | None = None
        self.g = 0
        self._hash: int | None = None

    def result(self, joint_action: list[Action]) -> "State":
        """
        Returns the state resulting from applying joint_action in this state.
        Precondition: Joint action must be applicable and non-conflicting in this state.
        """

        # Copy this state.
        copy_agent_rows = self.agent_rows[:]
        copy_agent_cols = self.agent_cols[:]
        copy_boxes = [row[:] for row in self.boxes]

        # Apply each action.
        for agent, action in enumerate(joint_action):
            if action.type is ActionType.NoOp:
                pass

            elif action.type is ActionType.Move:
                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols[agent] += action.agent_col_delta

            elif action.type is ActionType.Push:
                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols[agent] += action.agent_col_delta 

                box = copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]] 
                copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]] = ""
                copy_boxes[copy_agent_rows[agent] + action.box_row_delta][copy_agent_cols[agent] + action.box_col_delta] = box

            elif action.type is ActionType.Pull:
                box = copy_boxes[copy_agent_rows[agent] - action.box_row_delta][copy_agent_rows[agent] - action.box_col_delta]
                copy_boxes[copy_agent_rows[agent]][copy_agent_cols[agent]] = box
                copy_boxes[copy_agent_rows[agent] - action.box_row_delta][copy_agent_rows[agent] - action.box_col_delta] = ""

                copy_agent_rows[agent] += action.agent_row_delta
                copy_agent_cols += action.agent_col_delta

        copy_state = State(copy_agent_rows, copy_agent_cols, copy_boxes)

        copy_state.parent = self
        copy_state.joint_action = joint_action.copy()
        copy_state.g = self.g + 1

        return copy_state

    def is_goal_state(self) -> bool:
        for row in range(len(State.goals)):
            for col in range(len(State.goals[row])):
                goal = State.goals[row][col]

                if "A" <= goal <= "Z" and self.boxes[row][col] != goal:
                    return False
                if "0" <= goal <= "9" and not (
                    self.agent_rows[ord(goal) - ord("0")] == row and self.agent_cols[ord(goal) - ord("0")] == col
                ):
                    return False
        return True

    def get_expanded_states(self) -> list["State"]:
        num_agents = len(self.agent_rows)

        # Determine list of applicable action for each individual agent.
        applicable_actions = [
            [action for action in Action if self.is_applicable(agent, action)] for agent in range(num_agents)
        ]

        # Iterate over joint actions, check conflict and generate child states.
        joint_action = [Action.NoOp for _ in range(num_agents)]
        actions_permutation = [0 for _ in range(num_agents)]
        expanded_states = []
        while True:
            for agent in range(num_agents):
                joint_action[agent] = applicable_actions[agent][actions_permutation[agent]]

            if not self.is_conflicting(joint_action):
                expanded_states.append(self.result(joint_action))

            # Advance permutation.
            done = False
            for agent in range(num_agents):
                if actions_permutation[agent] < len(applicable_actions[agent]) - 1:
                    actions_permutation[agent] += 1
                    break
                else:  # noqa: RET508
                    actions_permutation[agent] = 0
                    if agent == num_agents - 1:
                        done = True

            # Last permutation?
            if done:
                break

        State._RNG.shuffle(expanded_states)
        return expanded_states

    def is_applicable(self, agent: int, action: Action) -> bool:
        agent_row = self.agent_rows[agent]
        agent_col = self.agent_cols[agent]
        _agent_color = State.agent_colors[agent]
        destination_row = agent_row + action.agent_row_delta
        destination_col = agent_col + action.agent_col_delta

        if action.type is ActionType.NoOp:
            return True

        if action.type is ActionType.Move:
            return self.is_free(destination_row, destination_col)

        if action.type is ActionType.Push:
            # if agent direction does not contain box of same color then return false
            # return is free of moving box in box direction
            if not self.boxes[destination_row][destination_col]: # assumes single agent system
                return False
            return self.is_free(destination_row + action.box_row_delta, destination_col + action.box_col_delta )

        if action.type is ActionType.Pull:
            # if opposing box direction does not contain agent of same color then return false
            # return is free of moving agent in agent direction
            if not self.boxes[destination_row - action.box_row_delta][destination_col - action.box_col_delta]: # assume single agent system
                return False
            return self.is_free(destination_row + action.agent_row_delta, destination_col + action.agent_col_delta)


        assert False, f"Not implemented for action type {action.type}."

    def is_conflicting(self, joint_action: list[Action]) -> bool:
        num_agents = len(self.agent_rows)

        destination_rows = [-1 for _ in range(num_agents)]  # row of new cell to become occupied by action
        destination_cols = [-1 for _ in range(num_agents)]  # column of new cell to become occupied by action
        box_rows = [-1 for _ in range(num_agents)]  # current row of box moved by action
        box_cols = [-1 for _ in range(num_agents)]  # current column of box moved by action

        # Collect cells to be occupied and boxes to be moved.
        for agent in range(num_agents):
            action = joint_action[agent]
            agent_row = self.agent_rows[agent]
            agent_col = self.agent_cols[agent]

            if action.type is ActionType.NoOp:
                pass

            elif action.type is ActionType.Move:
                destination_rows[agent] = agent_row + action.agent_row_delta
                destination_cols[agent] = agent_col + action.agent_col_delta
                box_rows[agent] = agent_row  # Distinct dummy value.
                box_cols[agent] = agent_col  # Distinct dummy value.

        for a1 in range(num_agents):
            if joint_action[a1] is Action.NoOp:
                continue

            for a2 in range(a1 + 1, num_agents):
                if joint_action[a2] is Action.NoOp:
                    continue

                # Moving into same cell?
                if destination_rows[a1] == destination_rows[a2] and destination_cols[a1] == destination_cols[a2]:
                    return True

        return False

    def is_free(self, row: int, col: int) -> bool:
        return not State.walls[row][col] and not self.boxes[row][col] and self.agent_at(row, col) is None

    def agent_at(self, row: int, col: int) -> str | None:
        for agent in range(len(self.agent_rows)):
            if self.agent_rows[agent] == row and self.agent_cols[agent] == col:
                return chr(agent + ord("0"))
        return None

    def extract_plan(self) -> list[list[Action]]:
        plan = []
        state: State | None = self
        while state is not None and state.joint_action is not None:
            plan.append(state.joint_action)
            state = state.parent
        plan.reverse()
        return plan

    def __hash__(self) -> int:
        if self._hash is None:
            prime = 31
            h = 1
            h = h * prime + hash(tuple(self.agent_rows))
            h = h * prime + hash(tuple(self.agent_cols))
            h = h * prime + hash(tuple(State.agent_colors))
            h = h * prime + hash(tuple(tuple(row) for row in self.boxes))
            h = h * prime + hash(tuple(State.box_colors))
            h = h * prime + hash(tuple(tuple(row) for row in State.goals))
            h = h * prime + hash(tuple(tuple(row) for row in State.walls))
            self._hash = h
        return self._hash

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, State):
            return False
        if self.agent_rows != other.agent_rows:
            return False
        if self.agent_cols != other.agent_cols:
            return False
        if State.agent_colors != other.agent_colors:
            return False
        if State.walls != other.walls:
            return False
        if self.boxes != other.boxes:
            return False
        if State.box_colors != other.box_colors:
            return False
        return State.goals == other.goals

    def __repr__(self) -> str:
        lines = []
        for row in range(len(self.boxes)):
            line = []
            for col in range(len(self.boxes[row])):
                if self.boxes[row][col]:
                    line.append(self.boxes[row][col])
                elif State.walls[row][col] is not None:
                    line.append("+")
                elif (agent := self.agent_at(row, col)) is not None:
                    line.append(agent)
                else:
                    line.append(" ")
            lines.append("".join(line))
        return "\n".join(lines)
