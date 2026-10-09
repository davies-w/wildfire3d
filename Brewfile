# Homebrew prerequisites for building the FDS engine on Apple Silicon.
#
# Read by `brew bundle`.  scripts/setup_engine.py runs `brew bundle check` and
# installs only if something is missing; Homebrew itself is installed first if
# it is absent.
#
# Not listed, because they come from the Xcode Command Line Tools: git, make,
# curl -- the FDS build scripts shell out to all three.  Not listed because the
# repository builds its own: python, via scripts/setup_env.py.

# gfortran. The FDS build target is ompi_gnu_osx, so the code is GNU Fortran,
# and HYPRE and SUNDIALS are compiled with it as well.
brew "gcc"

# mpifort, mpicc, mpicxx and mpirun. The FDS build scripts invoke all three
# compiler wrappers.
brew "open-mpi"

# cmake builds HYPRE and SUNDIALS; the FDS build scripts call it eight times.
brew "cmake"
