"""Run with: python -m unittest discover -s tests -v"""
import unittest
from shuffle_core import (ALGORITHMS, MASK, ORDERED_DECK, BuiltInRandom,
                          WELL512a, Xorshift32, bounded_random, fisher_yates,
                          run_benchmark, validate_rounds)


class ValidationTests(unittest.TestCase):
    def test_accepts_bounds(self):
        self.assertEqual(validate_rounds("1"), 1)
        self.assertEqual(validate_rounds(" 10000 "), 10000)

    def test_rejects_invalid_numbers(self):
        for sample in ("", " ", "0", "10001", "2.5", "-1", "words", "1e2"):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                validate_rounds(sample)


class RandomTests(unittest.TestCase):
    def test_rng_outputs_within_32_bits(self):
        for generator in (BuiltInRandom, Xorshift32, WELL512a):
            with self.subTest(generator=generator.__name__):
                values = [generator(123).next_u32() for _ in range(3)]
                self.assertTrue(all(0 <= value <= MASK for value in values))

    def test_reproducible_sequences(self):
        for generator in (BuiltInRandom, Xorshift32, WELL512a):
            with self.subTest(generator=generator.__name__):
                a = generator(42)
                b = generator(42)
                self.assertEqual([a.next_u32() for _ in range(100)],
                                 [b.next_u32() for _ in range(100)])

    def test_sequence_not_constant(self):
        for generator in (BuiltInRandom, Xorshift32, WELL512a):
            with self.subTest(generator=generator.__name__):
                rng = generator(42)
                self.assertGreater(len({rng.next_u32() for _ in range(100)}), 95)

    def test_bounded_random_in_range(self):
        for generator in (BuiltInRandom, Xorshift32, WELL512a):
            with self.subTest(generator=generator.__name__):
                rng = generator(1234)
                for bound in range(1, 53):
                    for _ in range(10):
                        self.assertIn(bounded_random(rng.next_u32, bound), range(bound))

    def test_known_xorshift32_values(self):
        rng = Xorshift32(1)
        self.assertEqual([rng.next_u32() for _ in range(5)],
                         [270369, 67634689, 2647435461, 307599695, 2398689233])


class ShuffleTests(unittest.TestCase):
    def test_full_deck_contains_all_cards(self):
        self.assertEqual(len(ORDERED_DECK), 52)
        self.assertEqual(len(set(ORDERED_DECK)), 52)
        for generator in (BuiltInRandom, Xorshift32, WELL512a):
            rng = generator(22)
            deck = list(ORDERED_DECK)
            fisher_yates(deck, rng.next_u32)
            self.assertEqual(set(deck), set(ORDERED_DECK))
            self.assertNotEqual(tuple(deck), ORDERED_DECK)

    def test_result_contains_timing_and_deck(self):
        for algorithm in ALGORITHMS:
            with self.subTest(algorithm=algorithm):
                result = run_benchmark(algorithm, 4)
                self.assertEqual(result.rounds, 4)
                self.assertGreaterEqual(result.elapsed_ns, 0)
                self.assertEqual(len(result.last_deck), 52)
                self.assertEqual(set(result.last_deck), set(ORDERED_DECK))

    def test_benchmark_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            run_benchmark(ALGORITHMS[0], 10001)


if __name__ == "__main__":
    unittest.main()
