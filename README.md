# CognoDB Graph Database Benchmark

A reproducible benchmark of **CognoDB Cloud** using a deterministic
100,000-relationship sample derived from the SNAP soc-Pokec social
network.

> **Important scope note:** The original assignment asks for CognoDB
> **plus at least four other managed graph databases** under equivalent
> resources. This repository currently documents and benchmarks CognoDB
> only. It should not be presented as the complete cross-platform
> assignment until the other four platforms have been measured with the
> same dataset and workloads.

------------------------------------------------------------------------

## 1. Objective

The goal is to build a reproducible graph-database benchmark harness
that measures:

-   Data-ingestion throughput
-   1-hop, 2-hop, and 3-hop traversals
-   Point lookup
-   Indexed/filtered lookup
-   Aggregation
-   Concurrent mixed read/write workload
-   Observable resource footprint

The benchmark uses the same local benchmark dataset, deterministic
seeds, warm-up iterations, measurement iterations, and client
environment so that the methodology can later be reused for additional
graph databases.

------------------------------------------------------------------------

## 2. Dataset

### Source

**SNAP soc-Pokec**

https://snap.stanford.edu/data/soc-Pokec.html

The raw SNAP dataset contains substantially more relationships than
required for this benchmark. A deterministic reservoir sample was
created locally so that the benchmark remains small enough for the
CognoDB free tier.

### Benchmark dataset

  Property                                Value
  ---------------------------- ----------------
  Dataset                        SNAP soc-Pokec
  Benchmark relationships               100,000
  Benchmark nodes                       169,870
  Relationship sampling seed                 42
  Start-node count                          100
  Start-node seed                         12345
  Warm-up iterations                         20
  Measurement iterations                    100
  Traversal depths                      1, 2, 3

The benchmark files are:

``` text
data/
├── raw/
│   └── snap_pokec/
│       ├── soc-pokec-relationships.txt.gz
│       └── soc-pokec-profiles.txt.gz
│
└── benchmark/
    ├── nodes.csv
    ├── relationships.csv
    ├── start_nodes.csv
    └── manifest.json
```

### Sampling methodology

The raw relationship file is streamed rather than loaded completely into
memory. Reservoir sampling with seed `42` selects exactly 100,000
relationships.

Nodes are then extracted from the sampled relationships and written to
`nodes.csv`.

The resulting benchmark dataset is validated for:

-   Duplicate nodes
-   Duplicate relationships
-   Invalid node references
-   Expected relationship count

------------------------------------------------------------------------

## 3. Project Structure

``` text
.
├── data/
│   ├── raw/
│   │   └── snap_pokec/
│   └── benchmark/
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
├── .gitignore
├── requirements.txt
└── README.md
```

Do **not** commit `.env`.

------------------------------------------------------------------------

## 4. Environment

### CognoDB

  Property          Value
  ----------------- ------------------------------
  Platform          CognoDB Cloud
  Database driver   Official Neo4j Python driver
  Protocol          Bolt over TLS (`bolt+s`)
  Username          `cognodb`
  Tier              Free / c0
  Region            Record actual region here
  Advertised CPU    0.5 burstable vCPU
  Advertised RAM    256 MB
  Advertised disk   1 GB

The URI and password are intentionally not included in this repository.

Configure them through environment variables:

``` env
COGNODB_URI=bolt+s://<instance-id>.databases.cognodb.cloud
COGNODB_USERNAME=cognodb
COGNODB_PASSWORD=<password>
```

------------------------------------------------------------------------

## 5. Installation

Create and activate a virtual environment:

``` powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

Install dependencies:

``` powershell
pip install -r requirements.txt
```

The Neo4j Python driver is used to connect to CognoDB.

------------------------------------------------------------------------

## 6. Reproducible Workflow

### 6.1 Inspect the raw dataset

``` powershell
python -m src.dataset.inspect
```

### 6.2 Create the deterministic 100,000-edge sample

``` powershell
python -m src.dataset.sample --size 100000 --seed 42
```

### 6.3 Transform relationships and extract nodes

``` powershell
python -m src.dataset.transform
```

### 6.4 Validate the benchmark dataset

``` powershell
python -m src.dataset.validate --expected-relationships 100000
```

Expected logical dataset:

``` text
Nodes:          169,870
Relationships:  100,000
```

### 6.5 Generate traversal start nodes

``` powershell
python -m src.dataset.start_nodes
```

The benchmark uses 100 deterministic start nodes with seed `12345`.

### 6.6 Generate/update the manifest

``` powershell
python -m src.dataset.manifest
```

------------------------------------------------------------------------

## 7. CognoDB Setup

### Test connectivity

``` powershell
python -m src.db.test_connection
```

### Create indexes/constraints

``` powershell
python -m src.loader.schema
```

The benchmark uses:

-   `User.id` as a unique property/constraint
-   `User.age` as an indexed property

### Load nodes

``` powershell
python -m src.loader.nodes
```

### Load relationships

``` powershell
python -m src.loader.relationships
```

The exact benchmark file `data/benchmark/relationships.csv` is loaded;
the raw 30M+ relationship file is not sampled again during loading.

### Validate the loaded database

``` powershell
python -m src.dataset.validate --expected-relationships 100000
```

------------------------------------------------------------------------

## 8. Benchmark Methodology

### Warm-up

Read workloads use:

``` text
20 warm-up iterations
100 measurement iterations
```

Warm-up results are excluded from reported latency metrics.

### Percentiles

The benchmark reports:

-   Minimum
-   p50
-   Mean
-   p95
-   Maximum

The assignment emphasizes p50 and p95 rather than averages alone.

### Client environment

Record the actual final benchmark machine and region here:

``` text
OS:               <record>
Python:           <record>
CPU:              <record>
RAM:              <record>
Region:           <record>
Network:          <record>
```

The same client machine and region should be used when additional
database platforms are benchmarked.

------------------------------------------------------------------------

# 9. Workloads

## 9.1 Traversals

The benchmark measures:

``` text
1-hop
2-hop
3-hop
```

from a deterministic set of 100 randomly selected source nodes.

The start-node selection is restricted to source nodes present in the
benchmark relationship dataset so that traversal tests do not
accidentally select isolated nodes.

Run:

``` powershell
python -m src.benchmark.check_traversals
python -m src.benchmark.traversals
```

------------------------------------------------------------------------

## 9.2 Point Lookup

Query pattern:

``` cypher
MATCH (n:User {id: $id})
RETURN n.id AS id
```

Indexed property:

``` text
User.id
```

Run:

``` powershell
python -m src.benchmark.lookups
```

------------------------------------------------------------------------

## 9.3 Filtered Lookup

Query pattern:

``` cypher
MATCH (n:User)
WHERE n.age = $age
RETURN count(n) AS count
```

Indexed property:

``` text
User.age
```

------------------------------------------------------------------------

## 9.4 Aggregation

The benchmark uses an age group-by aggregation:

``` cypher
MATCH (n:User)
WHERE n.age IS NOT NULL
RETURN n.age AS age, count(n) AS user_count
ORDER BY n.age
```

Run:

``` powershell
python -m src.benchmark.aggregation
```

------------------------------------------------------------------------

## 9.5 Mixed Workload

The mixed workload uses:

``` text
70% reads
30% writes
```

with:

``` text
Concurrency:
1
10
40
```

The write workload updates a temporary property on an existing `User`
node rather than creating additional relationships. This prevents the
benchmark from continuously increasing the logical relationship count.

Run the validation workload first:

``` powershell
python -m src.benchmark.mixed_workload --iterations 100
```

Then the full workload:

``` powershell
python -m src.benchmark.mixed_workload
```

After the workload, validate the original dataset again:

``` powershell
python -m src.dataset.validate --expected-relationships 100000
```

The expected logical relationship count must remain 100,000.

------------------------------------------------------------------------

# 10. Resource Footprint

Run:

``` powershell
python -m src.benchmark.resource_metrics
```

Record the values exposed by the CognoDB console.

  Resource                 Final value
  ------------------------ --------------------------------
  Nodes                    169,870
  Relationships            100,000
  Storage used             `<record final console value>`
  Storage limit            1 GiB
  Memory usage             `<record final console value>`
  Connections              `<record final console value>`
  CPU                      Not observable from driver
  Instance specification   `<record>`
  Region                   `<record>`

The database console should be treated as the source for platform
resource values that are not exposed through the driver.

------------------------------------------------------------------------

# 11. CognoDB Results

> The values below are results previously observed during development.
> Traversal results from the earlier run should **not** be treated as
> final because the start-node methodology was subsequently corrected.
> Final submission values should come from the clean benchmark instance.

## Data Loading

### Nodes

  Metric                   Result
  ------------ ------------------
  Nodes                   169,870
  Load time           255.271 sec
  Throughput     665.45 nodes/sec

### Relationships

  Metric                                          Result
  --------------- --------------------------------------
  Relationships                                  100,000
  Load time         `<final clean-instance measurement>`
  Throughput        `<final clean-instance measurement>`

------------------------------------------------------------------------

## Traversal

Previous exploratory run:

  Depth            p50          p95
  ------- ------------ ------------
  1-hop     242.308 ms   275.384 ms
  2-hop     242.806 ms   257.304 ms
  3-hop     243.292 ms   252.281 ms

**Status:** Re-run on the final clean instance after corrected
start-node generation before using these numbers in the final
submission.

------------------------------------------------------------------------

## Lookups

Previous measured run:

  Workload                   p50          p95
  ----------------- ------------ ------------
  Point lookup        258.342 ms   400.036 ms
  Filtered lookup     275.902 ms   473.255 ms

Indexed properties:

``` text
User.id
User.age
```

**Status:** Prefer final clean-instance measurements for submission.

------------------------------------------------------------------------

## Aggregation

Previous measured run:

  Workload                p50          p95
  -------------- ------------ ------------
  Age group-by     697.994 ms   769.255 ms

**Status:** Prefer final clean-instance measurement for submission.

------------------------------------------------------------------------

## Mixed Workload

Final values should be copied from:

``` powershell
python -m src.benchmark.mixed_workload
```

    Concurrency   Read %   Write %          QPS          p50          p95       Errors
  ------------- -------- --------- ------------ ------------ ------------ ------------
              1       70        30   `<record>`   `<record>`   `<record>`   `<record>`
             10       70        30   `<record>`   `<record>`   `<record>`   `<record>`
             40       70        30   `<record>`   `<record>`   `<record>`   `<record>`

------------------------------------------------------------------------

# 12. Resource / Free-Tier Caveat

During development, temporary write experiments caused the CognoDB
console's allocated storage usage to increase substantially even after
temporary benchmark data was removed.

At one point the development instance showed approximately:

``` text
Storage: 936 MB / 1 GiB
Memory: 83%
```

The logical graph was subsequently restored to:

``` text
169,870 nodes
100,000 relationships
```

This is an important free-tier caveat. Logical deletion of temporary
data should not be assumed to immediately return all allocated storage
to the platform.

For the final benchmark, the database should be started from a clean
instance and storage usage should be recorded from the CognoDB console.

------------------------------------------------------------------------

# 13. Methodology Caveats

The following should be disclosed in the final report:

1.  CognoDB was tested on its free/entry tier.
2.  The free tier has limited storage and memory.
3.  The database is remote, so measured query latency includes network
    and server round-trip overhead.
4.  Warm-up iterations are excluded from reported measurements.
5.  The benchmark uses the same fixed 100,000-edge dataset for
    reproducibility.
6.  Start nodes are selected deterministically using seed `12345`.
7.  Temporary mixed-workload writes modify existing nodes rather than
    creating new relationships.
8.  Resource values not exposed by the driver are marked as not
    observable and should be taken from the provider console.
9.  Any timeout, failed operation, throttling, or resource-limit event
    should be retained in the final results rather than hidden.

------------------------------------------------------------------------

# 14. Reproducibility Checklist

A clean benchmark run should follow:

``` text
1. Configure .env
2. Test connection
3. Create schema/indexes
4. Load nodes
5. Load relationships
6. Validate dataset
7. Generate start nodes
8. Validate start nodes
9. Run traversal benchmark
10. Run lookup benchmark
11. Run aggregation benchmark
12. Run mixed workload
13. Validate dataset again
14. Capture resource metrics
15. Record results
```

------------------------------------------------------------------------

# 15. Cross-Platform Benchmark Status

The assignment requires CognoDB plus at least four other graph databases
under equivalent resource constraints.

  ----------------------------------------------------------------------------------
  Platform   Dataset    Traversals   Lookups    Aggregation   Mixed      Footprint
             loaded                                                      
  ---------- ---------- ------------ ---------- ------------- ---------- -----------
  CognoDB    Yes        Yes\*        Yes\*      Yes\*         Yes\*      Yes\*

  Platform 2 Not        ---          ---        ---           ---        ---
             started                                                     

  Platform 3 Not        ---          ---        ---           ---        ---
             started                                                     

  Platform 4 Not        ---          ---        ---           ---        ---
             started                                                     

  Platform 5 Not        ---          ---        ---           ---        ---
             started                                                     
  ----------------------------------------------------------------------------------

`*` Final clean-instance values should replace exploratory development
measurements before submission.

------------------------------------------------------------------------

# 16. Analysis

The development measurements show a clear difference between simple
lookups and full graph-wide aggregation.

Point lookup was approximately 258 ms p50 in the exploratory run, while
the age group-by aggregation was approximately 698 ms p50. This is
consistent with the aggregation doing substantially more database work
than a point lookup.

The traversal measurements were unexpectedly close across 1-, 2-, and
3-hop depths in the exploratory run. Because the workload was remote,
fixed connection/network/server overhead may have dominated the small
additional traversal cost. However, these values should be re-measured
after the corrected start-node methodology before drawing a final
conclusion.

The free-tier storage behavior is also an important practical
observation. Logical cleanup does not necessarily mean that the provider
immediately returns allocated storage, so write-heavy workloads must be
designed and monitored carefully on a small free instance.

No claim is made here that CognoDB is faster or slower than another
database. A fair conclusion requires the same dataset, queries, client
environment, and equivalent resources on at least four additional
platforms.

------------------------------------------------------------------------

# 17. Security

Never commit:

``` text
.env
passwords
connection URIs
API keys
cloud credentials
```

Use environment variables instead.

Example `.gitignore`:

``` gitignore
.env
.venv/
myenv/
__pycache__/
*.pyc
```

