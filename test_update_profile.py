"""Regression checks for the profile SVG's columns and value alignment."""

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

import update_profile as profile


class ProfileLayoutTests(unittest.TestCase):
    """Exercise the actual renderer without network requests or credentials."""

    def test_columns_and_values(self):
        """Fill the left 40% with proportional art and enlarge the stats column."""
        for mode in profile.PALETTES:
            for value in (0, 1234, 999999999999):
                with self.subTest(mode=mode, value=value):
                    stats = dict.fromkeys(
                        ("followers", "repos", "contributed", "stars", "commits",
                         "loc_add", "loc_del", "loc"), value
                    )
                    root = ET.fromstring(profile.render(mode, stats))
                    ns = {"s": "http://www.w3.org/2000/svg"}
                    art = root.find(".//s:g[@id='art']", ns)
                    info = root.find("s:g[@id='info']", ns)
                    self.assertIsNotNone(art)
                    self.assertIsNotNone(info)
                    if value < 10000:
                        self.assertAlmostEqual(float(root.get("font-size")), 13.125)
                    rows = art.findall("s:text", ns)
                    self.assertEqual(len(rows), len(profile.ART_LINES))
                    for row in rows:
                        self.assertLessEqual(float(row.get("x")), 0)
                        self.assertGreaterEqual(
                            float(row.get("x")) + float(row.get("textLength")), 352
                        )
                    self.assertGreaterEqual(float(rows[0].get("y")), 0)
                    self.assertLess(float(rows[-1].get("y")), 600)
                    self.assertGreater(float(rows[len(rows) // 2].get("y")), 0)
                    self.assertLess(float(rows[len(rows) // 2].get("y")), 600)
                    self.assertIsNotNone(root.find("s:g[@clip-path='url(#art-column-clip)']", ns))
                    clip = root.find("s:defs/s:clipPath[@id='art-column-clip']/s:rect", ns)
                    self.assertEqual((clip.get("width"), clip.get("height")), ("352", "600"))
                    for actual, original in zip(rows, profile.ART_LINES):
                        expected = ET.fromstring(f"<text>{original}</text>")
                        self.assertEqual("".join(actual.itertext()), "".join(expected.itertext()))
                        self.assertEqual([span.get("fill") for span in actual],
                                         [span.get("fill") for span in expected])
                    for row in info.findall("s:text", ns):
                        self.assertLess(float(row.get("y")), 584)
                        for span in row:
                            self.assertGreaterEqual(float(span.get("x")), 360)
                            self.assertLessEqual(float(span.get("x")), 864)
                        text = "".join(row.itertext())
                        if "Stars:" in text or "Followers:" in text:
                            self.assertEqual(row[-1].get("text-anchor"), "end")
                            self.assertEqual(float(row[-1].get("x")), 864)
                            self.assertEqual(row[-1].text, f"{value:,}")

    def test_art_edge_fade(self):
        """Fade every edge through luminance masks while leaving the center opaque."""
        stats = dict.fromkeys(
            ("followers", "repos", "contributed", "stars", "commits",
             "loc_add", "loc_del", "loc"), 0
        )
        ns = {"s": "http://www.w3.org/2000/svg"}
        for mode in profile.PALETTES:
            root = ET.fromstring(profile.render(mode, stats))
            art = root.find(".//s:g[@id='art']", ns)
            self.assertIsNone(art.get("mask"))
            for axis in ("x", "y"):
                self.assertIsNotNone(root.find(f".//s:g[@mask='url(#fade-{axis}-mask)']", ns))
                gradient = root.find(f"s:defs/s:linearGradient[@id='fade-{axis}']", ns)
                self.assertIsNotNone(gradient)
                self.assertEqual(gradient.get("gradientUnits"), "userSpaceOnUse")
                self.assertEqual([stop.get("stop-color") for stop in gradient],
                                 ["black", "white", "white", "black"])
                self.assertEqual(gradient[1].get("offset"), "2%" if axis == "x" else "1.5%")
                mask = root.find(f"s:defs/s:mask[@id='fade-{axis}-mask']", ns)
                self.assertEqual(mask.get("maskContentUnits"), "userSpaceOnUse")
                self.assertEqual(mask.get("maskUnits"), "userSpaceOnUse")
                self.assertEqual((mask.get("width"), mask.get("height")), ("352", "600"))
                self.assertEqual(mask[0].get("fill"), f"url(#fade-{axis})")

    def test_line_widths(self):
        """Dotted leaders terminate at the same character boundary as rules."""
        stats = dict.fromkeys(
            ("followers", "repos", "contributed", "stars", "commits",
             "loc_add", "loc_del", "loc"), 1234
        )
        for row in profile.info_lines(stats):
            if row:
                self.assertEqual(len("".join(text for text, _ in row)), profile.W)

    def test_animation_and_static_fallback(self):
        """Keep stats and source art intact while shimmer rises through the top."""
        stats = dict.fromkeys(("followers", "repos", "contributed", "stars", "commits",
                              "loc_add", "loc_del", "loc"), 1234)
        ns = {"s": "http://www.w3.org/2000/svg"}
        for mode in profile.PALETTES:
            with self.subTest(mode=mode):
                static = ET.fromstring(profile.render(mode, stats, animated=False))
                moving = ET.fromstring(profile.render(mode, stats))
                self.assertEqual(ET.tostring(static.find("s:g[@id='info']", ns)),
                                 ET.tostring(moving.find("s:g[@id='info']", ns)))
                moving_art = moving.find(".//s:g[@id='art']", ns)
                top = moving_art[0].findall("s:tspan[@class='existing-aura']", ns)
                self.assertTrue(top)
                for row in moving_art:
                    cells = row.findall("s:tspan[@class='existing-aura']", ns)
                    self.assertLessEqual(len({cell.get('style').split('animation-delay:')[1]
                                              for cell in cells}), 1)
                    for cell in cells:
                        del cell.attrib['class']
                        del cell.attrib['style']
                self.assertEqual(ET.tostring(static.find(".//s:g[@id='art']", ns)),
                                 ET.tostring(moving_art))
                aura = moving.find(".//s:g[@id='aura']", ns)
                self.assertIsNotNone(aura)
                self.assertIsNone(static.find(".//s:g[@id='aura']", ns))
                self.assertFalse(moving.findall('.//s:script', ns))
                self.assertFalse(aura.findall('.//s:path', ns))
                self.assertIsNone(moving.find(".//s:g[@id='surrounding-aura']", ns))
                css = moving.find('s:defs/s:style', ns).text
                self.assertIn('prefers-reduced-motion: reduce', css)
                self.assertIn('.existing-aura { animation: none !important; }', css)
        readme = Path(__file__).with_name('README.md').read_text()
        self.assertLess(readme.index('light_static_mode.svg'), readme.index('light_mode.svg'))
        self.assertLess(readme.index('dark_static_mode.svg'), readme.index('dark_mode.svg'))


if __name__ == "__main__":
    unittest.main()
