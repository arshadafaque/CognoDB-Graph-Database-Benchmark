import argparse
import csv
import gzip
import random
from pathlib import Path


def reservoir_sample_relationships(
    input_path: Path,
    output_path: Path,
    sample_size: int,
    seed: int,
) -> int:

    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero")

    rng = random.Random(seed)

    reservoir: list[tuple[int, int]] = []

    total_edges = 0

    with gzip.open(
        input_path,
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) < 2:
                continue

            try:
                source = int(parts[0])
                target = int(parts[1])
            except ValueError:
                continue

            total_edges += 1

            edge = (source, target)

            if len(reservoir) < sample_size:

                reservoir.append(edge)

            else:

                index = rng.randint(
                    0,
                    total_edges - 1,
                )

                if index < sample_size:
                    reservoir[index] = edge

    if total_edges < sample_size:
        raise ValueError(
            f"Dataset contains only {total_edges:,} edges, "
            f"but {sample_size:,} were requested."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            ["source", "target"]
        )

        writer.writerows(reservoir)

    print("=" * 70)
    print("SAMPLING COMPLETE")
    print("=" * 70)

    print(f"Original relationships: {total_edges:,}")
    print(f"Sample size:            {len(reservoir):,}")
    print(f"Seed:                   {seed}")
    print(f"Output:                 {output_path}")

    return total_edges


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Create a deterministic Pokec benchmark edge sample."
    )

    parser.add_argument(
        "--input",
        default="data/raw/snap_pokec/soc-pokec-relationships.txt.gz",
    )

    parser.add_argument(
        "--output",
        default="data/benchmark/relationships_sampled.csv",
    )

    parser.add_argument(
        "--size",
        type=int,
        default=100_000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    reservoir_sample_relationships(
        input_path=Path(args.input),
        output_path=Path(args.output),
        sample_size=args.size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()