import unittest
import logging


from modules.frag import FRAG


logging.basicConfig(
    level=logging.WARN, format=f"%(asctime)s.%(msecs)03d %(levelname)s:%(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestFrag(unittest.TestCase):
    def test_drop(self):
        frag = FRAG(logger)
        self.assertEqual(
            True,
            frag.drop_db(),
        )

    def test_connect(self):
        frag = FRAG(logger)
        self.assertEqual(
            True,
            frag.connect_db(),
        )

    def test_ioc(self):
        frag = FRAG(logger)
        self.assertEqual(
            10,
            frag.add_iocs(),
        )

    def test_query(self):
        frag = FRAG(logger)
        query_dict = {
            "query_string": "Initial Access Execution",
            "condition_dict": {},
            "doc_multi_hit": False,
            "max_shard_ctx": 1,
            "n_results": 1,
        }
        meta, res = frag.query(query_dict, prompts=True)
        self.assertEqual(
            1,
            len(res),
        )
        self.assertEqual(
            1,
            len(meta),
        )