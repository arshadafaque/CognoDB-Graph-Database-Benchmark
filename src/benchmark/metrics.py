from statistics import mean


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    """
    Calculate a percentile using linear interpolation.

    Example:
        percentile(values, 50) -> p50
        percentile(values, 95) -> p95
    """

    if not values:
        raise ValueError(
            "Cannot calculate percentile from empty data."
        )

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (
        percentile_value / 100
    ) * (len(sorted_values) - 1)

    lower_index = int(rank)
    upper_index = lower_index + 1

    if upper_index >= len(sorted_values):
        return sorted_values[lower_index]

    fraction = rank - lower_index

    lower_value = sorted_values[
        lower_index
    ]

    upper_value = sorted_values[
        upper_index
    ]

    return (
        lower_value
        + (
            upper_value - lower_value
        )
        * fraction
    )


def calculate_latency_metrics(
    latencies_ms: list[float],
) -> dict[str, float]:
    """
    Calculate standard latency statistics.
    """

    if not latencies_ms:
        raise ValueError(
            "No latency measurements provided."
        )

    return {
        "count": len(latencies_ms),
        "min_ms": min(latencies_ms),
        "p50_ms": percentile(
            latencies_ms,
            50,
        ),
        "mean_ms": mean(latencies_ms),
        "p95_ms": percentile(
            latencies_ms,
            95,
        ),
        "max_ms": max(latencies_ms),
    }


def print_latency_metrics(
    name: str,
    metrics: dict[str, float],
) -> None:

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print(
        f"Iterations: {metrics['count']:,}"
    )

    print(
        f"Min:        {metrics['min_ms']:.3f} ms"
    )

    print(
        f"p50:        {metrics['p50_ms']:.3f} ms"
    )

    print(
        f"Mean:       {metrics['mean_ms']:.3f} ms"
    )

    print(
        f"p95:        {metrics['p95_ms']:.3f} ms"
    )

    print(
        f"Max:        {metrics['max_ms']:.3f} ms"
    )