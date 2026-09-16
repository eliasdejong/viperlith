# Benchmarks
## How to run
### 1: Seed a Dataset
First a small or large dataset has to be seeded with the desired skew. Examples:

	BENCH_SKEW=0.1 ./seed_small.sh
	BENCH_SKEW=0.9 ./seed_small.sh
	BENCH_SKEW=0.1 ./seed_large.sh
	BENCH_SKEW=0.9 ./seed_large.sh

This will use the parameters in either `.env.bench-small` or `.env.bench-large`.

### 2: Launch Main Application
To avoid having to a valid session cookie on every requests, the main application has to be started in "simulated session mode". Example:

	SIMULATED_SESSION_COUNT=524288 DEBUG=0 ./launch.sh

	SIMULATED_SESSION_COUNT=8192 DEBUG=0 ./launch.sh

The simulated session count must match the `SEED_USER_COUNT` inside `.env.bench-small` or `.env.bench-large` of the currently running benchmark.

### 3: Run the Benchmark
Run the desired benchmark:

	BENCH_SKEW=0.1 BENCH_READ_PCT=100 ./run_small.sh
	BENCH_SKEW=0.1 BENCH_READ_PCT=95 ./run_small.sh
	BENCH_SKEW=0.9 BENCH_READ_PCT=50 ./run_large.sh

- `BENCH_SKEW` must match the skew of the seeded dataset.
- `BENCH_READ_PCT` can be used to send different ratios of read/write requests.