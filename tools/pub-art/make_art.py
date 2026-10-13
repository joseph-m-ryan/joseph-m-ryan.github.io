"""Publication artwork for the site, drawn with matplotlib.

Each picture is an illustration built from a small toy calculation (not data
from the papers). Every picture is written twice into images/publications/:
a square 1254x1254 image for the paper page and a 4:3 720x540 thumbnail.

    python tools/pub-art/make_art.py            # all three
    python tools/pub-art/make_art.py crossover  # just one

Needs numpy, matplotlib and Pillow (with webp support).
"""

import io
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.patches import Polygon
from numpy.polynomial.laguerre import lagval
from numpy.polynomial.hermite import hermval
from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "images" / "publications"

# Colors follow the dark theme tokens in assets/css/site.css.
BG = "#050914"
HALO = "#0f1a3a"
INK = "#e7ecf5"
SOFT = "#c0c9d8"
MUTED = "#8b95a8"
FAINT = "#34405f"
BLUE = "#7eaaff"
LILAC = "#b9a8e6"
WARM = "#ffad60"
METAL = "#d9b98a"

TIME = LinearSegmentedColormap.from_list("time", [BLUE, LILAC, WARM])
DIVERGING = LinearSegmentedColormap.from_list("diverging", [WARM, "#5a3a2a", BG, "#243a6e", BLUE])
HEAT = LinearSegmentedColormap.from_list(
    "heat", [to_rgba(BLUE, 0.0), to_rgba(BLUE, 0.55), to_rgba(LILAC, 0.9), to_rgba(WARM, 1.0)])
DASH = (0, (4, 3))

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "mathtext.fontset": "stixsans",
    "text.color": MUTED,
    "figure.facecolor": BG,
    "axes.facecolor": "none",
    "savefig.facecolor": BG,
    "lines.solid_capstyle": "round",
    "lines.dash_capstyle": "round",
})


def panel(fig, rect, xlim=None, ylim=None):
    """A frameless, transparent drawing area."""
    ax = fig.add_axes(rect)
    ax.set_axis_off()
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    return ax


def backdrop(fig, cx=0.5, cy=0.5, spread=0.55):
    """Soft halo behind the drawing so the background isn't dead flat."""
    ax = panel(fig, (0, 0, 1, 1))
    g = np.linspace(0, 1, 300)
    x, y = np.meshgrid(g, g)
    halo = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * (spread / 2) ** 2))
    cmap = LinearSegmentedColormap.from_list("halo", [BG, HALO])
    ax.imshow(halo, extent=(0, 1, 0, 1), origin="lower", cmap=cmap, aspect="auto", zorder=-10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


def glow(ax, x, y, color, lw=1.6, strength=1.0, **kw):
    """A line with a faint bloom under it."""
    for width, alpha in ((7, 0.035), (4, 0.07), (2.2, 0.12)):
        ax.plot(x, y, color=color, lw=lw * width, alpha=alpha * strength, **kw)
    return ax.plot(x, y, color=color, lw=lw, **kw)


def bead(ax, x, y, color, size=7.5):
    """A particle: a dot with a halo."""
    for scale, alpha in ((4.2, 0.06), (2.8, 0.1), (1.8, 0.18)):
        ax.plot(x, y, "o", ms=size * scale, color=color, alpha=alpha, mec="none", zorder=6)
    ax.plot(x, y, "o", ms=size, color=color, mec=INK, mew=0.8, zorder=7)


def gradient_line(ax, x, y, cmap=TIME, lw=1.0, alpha=1.0, values=None):
    pts = np.column_stack([x, y])
    lc = LineCollection(np.stack([pts[:-1], pts[1:]], axis=1), cmap=cmap, lw=lw, alpha=alpha,
                        capstyle="round")
    lc.set_array(np.linspace(0, 1, len(x) - 1) if values is None else values)
    ax.add_collection(lc)
    return lc


def arrowhead(ax, x, y, dx, dy, color, size=9):
    ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0, mutation_scale=size,
                                shrinkA=0, shrinkB=0))


def save(draw, name):
    """Render draw(fig, square) at both aspect ratios and write the webp files."""
    for square, suffix, inches, size in (
        (True, "", (6.27, 6.27), (1254, 1254)),
        (False, "-thumb", (6.27, 4.7025), (720, 540)),
    ):
        fig = plt.figure(figsize=inches, dpi=400)
        draw(fig, square)
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        img = Image.open(buf).convert("RGB").resize(size, Image.LANCZOS)
        img.save(OUT / f"{name}{suffix}.webp", quality=90, method=6)
        print("wrote", f"{name}{suffix}.webp")


def fit(square, rect):
    """Rectangles are given for the 4:3 frame; pull them toward the middle of the square."""
    x, y, w, h = rect
    return (x, 0.5 + (y - 0.5) * 0.82, w, h * 0.82) if square else rect


def square_box(square, cx, cy, w):
    """A box that is square on the page, centered at (cx, cy), in figure fractions."""
    h = w if square else w * 4 / 3
    return (cx - w / 2, cy - h / 2, w, h)


# --------------------------------------------------------------------------
# Heating and escape under colored noise
# --------------------------------------------------------------------------

K = math.e / 2          # V(x) = K x^2 exp(-x^2/2): barriers of height 1 at |x| = sqrt(2)
TILT = 0.18             # steady force that tilts the trap and lowers its right-hand barrier


def well(x):
    """The tilted trap."""
    return K * x**2 * np.exp(-x**2 / 2) - TILT * x


def well_force(x):
    return -K * (2 * x - x**3) * math.exp(-x * x / 2) + TILT


_grid = np.linspace(-0.5, 0.5, 20001)
X_MIN = float(_grid[np.argmin(well(_grid))])


def colored_noise(rng, n, dt, alpha, f_min=0.0):
    """Gaussian noise with spectrum ~ 1/f^alpha above f_min, unit variance."""
    f = np.fft.rfftfreq(n, dt)
    amp = np.zeros_like(f)
    amp[1:] = f[1:] ** (-alpha / 2)
    amp[f < f_min] = 0
    spec = amp * (rng.normal(size=f.size) + 1j * rng.normal(size=f.size))
    x = np.fft.irfft(spec, n)
    return x / x.std()


def integrate(force_at, n, dt, stop=3.4):
    """Velocity-Verlet run from rest at the trap minimum; returns position and energy."""
    x, p = X_MIN, 0.0
    xs, es = [], []
    for i in range(n):
        f = force_at(i)
        p += 0.5 * dt * (well_force(x) + f)
        x += dt * p
        p += 0.5 * dt * (well_force(x) + f)
        xs.append(x)
        es.append(0.5 * p * p + K * x * x * math.exp(-x * x / 2) - TILT * x)
        if abs(x) > stop:
            break
    return np.array(xs), np.array(es)


def diffusive_run():
    """Weak 1/f noise with no slow part: the energy wanders up over many oscillations."""
    dt, n = 0.02, 40000
    for seed in range(400):
        xi = 0.07 * colored_noise(np.random.default_rng(seed), n, dt, 1.0, f_min=0.05)
        x, e = integrate(lambda i: xi[i], n, dt)
        if x[-1] > 3.4 and 0.5 * n < x.size < 0.95 * n and e[-1] < 0.85:
            return x, e
    raise RuntimeError("no escaping run found")


def ballistic_run():
    """One slow, strong push and the particle leaves in a single pass."""
    dt, n = 0.01, 4000
    t = np.arange(n) * dt
    push = 1.1 * np.exp(-((t - 3.6) / 1.2) ** 2)
    return integrate(lambda i: push[i], n, dt, stop=3.6)


def draw_escape(fig, square):
    backdrop(fig, 0.5, 0.35, 0.8)
    rng = np.random.default_rng(11)

    # Noise of several colors, white at the back to 1/f^2 in front.
    ax = panel(fig, fit(square, (0.05, 0.60, 0.52, 0.33)), (0, 1), (-1.2, 6.6))
    s = np.linspace(0, 1, 900)
    alphas = np.linspace(0, 2, 6)
    for k, a in enumerate(alphas):
        y = colored_noise(rng, 3600, 1.0, a)[:900]
        y = np.convolve(y, np.ones(5) / 5, mode="same")
        y = 0.55 * y / np.abs(y).max() * 1.6 + (len(alphas) - 1 - k) * 1.05
        rgba = np.tile(TIME(k / (len(alphas) - 1)), (s.size - 1, 1))
        rgba[:, 3] = np.clip(np.minimum(s[:-1], 1 - s[:-1]) / 0.22, 0, 1) ** 1.5
        pts = np.column_stack([s, y])
        ax.add_collection(LineCollection(np.stack([pts[:-1], pts[1:]], axis=1), colors=rgba,
                                         lw=0.95, capstyle="round"))

    # Their spectra.
    ax = panel(fig, fit(square, (0.67, 0.63, 0.26, 0.27)), (-0.08, 1.05), (-0.08, 1.12))
    ax.plot([0, 0, 1], [1.05, 0, 0], color=FAINT, lw=0.9)
    for k, a in enumerate(alphas):
        ax.plot([0.06, 0.96], [0.5 + 0.22 * a, 0.5 - 0.22 * a], color=TIME(k / (len(alphas) - 1)),
                lw=1.1)
    ax.text(1.02, 1.04, r"$S(f) \propto 1/f^{\,\alpha}$", color=SOFT, fontsize=10.5, ha="right",
            va="top")
    ax.text(0.5, -0.07, "frequency", fontsize=8.5, ha="center", va="top")

    # The tilted trap and two ways out over its lowered barrier.
    ax = panel(fig, fit(square, (0.03, 0.03, 0.94, 0.60)), (-3.7, 3.9), (-0.85, 1.5))
    xx = np.linspace(-3.7, 3.9, 800)
    x, e = diffusive_run()
    gradient_line(ax, x[::4], e[::4], lw=0.55, alpha=0.7)
    glow(ax, xx, well(xx), INK, lw=2.0, strength=0.8)
    bead(ax, x[-1], e[-1], WARM, size=6)

    xb, eb = ballistic_run()
    glow(ax, xb, eb, WARM, lw=1.7)
    arrowhead(ax, xb[-2], eb[-2], xb[-1] - xb[-2], eb[-1] - eb[-2], WARM)
    bead(ax, X_MIN, well(X_MIN), BLUE)

    ax.text(2.75, e[-1] - 0.1, "diffusive", color=WARM, fontsize=9, ha="center", va="top")
    ax.text(2.9, eb[-1] + 0.09, "ballistic", color=WARM, fontsize=9, ha="center")


# --------------------------------------------------------------------------
# Quantum first-passage times, measured stroboscopically
# --------------------------------------------------------------------------

def heating_runs(rng, runs, steps, rate, sub=40):
    """Phonon number of a noise-heated oscillator, sampled once per measurement.

    Between measurements n jumps up at rate*(n+1) and down at rate*n.
    """
    n = np.zeros(runs, dtype=int)
    out = np.zeros((steps + 1, runs), dtype=int)
    for k in range(1, steps + 1):
        for _ in range(sub):
            u = rng.random(runs)
            up = u < rate / sub * (n + 1)
            down = (u > 1 - rate / sub * n) & ~up
            n = n + up - down
        out[k] = n
    return out


def electrode(ax, pts, shade_from):
    """A flat metal piece: dark gradient fill with a thin bright outline."""
    pts = np.asarray(pts, dtype=float)
    patch = Polygon(pts, closed=True, fc="none", ec=METAL, lw=1.1, joinstyle="round", zorder=3)
    ax.add_patch(patch)
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    ramp = np.linspace(0, 1, 64)[:, None]
    if shade_from == "top":
        ramp = ramp[::-1]
    cmap = LinearSegmentedColormap.from_list("metal", ["#4a4350", "#141a2c"])
    im = ax.imshow(ramp, extent=(x0, x1, y0, y1), origin="lower", cmap=cmap, aspect="auto",
                   zorder=2)
    im.set_clip_path(patch)


def draw_trap(ax):
    """Side view of a blade trap: two blades, two endcap needles, one ion."""
    blade = [(-1.0, 1.6), (1.0, 1.6), (1.0, 1.12), (0.5, 0.4), (-0.5, 0.4), (-1.0, 1.12)]
    electrode(ax, blade, "bottom")
    electrode(ax, [(x, -y) for x, y in blade], "top")
    for sign in (1, -1):
        ax.plot([-1.0, 1.0], [sign * 1.12] * 2, color=METAL, lw=0.6, alpha=0.5, zorder=4)
        needle = [(1.5, 0.075), (0.72, 0.075), (0.56, 0.0), (0.72, -0.075), (1.5, -0.075)]
        electrode(ax, [(sign * x, y) for x, y in needle], "bottom")
    th = np.linspace(0, 2 * np.pi, 200)
    for r, a in ((0.16, 0.5), (0.27, 0.32), (0.38, 0.18)):
        ax.plot(1.25 * r * np.cos(th), 0.8 * r * np.sin(th), color=BLUE, lw=0.7, alpha=a)
    # Readout laser, passing between a needle and a blade.
    xs = np.array([-1.5, 1.5])
    for lw, a in ((7, 0.05), (3.5, 0.1), (1.0, 0.55)):
        ax.plot(xs, 0.2 * xs, color=BLUE, lw=lw, alpha=a, zorder=1)
    bead(ax, 0, 0, BLUE, size=6.5)


def draw_qfptd(fig, square):
    backdrop(fig, 0.3, 0.5, 0.75)
    steps, nb, rate = 5, 6, 1.0
    rng = np.random.default_rng(5)
    ns = heating_runs(rng, 4000, steps, rate)
    hit = ns >= nb
    first = np.where(hit.any(axis=0), hit.argmax(axis=0), -1)

    w = 0.37
    h = w * (1 if square else 4 / 3) * 3.5 / 3.0
    ax = panel(fig, (0.02, 0.5 - h / 2, w, h), (-1.5, 1.5), (-1.75, 1.75))
    draw_trap(ax)

    # Strobe timeline: one column per measurement.
    x0, x1 = 0.44, 0.975
    col = lambda k: x0 + (k + 0.6) / (steps + 1.2) * (x1 - x0)
    y_frames = 0.70 if not square else 0.665
    fw = 0.074

    ax = panel(fig, fit(square, (x0, 0.865, x1 - x0, 0.06)), (-0.6, steps + 0.6), (-0.2, 1.3))
    t = np.linspace(-0.6, steps + 0.6, 1200)
    pulses = sum(np.exp(-((t - k) / 0.055) ** 2) for k in range(steps + 1))
    glow(ax, t, pulses, BLUE, lw=1.0, strength=0.8)

    # Snapshots: the heated ion's phase-space distribution at each measurement.
    lim = 5.4
    g = np.linspace(-lim, lim, 240)
    gx, gp = np.meshgrid(g, g)
    th = np.linspace(0, 2 * np.pi, 200)
    radius = np.sqrt(2 * nb + 1)
    for k in range(steps + 1):
        ax = fig.add_axes(square_box(square, col(k), y_frames, fw))
        var = rate * k + 0.5
        blob = np.exp(-(gx**2 + gp**2) / (2 * var)) ** 0.75
        ax.imshow(blob, extent=(-lim, lim, -lim, lim), cmap=HEAT, vmin=0, vmax=1, origin="lower")
        ax.plot(radius * np.cos(th), radius * np.sin(th), color=WARM, lw=0.7, ls=(0, (2.5, 2.5)))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor(BG)
        for side in ax.spines.values():
            side.set_color(BLUE)
            side.set_linewidth(0.7)
            side.set_alpha(0.7)

    # Single-shot energy readings climbing to the threshold.
    ax = panel(fig, fit(square, (x0, 0.10, x1 - x0, 0.44)), (-0.6, steps + 0.6), (-0.9, nb + 3.6))
    ax.fill_between([-0.6, steps + 0.6], nb, nb + 3.6, color=WARM, alpha=0.07, lw=0)
    ax.plot([-0.6, steps + 0.6], [nb, nb], color=WARM, lw=1.1, ls=DASH)
    for k in range(steps + 1):
        ax.plot([k, k], [-0.9, nb + 3.6], color=BLUE, lw=0.7, alpha=0.28, ls=(0, (1.5, 3)))
    picks = [next(i for i in range(ns.shape[1]) if first[i] == k and ns[k, i] <= nb + cap
                  and ns[k - 1, i] >= floor)
             for k, cap, floor in ((3, 2, 2), (4, 1, 3), (5, 0, 2), (5, 2, 4))]
    for j, i in enumerate(picks):
        k = np.arange(first[i] + 1)
        main = j == 1
        if main:
            glow(ax, k, ns[k, i], BLUE, lw=1.5)
        else:
            ax.plot(k, ns[k, i], color=BLUE, lw=0.9, alpha=0.4)
        ax.plot(k[:-1], ns[k[:-1], i], "o", ms=4.2 if main else 3, color=BLUE,
                alpha=1 if main else 0.55, mec="none")
        if main:
            bead(ax, first[i], ns[first[i], i], WARM, size=5.5)
        else:
            ax.plot(first[i], ns[first[i], i], "o", ms=4, color=WARM, alpha=0.75, mec="none")
    ax.text(-0.5, nb + 0.35, "threshold", color=WARM, fontsize=8.5, ha="left", va="bottom")
    ax.text(steps + 0.6, -0.75, "time", fontsize=8.5, ha="right", va="top")
    ax.plot([-0.6, steps + 0.6], [-0.55, -0.55], color=FAINT, lw=0.9)
    arrowhead(ax, steps + 0.5, -0.55, 0.1, 0, FAINT, size=7)
    ax.text(-0.72, (nb - 0.5) / 2, "energy", fontsize=8.5, rotation=90, ha="right", va="center")


# --------------------------------------------------------------------------
# Quantum-classical crossover
# --------------------------------------------------------------------------

def fock_wigner(n, x, p):
    r2 = x**2 + p**2
    coef = np.zeros(n + 1)
    coef[n] = 1
    return (-1) ** n / np.pi * np.exp(-r2) * lagval(2 * r2, coef)


def fock_density(n, x):
    coef = np.zeros(n + 1)
    coef[n] = 1
    norm = 2.0**n * math.factorial(n) * np.sqrt(np.pi)
    return hermval(x, coef) ** 2 * np.exp(-x**2) / norm


def crosshair(ax, lim):
    ax.plot([-lim, lim], [0, 0], color=FAINT, lw=0.7, alpha=0.8, zorder=0)
    ax.plot([0, 0], [-lim, lim], color=FAINT, lw=0.7, alpha=0.8, zorder=0)


def draw_crossover(fig, square):
    """An n = 9 Wigner function, the oscillator, and the classical orbit of the same energy."""
    backdrop(fig, 0.5, 0.5, 0.7)
    n, lim = 9, 5.9
    amp = np.sqrt(2 * n + 1)
    side = 0.31
    yc = 0.5

    ax = panel(fig, square_box(square, 0.185, yc, side), (-lim, lim), (-lim, lim))
    g = np.linspace(-lim, lim, 700)
    x, p = np.meshgrid(g, g)
    wig = fock_wigner(n, x, p)
    vmax = 0.36 * np.abs(wig).max()
    rgba = DIVERGING(np.clip(0.5 + 0.5 * wig / vmax, 0, 1))
    rgba[..., 3] = np.clip(np.abs(wig) / (0.25 * vmax), 0, 1)
    ax.imshow(rgba, extent=(-lim, lim, -lim, lim), origin="lower", interpolation="bilinear")
    crosshair(ax, lim)

    # The oscillator: energy ladder, the n = 9 density, and the classical turning points.
    wbox = square_box(square, 0.5, yc, 0.25)
    wbox = (wbox[0], wbox[1] - 0.12 * wbox[3], wbox[2], wbox[3] * 1.24)
    ax = panel(fig, wbox, (-5.6, 5.6), (-0.6, 14.6))
    xx = np.linspace(-5.35, 5.35, 500)
    for level in range(13):
        half = np.sqrt(2 * level + 1)
        ax.plot([-half, half], [level + 0.5] * 2, color=FAINT, lw=0.8)
    glow(ax, xx, 0.5 * xx**2, INK, lw=1.8, strength=0.8)
    dens = fock_density(n, xx)
    lift = n + 0.5 + 9.0 * dens
    ax.fill_between(xx, n + 0.5, lift, color=BLUE, alpha=0.28, lw=0)
    glow(ax, xx, lift, BLUE, lw=1.2, strength=0.7)
    ax.plot([-amp, amp], [n + 0.5] * 2, color=WARM, lw=1.0, ls=DASH)
    bead(ax, amp, n + 0.5, WARM, size=5.5)
    bead(ax, -amp, n + 0.5, WARM, size=5.5)

    # Classical oscillator with the n = 9 energy, kicked by weak white noise.
    ax = panel(fig, square_box(square, 0.815, yc, side), (-lim, lim), (-lim, lim))
    crosshair(ax, lim)
    rng = np.random.default_rng(3)
    dt, steps = 0.02, 2800
    xs, ps = np.empty(steps), np.empty(steps)
    xc, pc = amp, 0.0
    kicks = rng.normal(scale=0.26 * np.sqrt(dt), size=steps)
    for i in range(steps):
        xc, pc = xc * np.cos(dt) + pc * np.sin(dt), pc * np.cos(dt) - xc * np.sin(dt) + kicks[i]
        xs[i], ps[i] = xc, pc
    th = np.linspace(0, 2 * np.pi, 300)
    glow(ax, amp * np.cos(th), amp * np.sin(th), WARM, lw=1.5)
    fade = LinearSegmentedColormap.from_list("fade", [to_rgba(WARM, 0.0), to_rgba(WARM, 0.8)])
    gradient_line(ax, xs, ps, cmap=fade, lw=0.7)
    bead(ax, xs[-1], ps[-1], WARM, size=6)


FIGURES = {
    "escape": (draw_escape, "colored-noise-escape"),
    "qfptd": (draw_qfptd, "qfptd-experiment"),
    "crossover": (draw_crossover, "quantum-classical-crossover"),
}

if __name__ == "__main__":
    for key in sys.argv[1:] or FIGURES:
        save(*FIGURES[key])
