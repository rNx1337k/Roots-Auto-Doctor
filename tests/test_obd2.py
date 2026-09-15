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


if __name__ == "__main__":
    unittest.main()
