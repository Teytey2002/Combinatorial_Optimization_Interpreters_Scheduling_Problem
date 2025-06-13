import gurobipy as gp
from gurobipy import GRB, quicksum
from instance import Instance
import itertools

example_instance = Instance("instances/example.json")

def simple_ip(instance, objective="OF1"):

    model = gp.Model("SimpleIP")
    model.reset()

    # === Variables ===
    interpreters = instance.interpreters
    sessions = instance.sessions

    # x_i,s = 1 if interpreter i is assigned to session s, 0 otherwise
    x = model.addVars(interpreters, sessions, vtype=GRB.BINARY, name="x")

    # y_i,l1,l2 = 1 if the pair (l1, l2) is covered in session s, 0 otherwise
    y = {}
    for s in sessions:
        languages = instance.languages_per_session[s]
        language_pairs = list(itertools.combinations(languages, 2))
        for l1, l2 in language_pairs:
            y[s, l1, l2] = model.addVar(vtype=GRB.BINARY, name=f"y_{s}_{l1}_{l2}")

    # z_i,s,l1,l2 = 1 if interpreter i covers the pair (l1, l2) in session s, 0 otherwise
    z = {}
    for i in interpreters:
        for s in sessions:
            session_languages = set(instance.languages_per_session[s])
            languages = itertools.combinations(session_languages, 2)
            for l1, l2 in languages:
                z[i, s, l1, l2] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{s}_{l1}_{l2}")

    # t[s] = 1 if all pairs are covered in session s, 0 otherwise
    t = model.addVars(sessions, vtype=GRB.BINARY, name="t")

    # === Constraints ===
    blocks = instance.blocks

    # 1: An interpreter can only be assigned to one session in a block
    for b in blocks:
        for i in interpreters:
            model.addConstr(quicksum(x[i, s] for s in instance.sessions_per_block[b]) <= 1,
                            name=f"one_session_per_interpreter_{i}_{b}")

    # 2: In a given session, translation l1 to l2 can only be covered if an interpreter that speaks both
    # languages is assigned
    for s in sessions:
        languages = instance.languages_per_session[s]
        for l1, l2 in itertools.combinations(languages, 2):
            eligible_interpreters = [i for i in interpreters if l1 in instance.languages_per_interpreter[i] and
                                     l2 in instance.languages_per_interpreter[i]]
            print(f"Eligible interpreters for session {s} and languages ({l1}, {l2}): {eligible_interpreters}")
            model.addConstr(
                quicksum(x[i, s] for i in eligible_interpreters) >= y[s, l1, l2],
                name=f"cover_pair_{s}_{l1}_{l2}"
            )

    # 3: A given interpreter can only cover one translation pair in a session
    for i in interpreters:
        for s in sessions:
            model.addConstr(
                quicksum(z[i, s, l1, l2] for (i2, s2, l1, l2) in z if i2 == i and s2 == s) <= x[i, s],
                name=f"one_translation_per_session_{i}_{s}"
            )

    model.update()
    print(*model.getConstrs(), sep="\n")
    exit()

    # 4: If an interpreter is not assigned to a session, they cannot be responsible for any language
    # pair in that session
    for (i, s, l1, l2) in z:
        model.addConstr(z[i, s, l1, l2] <= x[i, s], name=f"z_impl_x_{i}_{s}_{l1}_{l2}")

    # 5: A language pair is considered covered if at least one interpreter is actively assigned to interpret it
    for s in sessions:
        languages = instance.languages_per_session[s]
        language_pairs = list(itertools.combinations(languages, 2))
        for l1, l2 in language_pairs:
            model.addConstr(
                y[s, l1, l2] <= quicksum(z[i, s, l1, l2] for i in interpreters if (i, s, l1, l2) in z),
                name=f"y_impl_z_{s}_{l1}_{l2}"
            )

    # 6: A session can only be considered fully covered if all language pairs used in the session are covered
    for s in sessions:
        languages = instance.languages_per_session[s]
        language_pairs = list(itertools.combinations(languages, 2))
        for l1, l2 in language_pairs:
            model.addConstr(t[s] <= y[s, l1, l2], name=f"t_impl_y_{s}")

    for s in sessions:
        languages = instance.languages_per_session[s]
        for l1, l2 in itertools.combinations(languages, 2):
            model.addConstr(
                quicksum(z[i, s, l1, l2] for i in interpreters if (i, s, l1, l2) in z) <= 1,
                name=f"unique_translator_{s}_{l1}_{l2}"
            )

    # === Objective Function ===

    model.update()
    if objective == "OF1":
        model.setObjective(gp.quicksum(y[s, l1, l2] for (s, l1, l2) in y.keys()), GRB.MAXIMIZE)
    elif objective == "OF2":
        model.setObjective(quicksum(t[s] for s in sessions), GRB.MAXIMIZE)
    else:
        raise ValueError("Objective function must be either 'OF1' or 'OF2', got: " + objective)

    model.update()

    model._x = x
    model._y = y
    model._z = z
    model._t = t

    return model


model = simple_ip(example_instance, objective="OF1")
model.setParam("TimeLimit", 600)
model.optimize()
print(f"Runtime: {model.Runtime}")

z = model._z
model.printAttr("X")

print("\n--- Result ---")
if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
    print(f"Objective value: {model.ObjVal}")
    for i, s, l1, l2 in z:
        if z[i, s, l1, l2].X > 0.5:
            print(f"Interpreter {i} assigned to session {s} covers pair ({l1}, {l2})")