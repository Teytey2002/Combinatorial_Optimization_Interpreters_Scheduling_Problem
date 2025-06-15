from argparse import ArgumentParser
from isp import ISP
from isp_bridge import ISPBridge
import matplotlib.pyplot as plt
import numpy as np
import itertools
import os

parser = ArgumentParser()
parser.add_argument("--instance", type=str, default="instances/example.json", help="Path to instance file")
parser.add_argument("--oper-constr", action="store_true", help="Use operational constraints", default=False)
parser.add_argument("--bridging", action="store_true", help="Compare OF1 to bridging", default=False)

def get_coverage_ratios(model, bridging):
    instance = model.instance
    coverage_ratios = {}

    for s in instance.sessions:
        languages = instance.languages_per_session[s]
        language_pairs = list(itertools.combinations(languages, 2))
        total_pairs = len(language_pairs)

        covered = 0
        for l1, l2 in language_pairs:
            is_covered = False

            # Direct coverage by interpreters
            for i in instance.interpreters:
                zkey = (i, s, l1, l2)
                if zkey in model.z and model.z[zkey].X > 0.5:
                    is_covered = True
                    break

            # Coverage via bridging
            if not is_covered and bridging:
                for i1, i2, s1, la, lb, lp in model.w:
                    if {la, lb} == {l1, l2} and s1 == s:
                        if model.w[i1, i2, s1, la, lb, lp].X > 0.5:
                            is_covered = True
                            break

            if is_covered:
                covered += 1

        coverage_ratios[s] = covered / total_pairs if total_pairs > 0 else 0.0

    return coverage_ratios

if __name__ == "__main__":
    args = parser.parse_args()
    first_obj = ISP(args.instance, "OF1", args.oper_constr)
    if args.bridging:
        second_obj = ISPBridge(args.instance, "OF1", args.oper_constr)
    else:
        second_obj = ISP(args.instance, "OF2", args.oper_constr)

    first_obj.optimize()
    second_obj.optimize()

    ratios1 = get_coverage_ratios(first_obj, False)
    ratios2 = get_coverage_ratios(second_obj, args.bridging)

    sessions = sorted(ratios1.keys())
    x = np.arange(len(sessions))

    values1 = [ratios1[s] for s in sessions]
    values2 = [ratios2[s] for s in sessions]

    instance_name = os.path.basename(args.instance)
    instance_name = os.path.splitext(instance_name)[0]

    plt.figure(figsize=(14, 6))
    width = 0.35
    plt.bar(x - width/2, values1, width, label="OF1", color="skyblue")
    label = "OF2" if not args.bridging else "Bridging OF1"
    plt.bar(x + width/2, values2, width, label=label, color="salmon")
    plt.xlabel("Sessions")
    plt.ylabel("Coverage Ratio")
    if not args.bridging:
        suptitle = f"Coverage of Language Pairs per Session (OF1 vs OF2) on Instance: {instance_name}"
    else:
        suptitle = f"Coverage of Language Pairs per Session (OF1 vs OF1 with bridging) on Instance: {instance_name}"
    plt.suptitle(suptitle, fontsize=12)
    title = "Operational Constraints Applied" if args.oper_constr else "No Operational Constraints"
    plt.title(title, fontsize=10)
    plt.xticks(x, sessions, rotation=90)
    plt.ylim(0, 1.05)
    plt.legend()
    plt.tight_layout()
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.show()