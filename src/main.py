from argparse import ArgumentParser
from isp import ISP

parser = ArgumentParser()
parser.add_argument("--instance", type=str, default="instances/example.json", help="Path to instance file")
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument("--OF1", action="store_true", help="Use objective function OF1")
group.add_argument("--OF2", action="store_true", help="Use objective function OF2")

parser.add_argument("--oper-constr", action="store_true", help="Use operational constraints", default=False)

def determine_objective(args):
    if args.OF1:
        return "OF1"
    elif args.OF2:
        return "OF2"
    else:
        return "OF1"

if __name__ == "__main__":
    args = parser.parse_args()
    objective = determine_objective(args)
    model = ISP(args.instance, objective, args.oper_constr)
    print("Model is built")
    model.optimize()

    model.print_results()
    print(model.runtime)