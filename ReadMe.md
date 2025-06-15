# Interpreter Scheduling Problem (ISP)

This project implements an optimization-based solver for scheduling interpreters into multilingual sessions. It supports two objective functions and optional constraints, and includes both a direct and a bridge-based assignment model.

## 🛠 Dependencies

- Python 3.7+
- `gurobipy` (requires a valid Gurobi license)
- `numpy`
- `matplotlib`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

```bash
python src/main.py --instance path/to/instance.json [OPTIONS]
```

### Options

| Option            | Description                                                                              |
|-------------------|------------------------------------------------------------------------------------------|
| `--OF1`           | Use objective function 1 (maximize covered language pairs)                               |
| `--OF2`           | Use objective function 2 (maximize fully covered sessions)                               |
| `--oper-constr`   | Apply operational constraints (max 15 sessions and 3 consecutive blocks per interpreter) |
| `--bridging`      | Use the ISPBridge model, enabling bridge language assignments                            |
| `--plot`          | Display a timetable plot of session assignments                                          |

## 📊 Output

The script prints:
- Objective value
- MIP gap
- Runtime in seconds

When `--plot` is enabled, it shows a visual timetable of interpreter assignments per session, by day and hour.


## 📄 Batch Execution with Scripts

To benchmark multiple instance configurations efficiently, use the provided shell scripts.

### Base ISP Model

`src/run` runs the base `ISP` model (no bridging) on all JSON instances in `instances/` folder, for both OF1 and OF2 objectives, with and without operational constraints.

**Usage:**
```bash
cd src
./run
```

**Output:**
Reports the results in a CSV file `results.csv` in the same directory.
The results contain the run configuration, objective value, MIP gap, and the (optimization) runtime (not counting the model building).

### Bridge ISP Model

`src/run_bridge` runs the `ISPBridge` model (with bridging constraints), on small instances (`*I40*` or `S40-*`) only, using both OF1 and OF2, always with operational constraints.

**Usage:**
```bash
cd src
./run_bridge
```

**Output:**
Appends results to the same `results.csv` file.

## 🧪 Examples

```bash
# Solve using OF1, operational constraints, and plot results
python main.py --instance instances/isp-S40-I40.json --OF1 --oper-constr --plot

# Solve using bridge model
python main.py --instance instances/isp-S40-I40.json --OF1 --oper-constr --bridging --plot
```

## 📈 Comparing Objectives

A separate script allows graphical comparison of coverage ratios between:
- OF1 and OF2
- OF1 and OF1 with bridging

This is useful for analyzing the efficiency and impact of modeling choices.

## 📁 Project Structure

- `main.py`: Main runner for solving and plotting
- `isp.py`: ISP model with direct assignments
- `isp_bridge.py`: ISP model with bridge language capabilities
- `instance.py`: Parser for JSON instance files
- `compare_objectives.py`: Plot coverage ratios between objectives
