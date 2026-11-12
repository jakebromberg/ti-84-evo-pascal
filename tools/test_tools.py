"""Tests for the screenshot tools, using a real screenshot and the saved device reports."""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_screenshot  # noqa: E402
import decode_bits  # noqa: E402
import screen_kind  # noqa: E402
import screenshot  # noqa: E402
import triangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIANGLE_SHOT = os.path.join(ROOT, "docs", "pasfast5.png")
REPORT_SHOT = os.path.join(ROOT, "docs", "device-reports", "GRPROBE2.png")


class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.rows = screenshot.load(TRIANGLE_SHOT)

    def test_size(self):
        self.assertEqual((len(self.rows), len(self.rows[0])), (240, 320 * 3))

    def test_finished_triangle_is_pixel_exact(self):
        self.assertEqual(check_screenshot.wrong_pixels(self.rows), 0)

    def test_finished_triangle_has_nothing_outside_it(self):
        self.assertEqual(check_screenshot.stray_pixels(self.rows), 0)

    def test_a_different_screen_is_not_mistaken_for_the_triangle(self):
        other = screenshot.load(REPORT_SHOT)
        self.assertGreater(check_screenshot.wrong_pixels(other), 10000)
        self.assertGreater(check_screenshot.stray_pixels(other), 100)

    def test_program_screen_is_classified_as_drawing(self):
        self.assertEqual(screen_kind.kind(self.rows), "drawing")

    def test_triangle_screen_has_no_report_block(self):
        dark = decode_bits.dark_from_png(TRIANGLE_SHOT)
        self.assertRaises(ValueError, decode_bits.decode, dark)


class RealReportTests(unittest.TestCase):
    def test_probe_screenshot_decodes_to_the_saved_report(self):
        reports = os.path.join(ROOT, "docs", "device-reports")
        text = decode_bits.decode(decode_bits.dark_from_png(os.path.join(reports, "GRPROBE2.png")))
        with open(os.path.join(reports, "GRPROBE2.txt")) as f:
            self.assertEqual(text, f.read().rstrip("\n"))


class TriangleTests(unittest.TestCase):
    def test_pixel_count_and_corners(self):
        pixels = triangle.expected()
        self.assertEqual(len(pixels), 22155)
        self.assertEqual(pixels[(159, 0)], 1)
        self.assertEqual(pixels[(55, 209)], 1)
        self.assertEqual(pixels[(264, 209)], 1)


class DecodeRoundTripTests(unittest.TestCase):
    def test_probe_dry_run_decodes_to_its_own_report(self):
        probe = os.path.join(ROOT, "probes", "MODDUMP.py")
        result = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "validate.py"), "--run-only", probe],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        out = os.path.join(ROOT, "tools", "standins", "out.txt")
        text = decode_bits.decode(decode_bits.dark_from_dry_run(out))
        self.assertIn("[ti_draw]", text)
        self.assertIn("importable:", text)


class FallbackTests(unittest.TestCase):
    def test_pasfast6_is_exact_without_a_dotted_pen(self):
        """If setPen does not make dotted lines, PASFAST6 must notice, say so and still draw the exact picture."""
        program = os.path.join(ROOT, "programs", "PASFAST6.py")
        result = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "validate.py"), program],
                                capture_output=True, text=True, env=dict(os.environ, STANDIN_PEN="solid"))
        self.assertEqual(result.returncode, 0, result.stdout)
        with open(os.path.join(ROOT, "tools", "standins", "out.txt")) as f:
            texts = [line for line in f if line.startswith("T ")]
        self.assertTrue(any(line.rstrip().endswith("1 off") for line in texts), texts)


class MemoryTests(unittest.TestCase):
    def test_pasfast6_plans_in_a_small_heap(self):
        """PASFAST6 must compile and plan the picture in a 200k MicroPython heap on this computer.

        The calculator ran out of memory in the planner when the same measurement gave about 280k, and ran PASFAST5 at 277k only with little else stored, so 200k leaves a margin. The numbers are for 64-bit MicroPython, where lists take twice the room they do on the calculator.
        """
        with open(os.path.join(ROOT, "programs", "PASFAST6.py")) as f:
            source = f.read()
        self.assertEqual(source.count("COMPUTE_ONLY = False"), 1)
        with tempfile.TemporaryDirectory() as folder:
            program = os.path.join(folder, "PASFAST6.py")
            with open(program, "w") as f:
                f.write(source.replace("COMPUTE_ONLY = False", "COMPUTE_ONLY = True"))
            result = subprocess.run(["micropython", "-X", "heapsize=200k", "runprog.py", program],
                                    cwd=os.path.join(ROOT, "tools", "standins"), capture_output=True, text=True)
        with open(os.path.join(ROOT, "tools", "standins", "out.txt")) as f:
            error = f.readline().strip()
        self.assertEqual(error, "ERR", result.stdout[-400:])


if __name__ == "__main__":
    unittest.main()
