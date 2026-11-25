"""Medición de tiempo de pared monotónico en milisegundos."""

from contextlib import contextmanager
from time import perf_counter


@contextmanager
def measure(samples, stage):
    start = perf_counter()
    try:
        yield
    finally:
        samples[stage] = samples.get(stage, 0.0) + (perf_counter() - start) * 1000
