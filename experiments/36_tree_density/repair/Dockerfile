FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgfortran5 libgomp1 libopenmpi40 python3 ca-certificates libgoogle-perftools4 google-perftools binutils time && rm -rf /var/lib/apt/lists/*
COPY fds /usr/local/bin/fds
RUN echo '70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692  /usr/local/bin/fds' | sha256sum -c - && ldd /usr/local/bin/fds && test -f /usr/lib/x86_64-linux-gnu/libprofiler.so.0
WORKDIR /study
ENV OMP_NUM_THREADS=4 OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/study/worker.py"]
