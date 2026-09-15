import unittest

from protocols.obd2 import OBD2


class TestOBD2Parsing(unittest.TestCase):
    def test_mode01_single_pid(self):
        frames = OBD2._to_bytes(["41 0C 1A F8"], 0x01, pid=0x0C)
        self.assertEqual(frames, [bytes.fromhex("1AF8")])

    def test_mode01_ignores_invalid_lines(self):
        frames = OBD2._to_bytes(
            ["SEARCHING...", "NODATA", "41 05 7B"],
            0x01,
            pid=0x05,
        )
        self.assertEqual(frames, [bytes.fromhex("7B")])

    def test_dtc_payload_keeps_normal_dtc_bytes(self):
        payload = bytes.fromhex("0100")
        self.assertEqual(OBD2._dtc_payload(payload), payload)


    def test_supported_pids_ignores_short_response(self):
        class Adapter:
            def command(self, command):
                return ["41 00 80"]

        obd = OBD2(Adapter())
        self.assertEqual(obd.supported_pids(), set())

    def test_vin_extracts_exact_17_characters(self):
        class Adapter:
            def command(self, command):
                return ["49 02 01 57 56 57 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A 5A"]

        obd = OBD2(Adapter())
        self.assertEqual(obd.vin(), "WVWZZZZZZZZZZZZZZ")

    def test_clear_requires_positive_confirmation(self):
        class Adapter:
            def command(self, command):
                return ["44"]

        obd = OBD2(Adapter())
        self.assertTrue(obd.clear_trouble_codes())

    def test_clear_rejects_missing_confirmation(self):
        class Adapter:
            def command(self, command):
                return ["NO DATA"]

        obd = OBD2(Adapter())
        with self.assertRaises(Exception):
            obd.clear_trouble_codes()


if __name__ == "__main__":
    unittest.main()
