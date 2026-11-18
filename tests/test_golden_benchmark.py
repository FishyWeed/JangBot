"""Pytest wrapper ensuring the 106-item golden benchmark suite passes with zero regressions."""

from tools.eval.run_benchmark import run_benchmark


def test_golden_benchmark_suite_zero_failures():
    """All single-turn and multi-turn golden benchmark cases must pass."""
    assert run_benchmark() == 0
