from argparse import ArgumentParser
from isp import ISP
import matplotlib.pyplot as plt
import numpy as np
import itertools
import os

parser = ArgumentParser()
parser.add_argument("--instance", type=str, default="instances/example.json", help="Path to instance file")

def get_coverage_ratios(model):
    instance = model.instance
    coverage_ratios = {}

    for s in instance.sessions:
        languages = instance.languages_per_session[s]
        language_pairs = list(itertools.combinations(languages, 2))
        total_pairs = len(language_pairs)

        covered = 0
        for l1, l2 in language_pairs:
            for i in instance.interpreters:
                key = (i, s, l1, l2)
                if key in model.z and model.z[key].X > 0.5:
                    covered += 1
                    break   # Only count once per pair

        coverage_ratios[s] = covered / total_pairs if total_pairs > 0 else 0.0

    return coverage_ratios

if __name__ == "__main__":
    args = parser.parse_args()
    first_obj = ISP(args.instance, "OF1", False)
    second_obj = ISP(args.instance, "OF2", False)

    first_obj.optimize()
    second_obj.optimize()

    ratios1 = get_coverage_ratios(first_obj)
    ratios2 = get_coverage_ratios(second_obj)

    sessions = sorted(ratios1.keys())
    x = np.arange(len(sessions))

    values1 = [ratios1[s] for s in sessions]
    values2 = [ratios2[s] for s in sessions]

    instance_name = os.path.basename(args.instance)
    instance_name = os.path.splitext(instance_name)[0]

    plt.figure(figsize=(14, 6))
    width = 0.35
    plt.bar(x - width/2, values1, width, label="OF1", color="skyblue")
    plt.bar(x + width/2, values2, width, label="OF2", color="salmon")
    plt.xlabel("Sessions")
    plt.ylabel("Coverage Ratio")
    plt.title("Coverage of Language Pairs per Session (OF1 vs OF2) on Instance: " + instance_name)
    plt.xticks(x, sessions, rotation=90)
    plt.ylim(0, 1.05)
    plt.legend()
    plt.tight_layout()
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.show()