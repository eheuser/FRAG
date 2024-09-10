import unittest
import logging

from artifacts.parsers.pdf_file import identify_pdf, parse_pdf
from artifacts.parsers.pe_file import identify_pe, parse_pe
from artifacts.parsers.mft_file import identify_mft, parse_mft
from artifacts.parsers.registry_file import identify_reg, parse_reg
from artifacts.parsers.evtx_file import identify_evtx, parse_evtx

from artifacts.event_filter import filter_mft_path, filter_evtx_event, is_windows_autorun, is_lol_bin, references_lol_bin


logging.basicConfig(
    level=logging.WARN, format=f"%(asctime)s.%(msecs)03d %(levelname)s:%(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestParsers(unittest.TestCase):
    def test_evtx(self):
        self.assertEqual(
            True,
            identify_evtx("test/files/sysmon.evtx", logger),
        )
        self.assertEqual(
            len(parse_evtx("test/files/sysmon.evtx", logger)),
            1,
        )

    def test_mft(self):
        self.assertEqual(
            True,
            identify_mft("test/files/mft_test", logger),
        )
        self.assertEqual(
            len(parse_mft("test/files/mft_test", logger)),
            0,
        )

    def test_pdf(self):
        self.assertEqual(
            True,
            identify_pdf("test/files/sample.pdf", logger),
        )
        self.assertEqual(
            len(parse_pdf("test/files/sample.pdf", logger)),
            1,
        )

    def test_exe(self):
        self.assertEqual(
            True,
            identify_pe("test/files/upx.exe", logger),
        )
        self.assertEqual(
            len(parse_pe("test/files/upx.exe", logger)),
            1,
        )

    def test_reg(self):
        self.assertEqual(
            True,
            identify_reg("test/files/Amcache", logger),
        )
        self.assertEqual(
            len(parse_reg("test/files/Amcache", logger)),
            315,
        )

    def test_event_filter(self):
        self.assertEqual(
            True,
            filter_mft_path("Users\\Foo.exe"),
        )

        event = {
            "Event": {
                "EventData": {
                    "Image": "C:\\Windows\\System32\\cmd.exe",
                },
                "System": {
                    "Channel": "Microsoft-Windows-Sysmon/Operational",
                    "EventID": 1,
                    "TimeCreated": {
                        "#attributes": {
                            "SystemTime": "2023-03-08T02:40:10.998531Z",
                        }
                    }
                }
            }
        }
        self.assertEqual(
            (event, 1678243210.998531),
            filter_evtx_event(event),
        )

        self.assertEqual(
            True,
            is_windows_autorun("Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
        )

        self.assertEqual(
            True,
            is_lol_bin("C:\\Windows\\System32\\WindowsPowerShell\\v1. 0\\powershell.exe"),
        )

        self.assertEqual(
            True,
            references_lol_bin("\"powershell.exe\""),
        )