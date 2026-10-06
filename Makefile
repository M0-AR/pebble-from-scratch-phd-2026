.PHONY: test trace demo benchmark live snapshot verify

test:
	pytest tests/ -q

trace:
	python -m pebble --trace '2 + 3 * 4'

demo:
	python -m pebble programs/demo.pebble

benchmark:
	python benchmarks/bench_throughput.py

live:
	python experiments/live_market_validation.py

snapshot:
	python experiments/live_market_validation.py --snapshot-only

verify: test
	python experiments/precedence_experiment.py
	python experiments/live_market_validation.py --snapshot-only
	python benchmarks/bench_throughput.py
