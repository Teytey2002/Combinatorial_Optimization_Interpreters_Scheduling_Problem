from argparse import ArgumentParser
from isp import ISP
from isp_bridge import ISPBridge
import matplotlib.pyplot as plt
import numpy as np

parser = ArgumentParser()
parser.add_argument("--instance", type=str, default="instances/example.json", help="Path to instance file")
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument("--OF1", action="store_true", help="Use objective function OF1")
group.add_argument("--OF2", action="store_true", help="Use objective function OF2")

parser.add_argument("--oper-constr", action="store_true", help="Use operational constraints", default=False)
parser.add_argument("--bridging", action="store_true", help="Use bridging constraints", default=False)
parser.add_argument("--plot", action="store_true", help="Plot results", default=False)

def determine_objective(args):
    if args.OF1:
        return "OF1"
    elif args.OF2:
        return "OF2"
    else:
        return "OF1"

def random_light_color():
    return tuple(np.random.uniform(0.6, 1.0) for _ in range(3))

if __name__ == "__main__":
    args = parser.parse_args()
    objective = determine_objective(args)
    if not args.bridging:
        model = ISP(args.instance, objective, args.oper_constr)
    else:
        model = ISPBridge(args.instance, objective, args.oper_constr)
    print("Model is built")
    model.optimize()

    print(f"Objective value: {model.objective_value}")
    print(f"MIP gap: {model.mip_gap:.4%}")
    print(f"Runtime: {model.runtime:.2f} seconds")


    if args.plot:
        instance = model.instance
        interpreters = instance.interpreters
        sessions = instance.sessions
        blocks = instance.blocks

        fig, ax = plt.subplots(figsize=(12, 8))
        for b in instance.sessions_per_block:
            number_of_sessions = len(instance.sessions_per_block[b])
            current = 0
            width = 1 / number_of_sessions if number_of_sessions > 0 else 0
            for s in instance.sessions_per_block[b]:
                # randomly assign a color to each session
                day = blocks.index(b) // 8
                hour = 8 + (blocks.index(b) % 8)
                ax.broken_barh([(day + current, width)], (hour, 1), color=random_light_color())
                ax.text(day + current, hour+0.15, f"{s}", fontsize=8, color='black')
                current += width

                assigned_interpreters = set(
                    i for (i2, s2, l1, l2) in model.z.keys()
                    if s2 == s and model.z[i2, s2, l1, l2].X > 0.5
                    for i in [i2]
                )
                if args.bridging:
                    assigned_interpreters.union(
                        i for (i1, i2, s2, l1, l2, lp) in model.w.keys()
                        if s2 == s and model.w[i1, i2, s2, l1, l2, lp].X > 0.5
                        for i in [i1, i2]
                    )

                interps = [i.split()[-1] for i in assigned_interpreters]
                label = ', '.join(interps[:2]) + (f' +{len(interps) - 2}' if len(interps) > 2 else '')

                ax.text(day + current - width / 2, hour + 0.5, label.strip(), fontsize=8, color='black', ha='center')

        ax.set_xticks([i + 0.5 for i in range(5)])
        ax.set_xticklabels(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

        for x in range(6):
            ax.axvline(x=x, color='gray', linewidth=0.5)

        ax.set_yticks(range(8, 17))
        ax.set_yticklabels([f"{h}h" for h in range(8, 17)])
        ax.invert_yaxis()
        ax.set_ylabel("Hour")
        ax.set_xlabel("Day")
        ax.set_title("Time Table of Interpreters")

        plt.grid(True)
        plt.tight_layout()
        plt.show()