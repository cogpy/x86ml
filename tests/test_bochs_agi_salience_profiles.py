from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.bochs_agi_salience_profiles import (
    PROFILES,
    REPO_ROOT,
    apply_profile,
    write_profiles,
)


class SalienceProfileGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_path = REPO_ROOT / "bochs" / "agi.bochsrc"
        self.base_text = self.base_path.read_text(encoding="utf-8")

    def test_apply_profile_writes_salience_header(self) -> None:
        rendered = apply_profile(self.base_text, PROFILES[0])
        expected_vector = ", ".join(f"{k}={v}" for k, v in PROFILES[0].salience_vector.items())
        self.assertIn("# GENERATED PROFILE: max-grip", rendered)
        self.assertIn(f"SALIENCE_VECTOR: {expected_vector}", rendered)
        self.assertIn("clock: sync=slowdown, time0=0, rtc_sync=0", rendered)

    def test_write_profiles_creates_all_profiles(self) -> None:
        tempdir = Path(tempfile.mkdtemp(prefix="salience-profiles-"))
        try:
            write_profiles(self.base_path, tempdir)
            expected = {f"agi-{p.name}.bochsrc" for p in PROFILES}
            actual = {p.name for p in tempdir.glob("*.bochsrc")}
            self.assertEqual(expected, actual)
        finally:
            shutil.rmtree(tempdir)

    def test_throughput_profile_uses_fast_clock_mode(self) -> None:
        throughput = next(p for p in PROFILES if p.name == "throughput")
        rendered = apply_profile(self.base_text, throughput)
        self.assertIn("clock: sync=none, time0=0, rtc_sync=0", rendered)
        self.assertIn("quantum=64, ips=400000000", rendered)


if __name__ == "__main__":
    unittest.main()
