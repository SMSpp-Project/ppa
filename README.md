# Debian packaging of SMS++

The source package of the [SMS++ umbrella](https://gitlab.com/smspp/smspp-project)
for the [PPA](https://launchpad.net/~smspp-project/+archive/ubuntu/smspp), out of
which Launchpad builds one library package per module, one command package per
tool and the `smspp-project` metapackage of them all:

    sudo add-apt-repository ppa:smspp-project/smspp
    sudo apt install smspp-project     # everything
    sudo apt install smspp-ucblock     # the Unit Commitment tool alone
    sudo apt install libsmspp-mcf-dev  # the headers of the MCFBlock module

The umbrella is built once, and the install of each module goes to its own
package: `libsmspp-<module><soname>` holds the shared library,
`libsmspp-<module>-dev` the headers and the CMake configuration that
`find_package()` finds, `smspp-<tool>` the executable with its configuration
files, its examples and its man page.

## Layout

    debian/           the packaging, with the tables of the packages that
                      gen_debian.py writes: control, modules.tsv, tools.tsv
    gen_debian.py     generator of those tables, whose own tables carry the
                      modules, the tools and their dependencies
    mk-ppa-source     source package of a release, for one or more series

## A release

The tag of the umbrella publishes the release tarball, from which

    ./mk-ppa-source 0.6.0 resolute --upload

builds the source package of that version for that series and uploads it to
the PPA, which then builds the binary packages for every architecture. The
upload needs a GPG key registered on Launchpad, and `devscripts` and `dput`
installed.

## Adding a module

A new module needs its row in the `LIBS` table of `gen_debian.py` (directory,
package base, the modules it needs, the `-dev` packages outside the project
that its CMake configuration finds, and its description), and a new tool its
row in `TOOLS`. The version of a package comes from the `VERSION.txt` of its
module, so a minor bump renames the library package: that is the point of the
name, since the SONAME changes with it.

## What the packages do not carry

CPLEX, Gurobi and SCIP are not redistributable, so `libsmspp-milp` carries the
HiGHS backend alone; a build against the others is still the one of the
sources. FastFlow, which the core fetches at configure time, travels in the
source package as a second component, so that the build needs no network.
