# Spencer Cube

CSC 425 Term Project

## Team Members

| Name | Role |
| --- | --- |
| Josh Spencer | Solo project. Full stack development of the entire application (AI solver, back end, and front end). |

## Project Description

This project is a simple web app of a Rubik's Cube. The user can mix up the cube or set the starting state by hand, and then a search algorithm finds a path of moves that solves it, ideally the shortest one.

I am starting with a 2x2 cube, since its state space is small enough for brute force search like BFS. If time allows, I will add a 3x3 cube, which is far too large for plain BFS or DFS and will need a smarter approach such as IDA* with a pattern database heuristic. If it fits in scope, I may also add an algorithm selector so users can pick between different search algorithms and compare them.

**Input:** A UI of a Rubik's Cube that the user can scramble or edit to set the starting state.

**AI Task:** Search for a sequence of moves from the scrambled state to the solved state, and optimally the shortest one.

**Output:** The solved cube, plus the move sequence that gets from the scrambled state to the solved state.

### Evaluation

The solver will be judged on:

- Correctness: does the move sequence actually solve the cube?
- Solution length: how many moves it uses.
- Speed: how long the search takes.
- Nodes explored: how many states the algorithm looks at.

## Data and Environment

This project does not use a traditional dataset. It is a search problem, so the environment is the cube itself and the rules for turning it.

- **State:** one arrangement of every piece on the cube (position and orientation of each piece).
- **Actions:** a face turn. A quarter turn in either direction or a half turn counts as one move. With one corner held fixed, a 2x2 has 9 possible moves from any state, and a 3x3 has 18.
- **Goal:** the solved cube, with each face a single color.
- **State space size:** 3,674,160 reachable states on a 2x2 (one corner held fixed), and about 43 quintillion on a 3x3.
- **Known limits:** a 2x2 can always be solved in 11 moves or fewer, and a 3x3 in 20 or fewer.
