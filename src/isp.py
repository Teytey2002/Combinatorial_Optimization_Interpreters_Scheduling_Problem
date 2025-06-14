from instance import Instance
import gurobipy as gp
from gurobipy import GRB, quicksum
import itertools


class ISP:
    def __init__(self, name, objective, operational_constraints: bool = False):
        self.instance = Instance(name)

        self.model = gp.Model("SimpleIP")
        self.model.reset()

        self.x = None
        self.y = None
        self.z = None
        self.t = None

        self.is_optimized = False
        self._add_variables()
        self._add_base_constraints()
        if operational_constraints:
            self._add_operational_constraints()

        self.model.update()
        self._add_objective(objective)
        self.model.update()

        self.model._x = self.x
        self.model._y = self.y
        self.model._z = self.z
        self.model._t = self.t

        self.model.setParam("TimeLimit", 600)

    def _add_variables(self):
        # === Variables ===
        interpreters = self.instance.interpreters
        sessions = self.instance.sessions

        # x_i,s = 1 if interpreter i is assigned to session s, 0 otherwise
        self.x = self.model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")

        # y_i,l1,l2 = 1 if the pair (l1, l2) is covered in session s, 0 otherwise
        self.y = self.model.addVars(
            [
                (s, l1, l2)
                for s in sessions
                for l1, l2 in itertools.combinations(self.instance.languages_per_session[s], 2)
            ],
            vtype=GRB.BINARY, name="y"
        )

        # z_i,s,l1,l2 = 1 if interpreter i covers the pair (l1, l2) in session s, 0 otherwise
        self.z = self.model.addVars(
            [
                (i, s, l1, l2)
                for i in interpreters
                for s in sessions
                for l1, l2 in itertools.combinations(self.instance.languages_per_interpreter[i], 2)
                if l1 in self.instance.languages_per_session[s] and l2 in self.instance.languages_per_session[s]
            ],
            vtype=GRB.BINARY, name="z"
        )

        # t[s] = 1 if all pairs are covered in session s, 0 otherwise
        self.t = self.model.addVars(sessions, vtype=GRB.BINARY, name="t")

    def _add_base_constraints(self):

        # === Constraints ===
        blocks = self.instance.blocks
        interpreters = self.instance.interpreters
        sessions = self.instance.sessions

        # 1: An interpreter can only be assigned to one session in a block
        for b in blocks:
            for i in interpreters:
                self.model.addConstr(quicksum(self.x[i, s] for s in self.instance.sessions_per_block[b]) <= 1,
                                name=f"one_session_per_interpreter_{i}_{b}")

        # 2: In a given session, translation l1 to l2 can only be covered if an interpreter that speaks both
        # languages is assigned
        for s in sessions:
            languages = self.instance.languages_per_session[s]
            for l1, l2 in itertools.combinations(languages, 2):
                eligible_interpreters = [i for i in interpreters if l1 in self.instance.languages_per_interpreter[i] and
                                         l2 in self.instance.languages_per_interpreter[i]]
                self.model.addConstr(
                    quicksum(self.x[i, s] for i in eligible_interpreters) >= self.y[s, l1, l2],
                    name=f"cover_pair_{s}_{l1}_{l2}"
                )

        # 3: A given interpreter can only cover one translation pair in a session
        for i in interpreters:
            for s in sessions:
                self.model.addConstr(
                    quicksum(self.z[i, s, l1, l2] for (i2, s2, l1, l2) in self.z if i2 == i and s2 == s) <= self.x[i, s],
                    name=f"one_translation_per_session_{i}_{s}"
                )

        # 4: If an interpreter is not assigned to a session, they cannot be responsible for any language
        # pair in that session
        for (i, s, l1, l2) in self.z:
            self.model.addConstr(self.z[i, s, l1, l2] <= self.x[i, s], name=f"z_impl_x_{i}_{s}_{l1}_{l2}")

        # 5: A language pair is considered covered if at least one interpreter is actively assigned to interpret it
        for s in sessions:
            languages = self.instance.languages_per_session[s]
            language_pairs = list(itertools.combinations(languages, 2))
            for l1, l2 in language_pairs:
                self.model.addConstr(
                    self.y[s, l1, l2] <= quicksum(self.z[i, s, l1, l2] for i in interpreters if (i, s, l1, l2) in self.z),
                    name=f"y_impl_z_{s}_{l1}_{l2}"
                )

        # 6: A session can only be considered fully covered if all language pairs used in the session are covered
        for s in sessions:
            languages = self.instance.languages_per_session[s]
            language_pairs = list(itertools.combinations(languages, 2))
            for l1, l2 in language_pairs:
                self.model.addConstr(self.t[s] <= self.y[s, l1, l2], name=f"t_impl_y_{s}_{l1}_{l2}")

        # 7: Each language pair in a session may be interpreted by at most one interpreter. (logical constraint)
        for s in sessions:
            languages = self.instance.languages_per_session[s]
            for l1, l2 in itertools.combinations(languages, 2):
                self.model.addConstr(
                    quicksum(self.z[i, s, l1, l2] for i in interpreters if (i, s, l1, l2) in self.z) <= 1,
                    name=f"unique_translator_{s}_{l1}_{l2}"
                )

    def _add_operational_constraints(self):
        # === Additional Constraints ===
        # 8: An interpreter can only be assigned to a maximum of 15 sessions
        interpreters = self.instance.interpreters
        sessions = self.instance.sessions
        blocks = self.instance.blocks
        for i in interpreters:
            self.model.addConstr(quicksum(self.x[i, s] for s in sessions) <= 15, name=f"max_sessions_per_interpreter_{i}")

        # 9: An interpreter can only be assigned to a maximum of 3 consecutive blocks
        for i in interpreters:
            for k in range(len(blocks) - 3):
                group = blocks[k:k + 4]
                sessions_in_group = sum((self.instance.sessions_per_block[b] for b in group), [])
                self.model.addConstr(
                    quicksum(self.x[i, s] for s in sessions_in_group) <= 3,
                    name=f"max_3_consecutive_blocks_{i}_from_{group[0]}"
                )

    def _add_objective(self, objective):
        sessions = self.instance.sessions
        if objective == "OF1":
            self.model.setObjective(gp.quicksum(self.y[s, l1, l2] for (s, l1, l2) in self.y.keys()), GRB.MAXIMIZE)
        elif objective == "OF2":
            self.model.setObjective(quicksum(self.t[s] for s in sessions), GRB.MAXIMIZE)
        else:
            raise ValueError("Objective function must be either 'OF1' or 'OF2', got: " + objective)

    def optimize(self):
        self.model.optimize()
        self.is_optimized = True

    def print_results(self):
        if not self.is_optimized:
            print("Model has not been optimized yet. Call optimize() first.")
            return

        z = self.model._z
        self.model.printAttr("X")

        print("\n--- Result ---")
        if self.model.status == GRB.OPTIMAL or self.model.status == GRB.TIME_LIMIT:
            print(f"Objective value: {self.model.ObjVal}")
            for i, s, l1, l2 in z:
                if z[i, s, l1, l2].X > 0.5:
                    print(f"Interpreter {i} assigned to session {s} covers pair ({l1}, {l2})")

    @property
    def runtime(self):
        if not self.is_optimized:
            print("Model has not been optimized yet. Call optimize() first.")
            return None
        return self.model.Runtime
