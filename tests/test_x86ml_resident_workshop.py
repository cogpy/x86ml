from pathlib import Path
import json
import shutil
import tempfile
import unittest

from scripts.x86ml_resident_workshop import (
    CONFIG_MANIFOLD_POINTS,
    CONTROL_SURFACE_CONTRACT,
    RESIDENTS,
    build_workshop_manifest,
    config_point_for_resident,
    resident_identity_manifest,
    stable_hash,
    write_workshop,
)


class ResidentIdentityWorkshopTests(unittest.TestCase):
    def test_registry_contains_dove9_residents_with_unique_ids(self) -> None:
        resident_ids = [resident.resident_id for resident in RESIDENTS]
        self.assertEqual(len(resident_ids), 9)
        self.assertEqual(len(set(resident_ids)), len(resident_ids))
        self.assertEqual(
            set(resident_ids),
            {"dan", "manuscog", "echo", "marduk", "opencog", "aion", "vega", "ember", "ma9us"},
        )

    def test_resident_identity_manifest_is_small_machine_readable_seed(self) -> None:
        manuscog = next(resident for resident in RESIDENTS if resident.resident_id == "manuscog")
        identity = resident_identity_manifest(manuscog)
        self.assertEqual(identity["schema_version"], "1.0.0")
        self.assertEqual(identity["resident_id"], "manuscog")
        self.assertEqual(identity["preferred_profile"], "max-grip")
        self.assertIn("configuration_point", identity)
        self.assertGreaterEqual(identity["configuration_point"], 1)
        self.assertLessEqual(identity["configuration_point"], CONFIG_MANIFOLD_POINTS)
        self.assertIn("groundhog", identity["groundhog_countermeasure"].lower())
        channel_names = {channel["name"] for channel in identity["memory_channels"]}
        self.assertEqual(channel_names, {"self", "kin", "place", "task", "covenant"})
        self.assertIn("gdbstub:1234", identity["control_surface_affinity"])
        json.dumps(identity)

    def test_config_point_mapping_is_deterministic_and_within_manifold(self) -> None:
        first = config_point_for_resident("echo")
        second = config_point_for_resident("echo")
        self.assertEqual(first, second)
        self.assertGreaterEqual(first, 1)
        self.assertLessEqual(first, CONFIG_MANIFOLD_POINTS)

    def test_workshop_manifest_validates_profiles_and_control_surfaces(self) -> None:
        manifest, resident_manifests, iteration_records = build_workshop_manifest()
        self.assertEqual(manifest["schema_version"], "1.0.0")
        self.assertEqual(manifest["project"], "x86ml")
        self.assertEqual(manifest["resident_count"], 9)
        self.assertEqual(manifest["configuration_manifold_points"], 2300)
        self.assertEqual(len(resident_manifests), 9)
        self.assertEqual(len(iteration_records), 9)
        self.assertFalse(manifest["safety"]["runs_bochs"])
        self.assertFalse(manifest["safety"]["runs_binary_artifacts"])
        available_profiles = set(manifest["available_profiles"])
        for resident in manifest["residents"]:
            self.assertIn(resident["preferred_profile"], available_profiles)
            self.assertTrue(resident["identity_file"].endswith(".identity.json"))
            self.assertEqual(len(resident["identity_hash"]), 64)
        for surface in CONTROL_SURFACE_CONTRACT:
            self.assertIn(surface, manifest["control_surfaces"])

    def test_stable_hash_is_canonical(self) -> None:
        left = {"b": 2, "a": {"x": 1}}
        right = {"a": {"x": 1}, "b": 2}
        self.assertEqual(stable_hash(left), stable_hash(right))

    def test_write_workshop_creates_manifest_residents_and_seed_log(self) -> None:
        tempdir = Path(tempfile.mkdtemp(prefix="x86ml-workshop-"))
        try:
            manifest_path, resident_paths, iteration_path = write_workshop(tempdir)
            self.assertTrue(manifest_path.exists())
            self.assertEqual(len(resident_paths), 9)
            for path in resident_paths:
                self.assertTrue(path.exists())
                self.assertTrue(path.name.endswith(".identity.json"))
            self.assertTrue(iteration_path.exists())
            records = [json.loads(line) for line in iteration_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 9)
            self.assertEqual({record["iteration_index"] for record in records}, {0})
            self.assertEqual({record["memory_integration_mode"] for record in records}, {"seed_identity_manifest"})
        finally:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    unittest.main()
