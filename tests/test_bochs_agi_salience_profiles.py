from pathlib import Path
import json
import shutil
import tempfile
import unittest

from scripts.bochs_agi_salience_profiles import (
    MANIFEST_NAME,
    PROFILES,
    REPO_ROOT,
    apply_profile,
    build_manifest,
    profile_score,
    write_profiles,
)


class SalienceProfileGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_path = REPO_ROOT / "bochs" / "agi.bochsrc"
        self.base_text = self.base_path.read_text(encoding="utf-8")

    def test_apply_profile_writes_salience_header(self) -> None:
        max_grip = next(p for p in PROFILES if p.name == "max-grip")
        rendered = apply_profile(self.base_text, max_grip)
        expected_vector = ", ".join(f"{k}={v}" for k, v in max_grip.salience_vector.items())
        self.assertIn("# GENERATED PROFILE: max-grip", rendered)
        self.assertIn(f"SALIENCE_VECTOR: {expected_vector}", rendered)
        self.assertIn("# SALIENCE_SCORE:", rendered)
        self.assertIn("# MANIFEST: bochs/profiles/manifest.json", rendered)
        self.assertIn("clock: sync=slowdown, time0=0, rtc_sync=0", rendered)

    def test_write_profiles_creates_all_profiles_and_manifest(self) -> None:
        tempdir = Path(tempfile.mkdtemp(prefix="salience-profiles-"))
        try:
            written, manifest_path = write_profiles(self.base_path, tempdir)
            expected = {f"agi-{p.name}.bochsrc" for p in PROFILES}
            actual = {p.name for p in tempdir.glob("*.bochsrc")}
            self.assertEqual(expected, actual)
            self.assertEqual(expected, {p.name for p in written})
            self.assertEqual(tempdir / MANIFEST_NAME, manifest_path)
            self.assertTrue(manifest_path.exists())
        finally:
            shutil.rmtree(tempdir)

    def test_throughput_profile_uses_fast_clock_mode(self) -> None:
        throughput = next(p for p in PROFILES if p.name == "throughput")
        rendered = apply_profile(self.base_text, throughput)
        self.assertIn("clock: sync=none, time0=0, rtc_sync=0", rendered)
        self.assertIn("quantum=64, ips=400000000", rendered)

    def test_profile_scores_are_normalized_and_distinct(self) -> None:
        scores = {profile.name: profile_score(profile) for profile in PROFILES}
        self.assertEqual(set(scores), {"max-grip", "balanced", "throughput"})
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        self.assertGreater(scores["balanced"], scores["throughput"])

    def test_manifest_is_machine_readable_profile_contract(self) -> None:
        manifest = build_manifest(self.base_path, REPO_ROOT / "bochs" / "profiles")
        self.assertEqual(manifest["schema_version"], "1.0.0")
        self.assertEqual(manifest["project"], "x86ml")
        self.assertEqual(manifest["profile_count"], len(PROFILES))
        self.assertEqual(
            {profile["name"] for profile in manifest["profiles"]},
            {"max-grip", "balanced", "throughput"},
        )
        for profile in manifest["profiles"]:
            self.assertTrue(profile["file"].startswith("agi-"))
            self.assertIn("cpu", profile["replacement_directives"])
            self.assertIn("gdbstub:1234", profile["control_surfaces"].values())
            self.assertGreaterEqual(profile["salience_score"], 0.0)
            self.assertLessEqual(profile["salience_score"], 1.0)
        json.dumps(manifest)


if __name__ == "__main__":
    unittest.main()
