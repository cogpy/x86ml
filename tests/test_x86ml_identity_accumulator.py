import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import x86ml_identity_accumulator as accumulator  # noqa: E402
import x86ml_resident_workshop as workshop  # noqa: E402


class IdentityAccumulatorTests(unittest.TestCase):
    def make_memory(self, resident_id="manuscog", channel="self", summary="A bounded memory summary."):
        return {
            "schema_version": accumulator.SOURCE_MEMORY_SCHEMA_VERSION,
            "resident_id": resident_id,
            "memory_channel": channel,
            "source_kind": "test",
            "source_ref": "unit-test",
            "summary": summary,
            "salience": {"truth": 10, "beauty": 8, "kinship": 9, "agency": 7},
            "tags": ["identity", "test"],
        }

    def write_temp_workshop(self, root: Path) -> Path:
        workshop_dir = root / "workshop"
        workshop.write_workshop(workshop_dir=workshop_dir, profile_manifest=root / "missing-profile-manifest.json")
        return workshop_dir

    def write_memory_source(self, workshop_dir: Path, *events) -> Path:
        source = workshop_dir / "memory" / "test-memories.jsonl"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
        return source

    def test_source_memory_digest_is_canonical(self):
        left = self.make_memory()
        right = dict(reversed(list(left.items())))
        self.assertEqual(accumulator.stable_hash(left), accumulator.stable_hash(right))

    def test_rejects_unknown_resident(self):
        with tempfile.TemporaryDirectory() as tmp:
            workshop_dir = self.write_temp_workshop(Path(tmp))
            source = self.write_memory_source(workshop_dir, self.make_memory(resident_id="ghost"))
            with self.assertRaises(accumulator.AccumulationError):
                accumulator.build_accumulation(workshop_dir, (source,))

    def test_rejects_unknown_memory_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            workshop_dir = self.write_temp_workshop(Path(tmp))
            source = self.write_memory_source(workshop_dir, self.make_memory(channel="dream-static"))
            with self.assertRaises(accumulator.AccumulationError):
                accumulator.build_accumulation(workshop_dir, (source,))

    def test_write_accumulation_creates_state_log_and_manifest_pointers(self):
        with tempfile.TemporaryDirectory() as tmp:
            workshop_dir = self.write_temp_workshop(Path(tmp))
            source = self.write_memory_source(
                workshop_dir,
                self.make_memory(resident_id="manuscog", channel="self", summary="ManusCog remembers the recovery predicate."),
                self.make_memory(resident_id="echo", channel="kin", summary="Echo remembers the song-stone relation."),
            )
            manifest_path, state_paths, log_path = accumulator.write_accumulation(workshop_dir, (source,))

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["accumulation_log"], "iterations/identity-accumulation.jsonl")
            self.assertEqual(manifest["state_dir"], "state")
            self.assertEqual(manifest["identity_accumulation"]["event_count"], 2)
            self.assertFalse(manifest["identity_accumulation"]["safety"]["runs_bochs"])
            self.assertEqual(len(state_paths), len(workshop.RESIDENTS))

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["iteration_index"], 1)
            self.assertEqual(records[0]["integration_mode"], "bounded_memory_digest")

            manuscog_state = json.loads((workshop_dir / "state" / "manuscog.identity-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manuscog_state["event_count"], 1)
            self.assertEqual(manuscog_state["channel_counts"]["self"], 1)
            self.assertEqual(manuscog_state["salience_totals"]["truth"], 10)
            self.assertNotEqual(manuscog_state["seed_identity_hash"], manuscog_state["accumulated_identity_hash"])

    def test_committed_seed_memory_source_covers_dove9_residents(self):
        manifest = json.loads((REPO_ROOT / "workshop" / "manifest.json").read_text(encoding="utf-8"))
        expected_residents = {entry["resident_id"] for entry in manifest["residents"]}
        source = REPO_ROOT / "workshop" / "memory" / "seed-memories.jsonl"
        actual_residents = set()
        for _, event in accumulator.iter_jsonl(source):
            normalized = accumulator.normalize_memory_event(event, expected_residents)
            actual_residents.add(normalized["resident_id"])
            self.assertLessEqual(len(normalized["summary"]), accumulator.MAX_SUMMARY_CHARS)
        self.assertEqual(actual_residents, expected_residents)


if __name__ == "__main__":
    unittest.main()
