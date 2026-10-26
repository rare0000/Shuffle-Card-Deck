# Shuffle Card Deck

A small desktop app I made to experiment with different random-number generators and see how much they affect the time it takes to shuffle a deck of cards.

The idea was to test something simple — shuffling 52 cards — a few thousand times and compare the results. It turned out to be a useful way to learn about performance measurement, pseudo-random numbers, and why you should keep the actual work identical when comparing algorithms.

This is a **Python desktop application**, not a website. It opens in its own window using Tkinter.

## What it does

- Shuffles a real 52-card deck using the Fisher–Yates algorithm.
- Lets you choose anywhere from **1 to 10,000** shuffles per test.
- Compares **three random-number generators**: Python's built-in random generator, Xorshift32, and WELL512a.
- Shows when each test started and ended, the total elapsed time, and the average time per shuffle.
- Keeps a results table and a speed comparison so it's easy to see the difference.
- Displays the first few cards from the last shuffled deck.
- Warns you before clearing results if you change the number of rounds, with **OK** and **Cancel** options.
- Checks for missing, invalid, or out-of-range round counts.

## Technologies

- **Python 3.10+**
- **Tkinter** for the desktop interface
- **Python standard library** for the shuffle algorithms, timing, and tests
- **PyInstaller** (optional) for building a Windows `.exe`

No third-party packages are needed just to run the program.

## How to run it

1. Install [Python](https://www.python.org/downloads/) (3.10 or newer). On Windows, check **Add python.exe to PATH** during installation.
2. Download the repository and extract it, or clone it.
3. Double-click `run_windows.bat` on Windows, or open a terminal in the folder and run:

   ```bash
   python app.py
   ```

   On some systems the command is `python3 app.py`. Linux installations may also need the system's `python3-tk` package.

4. Enter a number of rounds, then click any of the three algorithm buttons. You can run them in any order.

## Making a Windows executable

If you want a standalone executable, run `build_windows_exe.bat` **on Windows**. It installs PyInstaller and builds `dist/Shuffle Card Deck.exe`. The build requires Python and an internet connection the first time, but people using the finished `.exe` won't need Python installed.

I didn't include a prebuilt `.exe` in this repository, since Windows executables need to be built and checked on Windows.

## How the comparison works

Each round creates a fresh ordered deck and runs the **same Fisher–Yates shuffle** on it. The only change is the random-number generator used for picking card positions. All three generators produce 32-bit values, and the program uses rejection sampling when choosing positions to avoid modulo bias.

| Algorithm | Notes |
| --- | --- |
| Built-in Random | Python's `random.Random` / Mersenne Twister; a standard-library baseline |
| Xorshift32 | A small, fast generator with a single 32-bit state |
| WELL512a | A generator using 16 × 32-bit state words (512 bits total) |

**About “JS Random” in the original project idea:** since I chose to build a native Python app instead of a JavaScript/browser app, I replaced `Math.random()` with Python's standard random generator. These are *not* the same algorithm, so the measurements should not be presented as a direct JavaScript `Math.random()` benchmark. The purpose here is comparing the implementations in this desktop project.

The test timer uses `time.perf_counter_ns()` for high-resolution elapsed measurements. Start/end wall-clock times are provided for reference. The displayed duration is the important performance figure.

### What I learned

The built-in generator is often faster because much of its implementation runs in optimized C, while the Xorshift32 and WELL512a versions here run in Python. This isn't a pure mathematical speed comparison between algorithms — Python interpreter overhead, machine load, and how many rounds you run all matter. Small tests can be especially noisy. For more reliable comparisons, use a larger round count and repeat each test a few times.

## Tests

To run the included tests:

```bash
python -m unittest discover -s tests -v
```

They cover round validation, repeatable random-number sequences, Xorshift32 reference output, shuffle correctness, and benchmark result structure.

## References

- [Fisher–Yates shuffle](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle)
- [Xorshift](https://en.wikipedia.org/wiki/Xorshift)
- [WELL random number generators](https://www.iro.umontreal.ca/~panneton/WELLRNG.html)
- [Python random documentation](https://docs.python.org/3/library/random.html)

This project was vibe coded with AI assistance.
