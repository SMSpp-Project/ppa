"""Generator of debian/control and of the per-package tables of the source
package, whose one build of the umbrella is split into one library package
per module, one command package per tool and the smspp-project metapackage.

Usage: gen_debian.py <source tree> [<debian dir>]
The version of each library package comes from the VERSION.txt of its module
in the source tree, since the SONAME is major.minor while 0.x, major after.
"""
import os
import sys
import textwrap

# (directory, package base, internal dependencies, -dev dependencies outside
#  the project, short description, long description)
LIBS = [
    ("SMS++", "libsmspp", [],
     ["libboost-dev", "libeigen3-dev", "libnetcdf-c++4-dev"],
     "core library of the SMS++ modelling framework",
     "The core defines the Block of a structured model, its Variable,\n"
     "Constraint, Objective and Function, the Solver attached to a Block and\n"
     "the Modification by which a change reaches the Solvers."),
    ("BinaryKnapsackBlock", "libsmspp-bkb", ["libsmspp"], [],
     "binary knapsack Block for SMS++",
     "The Block of the binary knapsack problem, with its dynamic programming\n"
     "and greedy Solvers."),
    ("MCFBlock", "libsmspp-mcf", ["libsmspp"], [],
     "min-cost flow Block for SMS++",
     "The Block of the min-cost flow problem on a network, which reads and\n"
     "writes the DIMACS and netCDF formats."),
    ("CapacitatedFacilityLocationBlock", "libsmspp-cflb",
     ["libsmspp-bkb", "libsmspp-mcf"], [],
     "capacitated facility location Block for SMS++",
     "The Block of the capacitated facility location problem, in its\n"
     "standard and knapsack reformulations, with a Benders Solver."),
    ("MMCFBlock", "libsmspp-mmcf", ["libsmspp-bkb", "libsmspp-mcf"], [],
     "multicommodity min-cost flow Block for SMS++",
     "The Block of the multicommodity min-cost flow problem, which reads the\n"
     "formats of the MMCF library."),
    ("LukFiBlock", "libsmspp-lukfi", ["libsmspp"], [],
     "test functions for nonsmooth optimization",
     "The Block of the test functions of Luksan and Vlcek, used to exercise\n"
     "the nondifferentiable Solvers."),
    ("UCBlock", "libsmspp-ucblock", ["libsmspp"], [],
     "Unit Commitment Block for SMS++",
     "The Block of the Unit Commitment problem of an electrical network,\n"
     "with the Blocks of its thermal, hydro, battery and intermittent units,\n"
     "of the network constraints and of the reserves, and the dynamic\n"
     "programming Solvers of the thermal unit."),
    ("StochasticBlock", "libsmspp-stochastic", ["libsmspp"], [],
     "stochastic wrapper Block for SMS++",
     "The Block that turns any Block into its stochastic version, mapping the\n"
     "realizations of a random variable onto the data of the wrapped Block."),
    ("TwoStageStochasticBlock", "libsmspp-tssb", ["libsmspp-stochastic"], [],
     "two-stage stochastic Block for SMS++",
     "The Block of a two-stage stochastic program, whose second stage is a\n"
     "set of scenario Blocks sharing the first-stage design variables."),
    ("MultiStageStochasticBlock", "libsmspp-mssb", ["libsmspp-tssb"], [],
     "multi-stage stochastic Block for SMS++",
     "The Block that aggregates the two-stage stochastic Blocks of the\n"
     "stages of a scenario tree."),
    ("SDDPBlock", "libsmspp-sddp", ["libsmspp-stochastic"],
     ["libstopt-dev", "libboost-mpi-dev", "libboost-timer-dev",
      "mpi-default-dev"],
     "stochastic dual dynamic programming Block",
     "The Block of a multistage stochastic program solved by SDDP, and the\n"
     "Solver that drives the algorithm of the StOpt library."),
    ("InvestmentBlock", "libsmspp-investment",
     ["libsmspp-sddp", "libsmspp-tssb", "libsmspp-ucblock"],
     ["libstopt-dev", "libboost-mpi-dev", "libboost-timer-dev",
      "mpi-default-dev"],
     "capacity expansion Block for SMS++",
     "The Block of the investment problem whose operational value is given by\n"
     "an inner Block, and the Function of its optimal value."),
    ("SVMBlock", "libsmspp-svm", ["libsmspp"],
     ["libsvm-dev", "liblinear-dev"],
     "support vector machine Block for SMS++",
     "The Block of the training problem of a support vector machine, in its\n"
     "primal and dual forms, and the Solvers that wrap libsvm and liblinear."),
    ("SingleFlowDCRBlock", "libsmspp-sfdcr", ["libsmspp"], [],
     "delay-constrained routing Block for SMS++",
     "The Block of the single-flow delay-constrained routing problem, with\n"
     "its Benders Solver."),
    ("MILPSolver", "libsmspp-milp", ["libsmspp"], ["libhighs-dev"],
     "MILP Solvers for SMS++",
     "The Solver that writes any Block as a mixed-integer linear program and\n"
     "hands it to a solver; this build carries the HiGHS backend, while the\n"
     "CPLEX, Gurobi and SCIP ones need those libraries at build time."),
    ("BundleSolver", "libsmspp-bundle", ["libsmspp-milp"],
     ["coinor-libclp-dev", "coinor-libosi-dev", "coinor-libcoinutils-dev",
      "libopenblas-dev"],
     "bundle Solver for SMS++",
     "The Solver of a nondifferentiable problem by the generalized bundle\n"
     "method, over the NDOSolver/FiOracle interface it bundles."),
    ("LagrangianDualSolver", "libsmspp-lds", ["libsmspp-milp"], [],
     "Lagrangian dual Solver for SMS++",
     "The Solver that builds the Lagrangian dual of a Block with linking\n"
     "constraints and solves it with an inner Solver."),
    ("FrankWolfeSolver", "libsmspp-frankwolfe", ["libsmspp"], [],
     "Frank-Wolfe Solver for SMS++",
     "The Solver of a convex problem over a compact set by the Frank-Wolfe\n"
     "algorithm, i.e., Dantzig-Wolfe decomposition."),
    ("BranchAndXSolver", "libsmspp-bnx", ["libsmspp"], [],
     "branch-and-X Solver for SMS++",
     "The relaxation-agnostic branch-and-bound Solver, which branches on the\n"
     "Variables of a Block whatever the Solver of its relaxation."),
    ("BendersDecompositionSolver", "libsmspp-bds", ["libsmspp"], [],
     "Benders decomposition Solver for SMS++",
     "The Solver that decomposes a Block into a master problem and its\n"
     "subproblems, generating the Benders cuts of their value functions."),
    ("MCFClassSolver", "libsmspp-mcfclass", ["libsmspp-mcf"], [],
     "MCFClass Solvers for SMS++",
     "The Solver of a min-cost flow Block by the algorithms of the MCFClass\n"
     "library, which it bundles: network simplex, relaxation, cost scaling."),
    ("MCFLemonSolver", "libsmspp-mcflemon", ["libsmspp-mcf"],
     ["liblemon-dev"],
     "LEMON Solvers for SMS++",
     "The Solver of a min-cost flow Block by the algorithms of the LEMON\n"
     "library."),
    ("ScenarioReductionSolver", "libsmspp-srs", ["libsmspp-tssb"], [],
     "scenario reduction Solver for SMS++",
     "The Solver that replaces the scenarios of a stochastic Block with a\n"
     "smaller set of representative ones."),
]

# the libraries that any tool needs to read a configuration naming a Solver
SOLVERS = ["libsmspp-lds", "libsmspp-bundle", "libsmspp-milp"]

# (package, tool directories, short description, long description)
TOOLS = [
    ("smspp-ucblock", ["ucblock_solver"],
     "Unit Commitment solver of SMS++",
     "ucblock_solver reads a UCBlock from a netCDF file and solves it with\n"
     "the Solvers of its configuration; MILP and Lagrangian dual\n"
     "configurations, and an example network, come with it."),
    ("smspp-tssb", ["tssb_solver"],
     "two-stage stochastic solver of SMS++",
     "tssb_solver reads a TwoStageStochasticBlock from a netCDF file and\n"
     "solves it with the Solvers of its configuration."),
    ("smspp-mssb", ["mssb_solver"],
     "multi-stage stochastic solver of SMS++",
     "mssb_solver reads a MultiStageStochasticBlock from a netCDF file and\n"
     "solves it with the Solvers of its configuration."),
    ("smspp-sddp", ["sddp_solver"],
     "SDDP solver of SMS++",
     "sddp_solver reads an SDDPBlock from a netCDF file and runs the\n"
     "stochastic dual dynamic programming algorithm on it."),
    ("smspp-investment", ["investmentblock_solver"],
     "capacity expansion solver of SMS++",
     "investmentblock_solver reads an InvestmentBlock from a netCDF file and\n"
     "solves the investment problem whose operations are an inner Block."),
    ("smspp-svm", ["svm_solver"],
     "support vector machine trainer of SMS++",
     "svm_solver trains a support vector machine on a data set in the libsvm\n"
     "format, with a grid search over the hyperparameters."),
    ("smspp-mcf", ["mcfblock_solver"],
     "min-cost flow solver of SMS++",
     "mcfblock_solver reads a min-cost flow problem in the DIMACS or netCDF\n"
     "format and solves it with the Solvers of its configuration."),
    ("smspp-bkb", ["bkblock_solver"],
     "binary knapsack solver of SMS++",
     "bkblock_solver reads a binary knapsack problem and solves it with the\n"
     "Solvers of its configuration."),
    ("smspp-cflb", ["cflblock_solver"],
     "capacitated facility location solver of SMS++",
     "cflblock_solver reads a capacitated facility location problem and\n"
     "solves it with the Solvers of its configuration."),
    ("smspp-mmcf", ["mmcfblock_solver"],
     "multicommodity min-cost flow solver of SMS++",
     "mmcfblock_solver reads a multicommodity min-cost flow problem and\n"
     "solves it with the Solvers of its configuration."),
    ("smspp-sfdcr", ["sfdcrblock_solver"],
     "delay-constrained routing solver of SMS++",
     "sfdcrblock_solver reads a single-flow delay-constrained routing\n"
     "problem from a netCDF file and solves it."),
    ("smspp-tools", ["block_solver", "chgcfg"],
     "generic solver and configuration editor of SMS++",
     "block_solver reads any Block from a netCDF file and solves it with the\n"
     "Solvers of its configuration, whatever its class; chgcfg edits the\n"
     "configuration files of the other tools."),
]

# the install of a module carries the library of the project it wraps, which
# is built in a directory of its own: (module, subdirectory, package base,
#  library file, short description, long description)
BUNDLED = [
    ("MCFClassSolver", "MCFClass", "libmcfclass", "libMCFClass",
     "min-cost flow algorithms of the MCFClass library",
     "MCFClass solves the min-cost flow problem by the network simplex, the\n"
     "relaxation and the cost-scaling algorithms, behind one interface; the\n"
     "MCFClassSolver module of SMS++ wraps it."),
    ("BundleSolver", "NdoFiOracle", "libndofioracle", "libNDOFiOracle",
     "bundle methods of the NDOSolver/FiOracle library",
     "NDOSolver/FiOracle solves a nondifferentiable problem given by an\n"
     "oracle of its function, by the generalized bundle method and by\n"
     "subgradient methods; the BundleSolver module of SMS++ wraps it."),
]

# the install of a module carries an auxiliary executable, which belongs to
# the command package of the module rather than to its development files
HELPERS = [
    ("BinaryKnapsackBlock", "bkbench", "smspp-bkb"),
    ("CapacitatedFacilityLocationBlock", "cfl2nc4", "smspp-cflb"),
    ("MCFBlock", "dmx2nc4", "smspp-mcf"),
    ("UCBlock", "nc4generator", "smspp-ucblock"),
]

MAINTAINER = "Donato Meoli <donato.meoli.95@gmail.com>"
HOMEPAGE = "https://smspp.gitlab.io/"
BUILD_DEPS = [
    "debhelper-compat (= 13)", "cmake (>= 3.21)", "pkgconf", "help2man",
    "libboost-dev", "libboost-mpi-dev", "libboost-timer-dev",
    "libeigen3-dev", "libnetcdf-c++4-dev",
    "libhighs-dev", "libstopt-dev", "libgeners-dev", "libbz2-dev",
    "zlib1g-dev", "liblemon-dev", "libsvm-dev",
    "liblinear-dev", "libopenblas-dev", "coinor-libclp-dev",
    "coinor-libosi-dev", "coinor-libcoinutils-dev", "mpi-default-dev",
]


def soversion(tree, module):
    """The SONAME of a module: major.minor while 0.x, major afterwards."""
    with open(os.path.join(tree, module, "VERSION.txt")) as f:
        major, minor = f.read().strip().split(".")[:2]
    return f"{major}.{minor}" if major == "0" else major


def wrap(lines):
    """The body of a Description, one leading space per line, under 80."""
    out = []
    for line in lines.split("\n"):
        out += textwrap.wrap(line, 76) or [""]
    return "".join(" " + l + "\n" for l in out)


def main():
    tree = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(tree, "debian")
    sover = {base: soversion(tree, d) for d, base, _, _, _, _ in LIBS}
    runtime = {base: base + sover[base] for base in sover}
    # (module) -> [(library package, library file)] of the wrapped projects
    wrapped = {}
    for module, sub, base, lib, _, _ in BUNDLED:
        pkg = base + soversion(tree, os.path.join(module, sub))
        wrapped.setdefault(module, []).append((pkg, lib))

    c = [f"""Source: smspp-project
Section: science
Priority: optional
Maintainer: {MAINTAINER}
Build-Depends: {(chr(10) + ' ').join(d + ',' for d in BUILD_DEPS)[:-1]}
Standards-Version: 4.7.2
Homepage: {HOMEPAGE}
Vcs-Git: https://gitlab.com/smspp/smspp-project.git
Vcs-Browser: https://gitlab.com/smspp/smspp-project
Rules-Requires-Root: no
"""]

    everything = []
    for module, base, needs, ext, short, long in LIBS:
        dev_deps = [f"{runtime[base]} (= ${{binary:Version}})"]
        dev_deps += [f"{p} (= ${{binary:Version}})"
                     for p, _ in wrapped.get(module, [])]
        dev_deps += [f"{n}-dev (= ${{binary:Version}})" for n in needs] + ext
        c.append(f"""
Package: {runtime[base]}
Architecture: any
Multi-Arch: same
Section: libs
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {short}
{wrap(long)} .
{wrap(f"This package holds the shared library of the {module} module.")}""")
        # no Multi-Arch: same, since the headers of a module, its generated
        # configuration header included, are outside the multiarch directory
        c.append(f"""
Package: {base}-dev
Architecture: any
Section: libdevel
Depends: {', '.join(dev_deps)}, ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {short} (development files)
{wrap(long)} .
{wrap(f"This package holds the headers and the CMake configuration of the "
      f"{module} module, which find_package({module}) then finds.")}""")
        everything.append(f"{base}-dev")

    for module, sub, base, lib, short, long in BUNDLED:
        pkg = base + soversion(tree, os.path.join(module, sub))
        c.append(f"""
Package: {pkg}
Architecture: any
Multi-Arch: same
Section: libs
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {short}
{wrap(long)} .
 The project travels inside SMS++, which builds it along with the module that
 wraps it; its headers and its CMake configuration are in the -dev package of
 that module.
""")
        everything.append(pkg)

    for pkg, tools, short, long in TOOLS:
        c.append(f"""
Package: {pkg}
Architecture: any
Section: science
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}
Description: {short}
{wrap(long)} .
 The configuration files and the examples of the tool are installed under
 /usr/share/SMS++_tools, where it looks for them when none is given.
""")
        everything.append(pkg)

    c.append(f"""
Package: smspp-project
Architecture: all
Section: science
Depends: {(chr(10) + ' ').join(p + ',' for p in everything)} ${{misc:Depends}}
Description: complete SMS++ framework
 SMS++ models a complex optimization problem as a tree of Blocks, each with
 its own structure, and solves it with the Solvers that exploit that
 structure: MILP reformulations, Lagrangian and Benders decompositions,
 bundle methods, dynamic programming.
 .
 This metapackage installs every module of the framework, with its headers,
 and every command-line tool.
""")

    with open(os.path.join(out, "control"), "w") as f:
        f.write("".join(c).replace("\n\n\n", "\n\n"))

    with open(os.path.join(out, "modules.tsv"), "w") as f:
        f.write("# module directory, library package, -dev package, and"
                " the library packages of the projects it wraps, each as"
                " package=library file\n")
        for module, base, _, _, _, _ in LIBS:
            extra = " ".join(f"{p}={lib}"
                             for p, lib in wrapped.get(module, []))
            f.write(f"{module}\t{runtime[base]}\t{base}-dev\t{extra}\n")

    with open(os.path.join(out, "tools.tsv"), "w") as f:
        f.write("# tool directories, package\n")
        for pkg, tools, _, _ in TOOLS:
            f.write(f"{','.join(tools)}\t{pkg}\n")

    with open(os.path.join(out, "helpers.tsv"), "w") as f:
        f.write("# -dev package holding it, executable, package it goes to\n")
        devof = {module: base + "-dev" for module, base, _, _, _, _ in LIBS}
        for module, exe, pkg in HELPERS:
            f.write(f"{devof[module]}\t{exe}\t{pkg}\n")

    # the library of a module is named after the project and the module, and
    # not after its SONAME, so that the packages of the framework read as one
    # family; the exception is a project that SMS++ wraps and does not rename
    for module, base, _, _, _, _ in LIBS:
        with open(os.path.join(out, f"{runtime[base]}.lintian-overrides"),
                  "w") as f:
            f.write("# the packages of the project are named after it and"
                    " after the module, not after the SONAME of the library,"
                    " which carries the name of the module alone\n")
            f.write(f"{runtime[base]}: package-name-doesnt-match-sonames *\n")

    # the auxiliary executables have no --help to make a man page out of
    byrecipient = {}
    for module, exe, pkg in HELPERS:
        byrecipient.setdefault(pkg, []).append(exe)
    for pkg, exes in byrecipient.items():
        with open(os.path.join(out, f"{pkg}.lintian-overrides"), "w") as f:
            f.write("# an auxiliary executable of the module, which has no"
                    " --help for help2man to read\n")
            for exe in exes:
                f.write(f"{pkg}: no-manual-page [usr/bin/{exe}]\n")



if __name__ == "__main__":
    main()
