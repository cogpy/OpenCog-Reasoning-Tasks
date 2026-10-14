"""Bounded, deterministic reasoning over concrete instances, without code execution.

Answers:
* truth-table-completions: {"variables": [names], "rows": [
  {"assignment": {name: bool}, "value": bool}]}, false-first row order.
* syllogism-reasoning: {"entailed": bool, "contradicted": bool,
  "consistent": bool}. Universal statements have no existential import;
  ``is``/``is_not`` subjects are named individuals. Inconsistent premises
  entail neither the query nor its negation (no explosion).
* towers-of-hanoi: {"moves": [{"from": peg, "to": peg}]}.
* stack-based-reasoning: {"pop_order": [strings]}, after pushing each step.

Validators inspect the supplied answer, not execution evidence or solver output.
The syllogism checker exhausts finite unary models represented by realized types;
one individual per witness/constant suffices because equality is not supported.
"""

import itertools
import re
import time


class _Invalid(ValueError):
    pass


class _Unsupported(ValueError):
    pass


_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_ -]{0,63}\Z")
_TOKEN = re.compile(r"\s*(<->|->|[()!&|^~]|[A-Za-z_][A-Za-z0-9_]*)")
_ALIASES = {"!": "NOT", "~": "NOT", "&": "AND", "|": "OR",
            "^": "XOR", "->": "IMPLIES", "<->": "IFF"}
_PRECEDENCE = {"IFF": 1, "IMPLIES": 2, "OR": 3, "XOR": 4, "AND": 5}
_NEGATION = {"all": "some_not", "no": "some", "some": "no",
             "some_not": "all", "is": "is_not", "is_not": "is"}


def _truth_input(instance):
    expression = instance.get("expression")
    if not isinstance(expression, str) or not expression.strip():
        raise _Invalid("expression must be a nonempty string")
    if len(expression) > 1024:
        raise _Unsupported("expression exceeds 1024 characters")
    tokens, position = [], 0
    expression = expression.strip()
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if not match:
            raise _Invalid("invalid expression token")
        token = match.group(1)
        tokens.append(_ALIASES.get(token, token))
        position = match.end()
    if len(tokens) > 256:
        raise _Unsupported("expression exceeds 256 tokens")
    cursor, names = 0, set()

    def parse(minimum=1, depth=0):
        nonlocal cursor
        if depth > 32:
            raise _Unsupported("expression exceeds depth 32")
        if cursor >= len(tokens):
            raise _Invalid("missing operand")
        token = tokens[cursor]
        cursor += 1
        if token == "NOT":
            node = ("NOT", parse(6, depth + 1))
        elif token == "(":
            node = parse(1, depth + 1)
            if cursor >= len(tokens) or tokens[cursor] != ")":
                raise _Invalid("unclosed parenthesis")
            cursor += 1
        elif token == ")" or token in _PRECEDENCE:
            raise _Invalid("expected variable")
        else:
            names.add(token)
            node = ("VAR", token)
        while cursor < len(tokens) and tokens[cursor] in _PRECEDENCE:
            operator = tokens[cursor]
            precedence = _PRECEDENCE[operator]
            if precedence < minimum:
                break
            cursor += 1
            right = parse(precedence if operator == "IMPLIES" else precedence + 1,
                          depth + 1)
            node = (operator, node, right)
        return node

    tree = parse()
    if cursor != len(tokens):
        raise _Invalid("unexpected trailing tokens")

    def tree_depth(node):
        return 1 if node[0] == "VAR" else 1 + max(tree_depth(child) for child in node[1:])

    if tree_depth(tree) > 32:
        raise _Unsupported("expression exceeds tree depth 32")
    if len(names) > 8:
        raise _Unsupported("at most eight variables are supported")
    variables = instance.get("variables", sorted(names))
    if (not isinstance(variables, list) or
            len(variables) != len(names) or
            any(not isinstance(name, str) for name in variables) or
            len(set(variables)) != len(variables) or set(variables) != names):
        raise _Invalid("variables must list each expression variable exactly once")
    return tree, sorted(names)


def _compile(tree):
    if tree[0] == "VAR":
        return [tree]
    code = _compile(tree[1])
    if len(tree) == 3:
        code += _compile(tree[2])
    return code + [(tree[0],)]


def _execute_boolean(code, assignment):
    stack = []
    for instruction in code:
        operator = instruction[0]
        if operator == "VAR":
            stack.append(assignment[instruction[1]])
        elif operator == "NOT":
            stack.append(not stack.pop())
        else:
            right, left = stack.pop(), stack.pop()
            if operator == "AND":
                value = left and right
            elif operator == "OR":
                value = left or right
            elif operator == "XOR":
                value = left != right
            elif operator == "IMPLIES":
                value = not left or right
            else:
                value = left == right
            stack.append(value)
    return stack[0]


def _check_boolean(tree, assignment):
    operator = tree[0]
    if operator == "VAR":
        return assignment[tree[1]]
    left = _check_boolean(tree[1], assignment)
    if operator == "NOT":
        return left is False
    right = _check_boolean(tree[2], assignment)
    true_pairs = {
        "AND": {(True, True)},
        "OR": {(True, True), (True, False), (False, True)},
        "XOR": {(True, False), (False, True)},
        "IMPLIES": {(False, False), (False, True), (True, True)},
        "IFF": {(False, False), (True, True)},
    }
    return (left, right) in true_pairs[operator]


def _syllogism_input(instance):
    premises, query = instance.get("premises"), instance.get("query")
    if not isinstance(premises, list):
        raise _Invalid("premises must be a list")
    if len(premises) > 32:
        raise _Unsupported("at most 32 premises are supported")
    predicates, constants = set(), set()
    for statement in premises + [query]:
        if not isinstance(statement, dict) or set(statement) != {"kind", "subject", "predicate"}:
            raise _Invalid("statements require kind, subject and predicate")
        kind = statement["kind"]
        if not isinstance(kind, str) or kind not in _NEGATION:
            raise _Invalid("unknown statement kind")
        for field in ("subject", "predicate"):
            if not isinstance(statement[field], str) or not _NAME.fullmatch(statement[field]):
                raise _Invalid("terms must be simple names of at most 64 characters")
        predicates.add(statement["predicate"])
        if kind in ("is", "is_not"):
            constants.add(statement["subject"])
        else:
            predicates.add(statement["subject"])
    if len(predicates) > 4 or len(constants) > 2:
        raise _Unsupported("at most four predicates and two named individuals are supported")
    return premises, query, sorted(predicates), sorted(constants)


def _satisfiable(statements, predicates, constants):
    """Solver: unary constraints have independent witnesses and named values."""
    indices = {name: index for index, name in enumerate(predicates)}

    def membership(value, name):
        return bool(value & (1 << indices[name]))

    types = list(range(1 << len(predicates)))
    for statement in statements:
        kind, subject, predicate = (statement[key] for key in ("kind", "subject", "predicate"))
        if kind == "all":
            types = [value for value in types
                     if not membership(value, subject) or membership(value, predicate)]
        elif kind == "no":
            types = [value for value in types
                     if not (membership(value, subject) and membership(value, predicate))]
    if not types:
        return False
    for constant in constants:
        facts = [item for item in statements
                 if item["kind"] in ("is", "is_not") and item["subject"] == constant]
        if not any(all(membership(value, item["predicate"]) == (item["kind"] == "is")
                       for item in facts) for value in types):
            return False
    for item in statements:
        if item["kind"] in ("some", "some_not"):
            if not any(membership(value, item["subject"]) and
                       membership(value, item["predicate"]) == (item["kind"] == "some")
                       for value in types):
                return False
    return True


def _solve_syllogism(data):
    premises, query, predicates, constants = data
    consistent = _satisfiable(premises, predicates, constants)
    negated = dict(query, kind=_NEGATION[query["kind"]])
    return {"consistent": consistent,
            "entailed": consistent and not _satisfiable(premises + [negated], predicates, constants),
            "contradicted": consistent and not _satisfiable(premises + [query], predicates, constants)}


def _model_check(data):
    """Independent checker: enumerate every nonempty set of realized unary types."""
    premises, query, predicates, constants = data
    types = list(itertools.product((False, True), repeat=len(predicates)))
    extensions = {
        name: sum(1 << index for index, value in enumerate(types) if value[column])
        for column, name in enumerate(predicates)
    }
    universe = (1 << len(types)) - 1

    def constraints(statements):
        forbidden, witnesses = 0, []
        individuals = {name: universe for name in constants}
        for item in statements:
            kind, subject, predicate = (item[key] for key in ("kind", "subject", "predicate"))
            positive = extensions[predicate]
            if kind in ("is", "is_not"):
                individuals[subject] &= positive if kind == "is" else universe ^ positive
            else:
                subject_types = extensions[subject]
                if kind == "all":
                    forbidden |= subject_types & (universe ^ positive)
                elif kind == "no":
                    forbidden |= subject_types & positive
                else:
                    witnesses.append(subject_types & (positive if kind == "some" else universe ^ positive))
        return forbidden, witnesses, list(individuals.values())

    specifications = [
        constraints(premises),
        constraints(premises + [query]),
        constraints(premises + [dict(query, kind=_NEGATION[query["kind"]])]),
    ]
    found = [False, False, False]
    for world in range(1, universe + 1):
        for index, (forbidden, witnesses, individuals) in enumerate(specifications):
            if (not found[index] and not world & forbidden and
                    all(world & mask for mask in witnesses) and
                    all(world & mask for mask in individuals)):
                found[index] = True
        if all(found):
            break
    return {"consistent": found[0], "entailed": found[0] and not found[2],
            "contradicted": found[0] and not found[1]}


def _hanoi_input(instance):
    disks = instance.get("disks")
    if type(disks) is not int or disks < 1:
        raise _Invalid("disks must be a positive integer")
    if disks > 10:
        raise _Unsupported("at most ten disks are supported")
    pegs = [instance.get("source", "A"), instance.get("target", "C"),
            instance.get("auxiliary", "B")]
    if any(not isinstance(peg, str) or not _NAME.fullmatch(peg) for peg in pegs):
        raise _Invalid("pegs must be simple names")
    if len(set(pegs)) != 3:
        raise _Invalid("source, target and auxiliary must be distinct")
    return disks, *pegs


def _stack_input(instance):
    steps = instance.get("steps")
    if not isinstance(steps, list):
        raise _Invalid("steps must be a list of strings")
    if len(steps) > 1024:
        raise _Unsupported("at most 1024 stack steps are supported")
    if any(not isinstance(step, str) for step in steps):
        raise _Invalid("each stack step must be a string")
    if any(len(step) > 1024 for step in steps):
        raise _Unsupported("stack step exceeds 1024 characters")
    return steps


class ReasoningBackend:
    """Execute and separately validate four supported concrete task schemas."""

    supported_tasks = frozenset({
        "truth-table-completions", "syllogism-reasoning",
        "towers-of-hanoi", "stack-based-reasoning",
    })
    available_capabilities = frozenset({
        "boolean_evaluation", "deterministic_rules", "knowledge_representation",
        "planning", "recursion", "state_transitions",
    })
    evaluator_version = "bounded-reasoning-v1"

    def _prepare(self, task_id, instance):
        if not isinstance(task_id, str) or task_id not in self.supported_tasks:
            raise _Unsupported("task has no implemented executor or validator")
        if not isinstance(instance, dict):
            raise _Invalid("instance must be a structured dictionary")
        parsers = {"truth-table-completions": _truth_input,
                   "syllogism-reasoning": _syllogism_input,
                   "towers-of-hanoi": _hanoi_input,
                   "stack-based-reasoning": _stack_input}
        return parsers[task_id](instance)

    def execute(self, task_id, instance):
        start = time.perf_counter()
        result = {"status": "completed", "answer": None, "evidence": [],
                  "confidence": 0.0, "resource_usage": {}, "errors": []}
        try:
            data = self._prepare(task_id, instance)
            if task_id == "truth-table-completions":
                tree, names = data
                code, rows = _compile(tree), []
                for values in itertools.product((False, True), repeat=len(names)):
                    assignment = dict(zip(names, values))
                    rows.append({"assignment": assignment,
                                 "value": _execute_boolean(code, assignment)})
                answer = {"variables": names, "rows": rows}
                units = len(rows)
            elif task_id == "syllogism-reasoning":
                answer = _solve_syllogism(data)
                units = 1 << len(data[2])
            elif task_id == "towers-of-hanoi":
                disks, source, target, auxiliary = data
                moves = []

                def move(count, origin, destination, spare):
                    if count:
                        move(count - 1, origin, spare, destination)
                        moves.append({"from": origin, "to": destination})
                        move(count - 1, spare, destination, origin)

                move(disks, source, target, auxiliary)
                answer, units = {"moves": moves}, len(moves)
            else:
                answer, units = {"pop_order": list(reversed(data))}, len(data)
            result.update(answer=answer, confidence=1.0,
                          evidence=[{"method": "bounded deterministic execution", "task_id": task_id}])
            result["resource_usage"]["work_units"] = units
        except (_Invalid, _Unsupported) as error:
            result.update(status="invalid_input" if isinstance(error, _Invalid) else "unsupported",
                          errors=[str(error)])
        except Exception:
            result.update(status="error", errors=["execution failed"])
        result["resource_usage"]["elapsed_seconds"] = time.perf_counter() - start
        return result

    def validate(self, task_id, instance, answer):
        result = {"validation_status": "failed", "evaluated": False, "success": False,
                  "quality_score": 0.0, "evidence": [], "issues": [],
                  "evaluator_version": self.evaluator_version}
        try:
            data = self._prepare(task_id, instance)
        except (_Invalid, _Unsupported) as error:
            result.update(validation_status="invalid_input" if isinstance(error, _Invalid) else "unsupported",
                          issues=[str(error)])
            return result
        result["evaluated"] = True
        method = {
            "truth-table-completions": "recursive truth-function checker",
            "syllogism-reasoning": "exhaustive finite unary model checker",
            "towers-of-hanoi": "legal move replay, goal and minimum-length checks",
            "stack-based-reasoning": "stack push/pop replay",
        }[task_id]
        try:
            if task_id == "truth-table-completions":
                self._validate_truth(data, answer)
            elif task_id == "syllogism-reasoning":
                if (not isinstance(answer, dict) or set(answer) != {"entailed", "contradicted", "consistent"}
                        or any(type(value) is not bool for value in answer.values())):
                    raise _Invalid("answer requires exactly three boolean conclusions")
                if answer != _model_check(data):
                    raise _Invalid("conclusions disagree with finite models")
            elif task_id == "towers-of-hanoi":
                self._validate_hanoi(data, answer)
            else:
                if (not isinstance(answer, dict) or set(answer) != {"pop_order"} or
                        not isinstance(answer["pop_order"], list) or
                        len(answer["pop_order"]) != len(data) or
                        any(not isinstance(item, str) for item in answer["pop_order"])):
                    raise _Invalid("answer requires a pop_order list of strings")
                stack = list(data)
                for item in answer["pop_order"]:
                    if not stack or stack.pop() != item:
                        raise _Invalid("incorrect stack pop order")
                if stack:
                    raise _Invalid("missing stack pops")
            result.update(validation_status="passed", success=True, quality_score=1.0,
                          evidence=[{"method": method, "outcome": "passed"}])
        except (ValueError, TypeError, KeyError, IndexError) as error:
            result["issues"] = [str(error)]
            result["evidence"] = [{"method": method, "outcome": "failed",
                                   "issues": list(result["issues"])}]
        except Exception:
            result.update(evaluated=False, issues=["independent evaluator failed"])
        return result

    @staticmethod
    def _validate_truth(data, answer):
        tree, names = data
        if not isinstance(answer, dict) or set(answer) != {"variables", "rows"}:
            raise _Invalid("answer requires variables and rows")
        if answer["variables"] != names or not isinstance(answer["variables"], list):
            raise _Invalid("incorrect variables")
        rows = answer["rows"]
        if not isinstance(rows, list) or len(rows) != 1 << len(names):
            raise _Invalid("truth table must contain every assignment exactly once")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"assignment", "value"}:
                raise _Invalid("each row requires assignment and value")
            assignment = row["assignment"]
            if (not isinstance(assignment, dict) or set(assignment) != set(names) or
                    any(type(value) is not bool for value in assignment.values()) or
                    type(row["value"]) is not bool):
                raise _Invalid("assignments and values must be boolean")
            key = tuple(assignment[name] for name in names)
            if key in seen:
                raise _Invalid("duplicate assignment")
            seen.add(key)
            if row["value"] != _check_boolean(tree, assignment):
                raise _Invalid("incorrect truth value")

    @staticmethod
    def _validate_hanoi(data, answer):
        disks, source, target, auxiliary = data
        if not isinstance(answer, dict) or set(answer) != {"moves"}:
            raise _Invalid("answer requires moves")
        moves = answer["moves"]
        if not isinstance(moves, list) or len(moves) != (1 << disks) - 1:
            raise _Invalid("plan must have the minimum number of moves")
        pegs = {source: list(range(disks, 0, -1)), target: [], auxiliary: []}
        for move in moves:
            if not isinstance(move, dict) or set(move) != {"from", "to"}:
                raise _Invalid("each move requires from and to")
            origin, destination = move["from"], move["to"]
            if (not isinstance(origin, str) or not isinstance(destination, str) or
                    origin not in pegs or destination not in pegs or origin == destination):
                raise _Invalid("invalid move pegs")
            if not pegs[origin]:
                raise _Invalid("cannot move from an empty peg")
            disk = pegs[origin].pop()
            if pegs[destination] and pegs[destination][-1] < disk:
                raise _Invalid("cannot put a larger disk on a smaller disk")
            pegs[destination].append(disk)
        if pegs[target] != list(range(disks, 0, -1)):
            raise _Invalid("plan does not reach the target")

    def run(self, task_id, instance):
        result = self.execute(task_id, instance)
        if result["status"] == "completed":
            result["validation"] = self.validate(task_id, instance, result["answer"])
        else:
            status = result["status"] if result["status"] in ("unsupported", "invalid_input") else "failed"
            result["validation"] = {
                "validation_status": status, "evaluated": False, "success": False,
                "quality_score": 0.0, "evidence": [], "issues": list(result["errors"]),
                "evaluator_version": self.evaluator_version,
            }
        result["success"] = (result["status"] == "completed" and
                             result["validation"]["success"])
        return result
