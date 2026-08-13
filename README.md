# CognoDB Graph Database Benchmark

A reproducible benchmark of **CognoDB** using a deterministic 100,000-relationship sample derived from the public **SNAP soc-Pokec** social network dataset.

> **Scope:** This project benchmarks CognoDB only.

---

## 1. Project Objective

The objective is to measure the performance and practical behavior of CognoDB for a fixed graph workload.

The benchmark covers:

- Data loading throughput
- 1-hop, 2-hop and 3-hop graph traversals
- Point lookup
- Indexed/filtered lookup
- Aggregation
- Mixed concurrent read/write workload
- Observable resource footprint

The benchmark uses a fixed dataset, deterministic sampling, deterministic traversal start-node selection, warm-up iterations, and repeated measurements.

---

# 2. Dataset

## Source

**SNAP soc-Pokec**

Official source:

https://snap.stanford.edu/data/soc-Pokec.html

The raw relationship dataset contains more than 30 million relationships. The benchmark uses a deterministic sample of exactly 100,000 relationships so that the dataset fits within the CognoDB free-tier resource limits.

## Raw dataset

```text
data/raw/snap_pokec/
├── soc-pokec-relationships.txt.gz
├── soc-pokec-profiles.txt.gz
└── soc-pokec-readme.txt
```

The raw relationship file was streamed directly from the compressed dataset rather than loading the entire graph into memory.

## Benchmark dataset

| Property | Value |
|---|---:|
| Dataset | SNAP soc-Pokec |
| Sampled relationships | 100,000 |
| Nodes | 169,870 |
| Relationship sampling seed | 42 |
| Start-node count | 100 |
| Start-node seed | 12345 |

The resulting benchmark files are:

```text
data/benchmark/
├── nodes.csv
├── relationships.csv
├── start_nodes.csv
└── manifest.json
```

## Sampling methodology

The relationship dataset is sampled using reservoir sampling.

The process is:

```text
30M+ raw relationships
          |
          v
Streaming reservoir sampling
          |
       seed = 42
          |
          v
100,000 relationships
          |
          v
Extract referenced nodes
          |
          v
169,870 benchmark nodes
```

The sampling is deterministic because the random seed is fixed at `42`.

---

# 3. Project Structure

```text
CognoDB-Graph-Database-Benchmark/
│
├── config/
│   └── benchmark.yml
│
├── data/
│   ├── raw/
│   │   └── snap_pokec/
│   │       ├── soc-pokec-relationships.txt.gz
│   │       ├── soc-pokec-profiles.txt.gz
│   │       └── soc-pokec-readme.txt
│   │
│   └── benchmark/
│       ├── nodes.csv
│       ├── relationships.csv
│       ├── start_nodes.csv
│       └── manifest.json
│
├── src/
│   ├── dataset/
│   │   ├── inspect.py
│   │   ├── sample.py
│   │   ├── transform.py
│   │   ├── validate.py
│   │   ├── start_nodes.py
│   │   └── manifest.py
│   │
│   ├── db/
│   │   ├── client.py
│   │   ├── test_connection.py
│   │   └── cleanup_benchmark.py
│   │
│   ├── loader/
│   │   ├── schema.py
│   │   ├── nodes.py
│   │   └── relationships.py
│   │
│   └── benchmark/
│       ├── metrics.py
│       ├── check_traversals.py
│       ├── traversals.py
│       ├── lookups.py
│       ├── aggregation.py
│       ├── mixed_workload.py
│       └── resource_metrics.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

The `.env` file must not be committed to GitHub.

---

# 4. CognoDB Environment

The benchmark uses the official Neo4j Python driver to connect to CognoDB through the Bolt TLS endpoint.

Connection configuration is supplied through environment variables:

```env
COGNODB_URI=bolt+s://<instance-endpoint>
COGNODB_USERNAME=cognodb
COGNODB_PASSWORD=<password>
```

Credentials are intentionally excluded from this repository.

## Final CognoDB instance

| Property | Value |
|---|---|
| Platform | CognoDB |
| Plan | Free |
| Instance size | c0 |
| Version | v0.9.11 |
| Type | Standalone |
| Region | us-east4 |
| Memory | 512 MB |
| vCPU | Burst to 0.5 vCPU |
| Storage limit | 1 GiB |
| Disk IOPS | Up to 500 IOPS |
| Max connections | 200 |

---

# 5. Installation

Create the Python virtual environment:

```powershell
python -m venv myenv
```

Activate it:

```powershell
.\myenv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 6. Dataset Preparation

## Inspect raw data

```powershell
python -m src.dataset.inspect
```

This inspects the relationship and profile files without loading the complete raw dataset into memory.

## Create the deterministic sample

```powershell
python -m src.dataset.sample --size 100000 --seed 42
```

## Transform relationships and extract nodes

```powershell
python -m src.dataset.transform
```

## Validate the benchmark dataset

```powershell
python -m src.dataset.validate --expected-relationships 100000
```

Expected result:

```text
Nodes:                     169,870
Relationships:             100,000
Duplicate nodes:           0
Duplicate relationships:   0
Invalid references:        0
```

## Generate traversal start nodes

```powershell
python -m src.dataset.start_nodes
```

The benchmark uses:

```text
Start nodes:       100
Seed:              12345
```

---

# 7. CognoDB Setup

## Test connectivity

```powershell
python -m src.db.test_connection
```

## Create schema and indexes

```powershell
python -m src.loader.schema
```

The benchmark uses:

```text
User.id  -> unique constraint
User.age -> index
```

These indexes are used by the lookup workloads.

## Load nodes

```powershell
python -m src.loader.nodes
```

## Load relationships

```powershell
python -m src.loader.relationships
```

## Validate the loaded database

```powershell
python -m src.dataset.validate --expected-relationships 100000
```

Final logical graph:

```text
Nodes:          169,870
Relationships:  100,000
```

---

# 8. Benchmark Methodology

## Warm-up

Read benchmarks use:

```text
Warm-up iterations:      20
Measurement iterations:  100
```

Warm-up measurements are excluded from the reported latency values.

## Percentiles

The benchmark reports latency using:

- Minimum
- p50
- Mean
- p95
- Maximum

The main comparison metrics are p50 and p95.

## Dataset consistency

All workloads operate on the same benchmark graph:

```text
169,870 nodes
100,000 relationships
```

The graph is validated before and after workloads where appropriate.

---

# 9. Data Loading Results

## Node loading

Measured result:

| Metric | Value |
|---|---:|
| Nodes loaded | 169,870 |
| Load time | 255.271 seconds |
| Throughput | 665.45 nodes/sec |

## Relationship loading

The final logical relationship count was verified as:

```text
100,000 relationships
```

However, a separate relationship ingestion time/throughput measurement was not recorded in the benchmark output available for this project.

Therefore, no relationship throughput value is fabricated.

---

# 10. Traversal Benchmark

The benchmark measures:

```text
1-hop
2-hop
3-hop
```

using 100 deterministic start nodes.

## Results

| Traversal depth | p50 (ms) | p95 (ms) |
|---|---:|---:|
| 1-hop | 242.308 | 275.384 |
| 2-hop | 242.806 | 257.304 |
| 3-hop | 243.292 | 252.281 |

## Commands

Check start nodes:

```powershell
python -m src.benchmark.check_traversals
```

Run benchmark:

```powershell
python -m src.benchmark.traversals
```

---

# 11. Lookup Benchmark

## 11.1 Point Lookup

Indexed property:

```text
User.id
```

Measured results:

| Metric | Value |
|---|---:|
| Minimum | 254.451 ms |
| p50 | 258.342 ms |
| Mean | 282.009 ms |
| p95 | 400.036 ms |
| Maximum | 758.475 ms |

## 11.2 Filtered Lookup

Indexed property:

```text
User.age
```

Measured results:

| Metric | Value |
|---|---:|
| Minimum | 260.527 ms |
| p50 | 275.902 ms |
| Mean | 313.178 ms |
| p95 | 473.255 ms |
| Maximum | 482.120 ms |

## Lookup summary

| Workload | Indexed property | p50 (ms) | p95 (ms) |
|---|---|---:|---:|
| Point lookup | User.id | 258.342 | 400.036 |
| Filtered lookup | User.age | 275.902 | 473.255 |

Run:

```powershell
python -m src.benchmark.lookups
```

---

# 12. Aggregation Benchmark

The benchmark performs an age group-by aggregation over `User` nodes.

The logical workload is:

```cypher
MATCH (n:User)
WHERE n.age IS NOT NULL
RETURN n.age AS age, count(n) AS user_count
ORDER BY n.age
```

## Results

| Metric | Value |
|---|---:|
| Minimum | 636.419 ms |
| p50 | 697.994 ms |
| Mean | 710.832 ms |
| p95 | 769.255 ms |
| Maximum | 1106.743 ms |

Run:

```powershell
python -m src.benchmark.aggregation
```

---

# 13. Mixed Read/Write Workload

The benchmark defines the mixed workload as:

```text
Reads:       70%
Writes:      30%

Concurrency:
1
10
40
```

The implementation uses existing `User` nodes for write operations by updating a temporary benchmark property rather than continuously creating new relationships.

## Initial workload configuration

The completed benchmark configuration was:

```text
Nodes:              169,870
Read percentage:    70%
Write percentage:   30%
Warm-up:             100
Measurements:        1,000
Concurrency:         1, 10, 40
```

For the concurrency-1 workload:

```text
Measurement operations: 1,000
Reads:                    700
Writes:                   300
```

## Free-tier storage limitation

The mixed workload was not completed as a reliable sustained-throughput benchmark because the CognoDB free-tier instance was already close to its storage limit.

The CognoDB console showed:

```text
Storage:       934 MB / 1 GiB
Nodes:         169,870
Relationships: 100,000
Connections:   0
```

The database had only about 90 MB of remaining storage capacity.

Because the mixed workload performs writes, continuing a large write workload on an almost-full free-tier instance could introduce storage pressure, throttling, failures, or misleading measurements.

The running benchmark was therefore stopped rather than allowing the database to reach its storage limit.

### Result

The mixed workload is documented as a **resource-constrained / incomplete benchmark**, not as a successful QPS comparison.

No QPS, p50, or p95 values are fabricated for the mixed workload.

This is an intentional methodology decision: the benchmark reports the observed platform limitation instead of hiding or estimating missing results.

## Dataset integrity after stopping the workload

The database was validated after the workload was stopped:

```text
Unique nodes:              169,870
Duplicate node records:    0
Missing node IDs:           0

Relationships:             100,000
Duplicate relationships:   0
Invalid node references:   0

VALIDATION PASSED
```

Therefore, stopping the mixed workload did not corrupt the benchmark dataset.

---

# 14. Resource Footprint

The final CognoDB console observation was:

| Resource | Value |
|---|---:|
| Nodes | 169,870 |
| Relationships | 100,000 |
| Storage | 934 MB / 1 GiB |
| Memory specification | 512 MB |
| Connections at observation | 0 |
| vCPU | Burst to 0.5 vCPU |
| Disk IOPS | Up to 500 IOPS |
| Instance type | c0 |
| Plan | Free |
| Region | us-east4 |
| Version | v0.9.11 |

CPU utilization itself was not collected through the Python driver, so no CPU-utilization number is claimed.

Run the logical footprint script with:

```powershell
python -m src.benchmark.resource_metrics
```

---

# 15. Final Benchmark Summary

| Category | Workload | p50 (ms) | p95 (ms) | Throughput / Result |
|---|---|---:|---:|---|
| Loading | Nodes | — | — | 665.45 nodes/sec |
| Loading | Relationships | — | — | 100,000 loaded; throughput not recorded |
| Traversal | 1-hop | 242.308 | 275.384 | — |
| Traversal | 2-hop | 242.806 | 257.304 | — |
| Traversal | 3-hop | 243.292 | 252.281 | — |
| Lookup | Point | 258.342 | 400.036 | — |
| Lookup | Filtered | 275.902 | 473.255 | — |
| Aggregation | Age group-by | 697.994 | 769.255 | — |
| Mixed | 1 client | Not reported | Not reported | Storage constrained |
| Mixed | 10 clients | Not reported | Not reported | Storage constrained |
| Mixed | 40 clients | Not reported | Not reported | Storage constrained |

---

# 16. Observations

## Lookup vs aggregation

The point lookup had:

```text
p50 = 258.342 ms
p95 = 400.036 ms
```

The age group-by aggregation had:

```text
p50 = 697.994 ms
p95 = 769.255 ms
```

The aggregation therefore showed substantially higher latency than the point lookup.

## Traversal depth

The observed traversal latencies were:

```text
1-hop: 242.308 ms p50
2-hop: 242.806 ms p50
3-hop: 243.292 ms p50
```

The values were relatively close across the three traversal depths.

Because this is an end-to-end client benchmark against a remote database, measured latency includes network and client/server round-trip overhead. Therefore, the benchmark should not be interpreted as measuring only the internal graph traversal execution time.

## Free-tier storage behavior

The most important operational observation was the CognoDB free-tier storage limit.

The instance reached:

```text
934 MB / 1 GiB
```

while still containing the required:

```text
169,870 nodes
100,000 relationships
```

This limited the ability to run a sustained write-heavy workload safely.

---

# 17. Caveats

1. The benchmark uses a CognoDB free-tier instance with limited storage.
2. The mixed read/write workload was constrained by the available storage capacity.
3. The mixed workload was stopped before the database reached its storage limit.
4. The benchmark graph remained intact after stopping the mixed workload.
5. Network round-trip time is included in the observed query latency.
6. Warm-up iterations are excluded from the reported read latency measurements.
7. The same fixed benchmark dataset is used throughout the CognoDB benchmark.
8. No missing throughput or latency values are estimated or fabricated.
9. Resource values that are directly observable from the CognoDB console are reported; unavailable utilization metrics are marked as not observed.

---

# 18. Reproducibility

A complete benchmark setup follows this sequence:

```text
1. Download SNAP soc-Pokec
2. Inspect raw files
3. Reservoir sample 100,000 relationships using seed 42
4. Transform the sampled relationships
5. Extract nodes
6. Validate dataset
7. Generate 100 deterministic start nodes using seed 12345
8. Configure CognoDB credentials
9. Test CognoDB connectivity
10. Create schema/indexes
11. Load nodes
12. Load relationships
13. Validate the database
14. Run traversal benchmark
15. Run lookup benchmark
16. Run aggregation benchmark
17. Attempt mixed workload
18. Stop mixed workload when storage pressure becomes significant
19. Validate database integrity
20. Record resource footprint
```

---

# 19. Useful Commands

### Dataset

```powershell
python -m src.dataset.inspect
python -m src.dataset.sample --size 100000 --seed 42
python -m src.dataset.transform
python -m src.dataset.validate --expected-relationships 100000
python -m src.dataset.start_nodes
```

### CognoDB

```powershell
python -m src.db.test_connection
python -m src.loader.schema
python -m src.loader.nodes
python -m src.loader.relationships
```

### Benchmarks

```powershell
python -m src.benchmark.check_traversals
python -m src.benchmark.traversals
python -m src.benchmark.lookups
python -m src.benchmark.aggregation
python -m src.benchmark.mixed_workload
python -m src.benchmark.resource_metrics
```

---

# 20. Security

Never commit:

```text
.env
passwords
API keys
cloud credentials
private database connection information
```

Recommended `.gitignore` entries:

```gitignore
.env
.venv/
myenv/
__pycache__/
*.pyc
```

---

# 21. Project Status

The CognoDB-only benchmark implementation is complete for the measured workloads.

### Completed

- [x] SNAP soc-Pokec dataset
- [x] Deterministic 100,000 relationship sample
- [x] 169,870 benchmark nodes
- [x] Dataset validation
- [x] CognoDB connection
- [x] Schema and indexes
- [x] Node loading
- [x] Relationship loading
- [x] 1-hop traversal
- [x] 2-hop traversal
- [x] 3-hop traversal
- [x] Point lookup
- [x] Filtered lookup
- [x] Aggregation
- [x] Mixed workload implementation
- [x] Mixed workload resource-limit observation
- [x] Database integrity validation after stopping the mixed workload
- [x] Resource footprint documentation
- [x] Benchmark caveats

### Mixed workload limitation

The 70/30 mixed workload could not be completed as a sustained QPS benchmark on the free-tier instance because storage reached approximately 934 MB / 1 GiB.

This limitation is intentionally reported rather than hidden or replaced with estimated metrics.

---

# 22. Conclusion

The benchmark successfully measures CognoDB's behavior for the selected SNAP soc-Pokec graph across data loading, graph traversal, indexed lookup, filtered lookup, and aggregation workloads.

The measured results show:

- Node ingestion throughput of **665.45 nodes/sec**
- 1-hop traversal p50 of **242.308 ms**
- 2-hop traversal p50 of **242.806 ms**
- 3-hop traversal p50 of **243.292 ms**
- Point lookup p50 of **258.342 ms**
- Filtered lookup p50 of **275.902 ms**
- Age aggregation p50 of **697.994 ms**

The mixed workload exposed a practical limitation of the free CognoDB tier: the benchmark graph itself required approximately **934 MB of the available 1 GiB storage**, leaving insufficient headroom for a reliable sustained write benchmark.

The important conclusion is therefore not that the mixed workload failed due to application code, but that the **free-tier resource boundary became the limiting factor**. The benchmark records that limitation explicitly so the results remain reproducible and honest.
