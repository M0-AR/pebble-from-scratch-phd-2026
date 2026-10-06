FROM python:3.12-slim
WORKDIR /pebble
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["bash", "-c", "pytest tests/ -q && python experiments/precedence_experiment.py && python experiments/live_market_validation.py --snapshot-only && python benchmarks/bench_throughput.py && echo ALL_GREEN"]
