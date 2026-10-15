FROM debian:trixie-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gfortran make libopenmpi-dev openmpi-bin ca-certificates git && rm -rf /var/lib/apt/lists/*
WORKDIR /fds
ADD fds-source.tar.gz /fds/
WORKDIR /fds/Build/ompi_gnu_linux
RUN make -j1 VPATH=../../Source -f ../makefile ompi_gnu_linux COMP_FC=mpifort GIT_HASH=ff928dbf68a2623ced3a007be75391c6dc6c9f90 GIT_DATE=2026-10-15 GIT_BRANCH=pinned

FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgfortran5 libgomp1 libopenmpi40 python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=build /fds/Build/ompi_gnu_linux/fds_ompi_gnu_linux /usr/local/bin/fds
WORKDIR /study
COPY study.py worker.py manifest.json /study/
COPY decks /study/decks
ENV FDS_BINARY=/usr/local/bin/fds OMP_NUM_THREADS=4 OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/study/worker.py"]
