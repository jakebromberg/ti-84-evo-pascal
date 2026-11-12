# Prior art for the optimizations

A survey of earlier work behind each technique the programs in this repo use. It comes from web searches made on 2026-11-11, so it is a starting point and not a complete literature review: not finding a precedent does not show there is none.

## Summary

Almost every technique has clear prior art. The parts with no precedent found are the combination, three specific tricks (listed at the end) and the measurements of the Evo itself.

## Direct precedents

| What the programs do | Prior art | How close |
|---|---|---|
| Call the native `ti_graphics` module instead of `ti_draw` | critor's [exploration of `ti_graphics`](https://tiplanet.org/forum/viewtopic.php?t=23791&p=252807) on the TI-83 Premium CE Edition Python (TI-Planet, 4 May 2020) | Direct. The same function names, the same 320×210 drawing area starting at y = 30, `setPen` taking integers and not names, and `fillPolygon` handling shapes that cross themselves. The Evo's module is evidently the CE's carried over. |
| Pen style 3 for dotted lines (`PASFAST6`) | The same post: `setPen(3, 3)` is undocumented and gives a dotted pattern "made of points" | Direct for the pen value. Not for using it to paint several separate pixels in one call. |
| Fewer, larger drawing calls | critor's [optimized radar animation](https://tiplanet.org/forum/viewtopic.php?f=41&t=23824) (TI-Planet, 12 May 2020): replacing `set_pixel` loops with `ti_graphics` shapes took one revolution from 41 minutes to 18.5 s | Direct. The same principle on the same module. |
| Layered boxes: long ones first, shorter ones on top | [LeetCode 664, "Strange Printer"](https://leetcode.doocs.org/en/lc/664/): the fewest strokes when each stroke paints a run in one color and later strokes cover earlier ones | The exact problem for one row. Its O(n³) interval method gives the best possible layering, which the README notes is too slow on the calculator; the programs use a greedy shortcut. |
| A whole row in one integer, next row `(R + (R << 8)) & mask` | Rows of Pascal's triangle as [powers of 11](https://ecommons.udayton.edu/epumd/vol1/iss1/3), which holds in any base; [powers of 101, 1001 and so on](https://pmc.ncbi.nlm.nih.gov/articles/PMC9668569) to leave room between entries; [Kronecker substitution](https://arxiv.org/pdf/0712.4046), which packs a polynomial's coefficients into one large integer | Direct. What the programs add is masking every byte to its remainder mod 16 at each step, so entries never grow into their neighbors. |
| The same, mod 2 | Each row is the row above XOR itself shifted by one; [cellular automaton rules 60 and 90](https://mathworld.wolfram.com/SierpinskiSieve.html) | Direct special case. |
| One color at a time | Sorting draw calls by render state in graphics engines ([Unity](https://docs.unity3d.com/2018.4/Documentation/Manual/DrawCallBatching.html), [PowerVR](https://docs.imgtec.com/starter-guides/powervr-architecture/html/topics/rules/do-group-per-material.html)) | The same idea in another field. |
| `gc.collect()` every 16 rows while planning | [Maximising MicroPython speed](https://docs.micropython.org/en/latest/reference/speed_python.html): collecting regularly reduces fragmentation, and "severe fragmentation can lead to non-recoverable allocation failures" | Direct. It describes the failure the planner hit. |
| Hot loops in a function, calls bound to local names | The same page, on caching object references | Direct. |
| Timing a program without taking screenshots during the run | The [probe effect](https://www.wikipedia.org/wiki/Probe_effect): measuring a system changes its behavior. Cambridge lecture notes advise [not benchmarking while tracing](https://www.cl.cam.ac.uk/teaching/2223/AOS/advopsys-lecture-2-2-probe-effect.pdf) unless the effect is measured | Direct. |

## Background rather than precedent

- **The zero triangles.** [Kummer's theorem](https://www.cecm.sfu.ca/organics/papers/granville/paper/binomial/html/node2.html) (1852) gives the power of 2 dividing a binomial coefficient as a count of carries, which decides when an entry is 0 mod 16. Lucas' theorem and its extension to prime powers by Davis and Webb are surveyed in [Lucas' theorem: its generalizations, extensions and applications](https://arxiv.org/pdf/1409.3820). [Bannink and Buhrman](https://arxiv.org/pdf/1708.07429) prove the Sierpinski-like structure of Pascal's triangle modulo prime powers. [Davis](https://www.fq.math.ca/Scanned/29-1/davis.pdf) treats the triangle modulo 4, [Huard, Spearman and Williams](https://people.math.carleton.ca/~williams/papers/pdf/217.pdf) modulo 8, and [Rowland](https://arxiv.org/pdf/1001.1783) counts the nonzero entries modulo p^α.
- **Drawing a Sierpinski triangle from filled triangles.** The usual recursive construction, for example [Stanford's CS106B assignment](https://web.stanford.edu/class/cs106b/assignments/3-recursion/sierpinski), draws whole triangles and not pixels. `TRIPROBE` and `POLYRULE` tried the same for the zero triangles.
- **Polygon edges, and repair by reading pixels back.** Fill rules such as the [top-left rule](https://learn.microsoft.com/en-us/windows/win32/direct3d9/rasterization-rules) are standard, and Microsoft's page warns that implementations vary. Drawing and then reading pixels back is how [Chromium](https://chromium.googlesource.com/chromium/src/+/HEAD/components/viz/service/display/readback_pixeltest.cc) and Skia test their renderers.
- **Dotted lines.** [OpenGL's line stipple](https://docs.gl/gl2/glLineStipple) is the same mechanism: a bit mask repeated along a line.
- **Boxes from a picture.** Covering a bitmap with the fewest rectangles is [NP-hard](https://arxiv.org/pdf/1910.01193); greedy tools such as [bitmap-to-boxes](https://npmjs.com/package/bitmap-to-boxes) exist.
- **The pixel-block reports.** Showing [QR codes on a microcontroller's display](https://community.element14.com/technologies/embedded/b/blog/posts/improving-user-experience-with-qr-codes-for-microcontrollers) to get data off a device is the nearest thing found.

## The Evo itself

- A [Cemetech thread](https://www.cemetech.net/forum/viewtopic.php?p=317962) on the Evo's Python reportedly puts its heap at about 169 KB, against the 163 KB measured here. The page could not be opened when this was written, so that figure comes from a search engine's summary of it.
- [CalcPlex](https://calcplex.com/python-commands/) lists six of the Evo's `ti_graphics` functions (`drawArc`, `drawImage`, `fillArc`, `hsv_to_rgb`, `setFont`, `string_size`), none of which the programs use.
- TI-Planet's review gives the processor as a [Cortex-M33 at 156 MHz](https://tiplanet.org/forum/viewtopic.php?f=41&t=27365&lang=en).
- No timing of the Evo's drawing calls was found, and no Pascal's triangle program for it. The Sierpinski programs found for earlier TI calculators plot points one at a time, for example with the [chaos game](https://learn.cemetech.net/index.php/TI-BASIC:Sierpinski_Triangle).

## No precedent found

- Drawing the two slanted sides of each zero triangle as lines, which works because every entry on a side has one value (each is the entry above it plus a zero). No statement of that property turned up either, though it follows in one step from the rule that builds the triangle.
- Using a dotted pen to paint several separate pixels with one call.
- The Evo measurements in the README: the 50-corner limit of `fillPolygon` and its cost per corner, how its edges are rounded, and which pixels each pen style paints.
