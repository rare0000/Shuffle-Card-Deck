"""Card shuffling and deterministic 32-bit PRNGs for Shuffle Card Deck.

All three methods feed the SAME Fisher–Yates implementation, which lets the
benchmark compare the Python PRNG implementations without changing the shuffle.
These generators are for games and experiments, not for cryptography.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from random import Random
from time import perf_counter_ns
from typing import Callable

MASK = 0xFFFFFFFF
SUITS = ("♠", "♥", "♦", "♣")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
ORDERED_DECK = tuple(f"{rank}{suit}" for suit in SUITS for rank in RANKS)
ALGORITHMS = ("Built-in Random", "Xorshift32", "WELL512a")


class BuiltInRandom:
    """Python's Mersenne Twister baseline; NOT JavaScript Math.random()."""

    def __init__(self, seed: int):
        self._rng = Random(seed)

    def next_u32(self) -> int:
        return self._rng.getrandbits(32)


class Xorshift32:
    """George Marsaglia's 32-bit xorshift (13, 17, 5)."""

    def __init__(self, seed: int):
        self.state = seed & MASK or 0x6D2B79F5  # non-zero state required

    def next_u32(self) -> int:
        x = self.state
        x ^= (x << 13) & MASK
        x ^= x >> 17
        x ^= (x << 5) & MASK
        self.state = x & MASK
        return self.state


class WELL512a:
    """WELL512a recurrence with sixteen 32-bit state words.

    Seeded via SplitMix32-style mixing to avoid low-diversity initial state.
    All intermediate operations wrap at 32 bits as in a C uint32_t version.
    """

    def __init__(self, seed: int):
        value = seed & MASK
        self.state: list[int] = []
        for _ in range(16):
            value = (value + 0x9E3779B9) & MASK
            z = value
            z = ((z ^ (z >> 16)) * 0x85EBCA6B) & MASK
            z = ((z ^ (z >> 13)) * 0xC2B2AE35) & MASK
            self.state.append((z ^ (z >> 16)) & MASK)
        if not any(self.state):
            self.state[0] = 1
        self.index = 0

    def next_u32(self) -> int:
        s = self.state
        i = self.index
        a = s[i]
        c = s[(i + 13) & 15]
        b = (a ^ c ^ ((a << 16) & MASK) ^ ((c << 15) & MASK)) & MASK
        c = s[(i + 9) & 15]
        c = (c ^ (c >> 11)) & MASK
        a = s[i] = (b ^ c) & MASK
        d = (a ^ ((a << 5) & 0xDA442D24)) & MASK
        i = (i + 15) & 15
        a = s[i]
        s[i] = (a ^ b ^ d ^ ((a << 2) & MASK) ^ ((b << 18) & MASK) ^ ((c << 28) & MASK)) & MASK
        self.index = i
        return s[i]


def make_generator(algorithm: str, seed: int):
    return {"Built-in Random": BuiltInRandom,
            "Xorshift32": Xorshift32,
            "WELL512a": WELL512a}[algorithm](seed)


def bounded_random(next_u32: Callable[[], int], upper: int) -> int:
    """Unbiased integer in [0, upper), via 32-bit rejection sampling."""
    if not 1 <= upper <= (1 << 32):
        raise ValueError("upper out of range")
    ceiling = (1 << 32) - ((1 << 32) % upper)
    while True:
        n = next_u32()
        if n < ceiling:
            return n % upper


def fisher_yates(deck: list[str], next_u32: Callable[[], int]) -> None:
    for i in range(len(deck) - 1, 0, -1):
        j = bounded_random(next_u32, i + 1)
        deck[i], deck[j] = deck[j], deck[i]


@dataclass(frozen=True)
class BenchmarkResult:
    algorithm: str
    rounds: int
    started: datetime
    finished: datetime
    elapsed_ns: int
    last_deck: tuple[str, ...]
    checksum: int

    @property
    def milliseconds(self) -> float:
        return self.elapsed_ns / 1_000_000

    @property
    def microseconds_per_shuffle(self) -> float:
        return self.elapsed_ns / self.rounds / 1_000


def validate_rounds(value: str) -> int:
    text = value.strip()
    if not text or not text.isdecimal():
        raise ValueError("Enter a whole number of rounds between 1 and 10,000.")
    rounds = int(text)
    if not 1 <= rounds <= 10_000:
        raise ValueError("Rounds must be between 1 and 10,000.")
    return rounds


def run_benchmark(algorithm: str, rounds: int, seed: int = 0x12345678) -> BenchmarkResult:
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown algorithm")
    if not 1 <= rounds <= 10_000:
        raise ValueError("Rounds must be between 1 and 10,000")
    generator = make_generator(algorithm, seed)
    get_random = generator.next_u32
    checksum = 0
    last_deck = list(ORDERED_DECK)

    # Exactly `rounds` independent 52-card shuffles, excluding construction
    # and timestamp/formatting from measured time.
    started = datetime.now()
    start_ns = perf_counter_ns()
    for _ in range(rounds):
        deck = list(ORDERED_DECK)
        fisher_yates(deck, get_random)
        checksum = ((checksum * 31) + ORDERED_DECK.index(deck[0])) & MASK
        last_deck = deck
    elapsed_ns = perf_counter_ns() - start_ns
    finished = datetime.now()
    return BenchmarkResult(
        algorithm, rounds, started, finished, elapsed_ns,
        tuple(last_deck), checksum,
    )
