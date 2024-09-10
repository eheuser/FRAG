import unittest
import logging

from modules.llm_api import LLMAPI
from utils.utils import read_llm_config


logging.basicConfig(
    level=logging.WARN, format=f"%(asctime)s.%(msecs)03d %(levelname)s:%(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestLLM(unittest.TestCase):
    def test_llm(self):
        config = read_llm_config(logger)
        self.assertEqual(
            isinstance(config, dict),
            True,
        )
    
    def test_llm_temp(self):
        config = read_llm_config(logger)
        llm_api = LLMAPI(config, logger)

        self.assertEqual(
            llm_api.temperature,
            config.get("temperature"),
        )

        llm_api.increase_temperature()
        self.assertNotEqual(
            llm_api.temperature,
            config.get("temperature"),
        )

        llm_api.reset_temperature()
        self.assertEqual(
            llm_api.temperature,
            config.get("temperature"),
        )

    def test_llm_token(self):
        config = read_llm_config(logger)
        llm_api = LLMAPI(config, logger)
        self.assertEqual(
            llm_api.get_token_cnt("Test token text"),
            9,
        )

    def test_llm_query(self):
        config = read_llm_config(logger)
        llm_api = LLMAPI(config, logger)
        result = llm_api.atomic_query(None, [ ["user", "Introduce yourself"] ], None )
        self.assertNotEqual(
            len(result),
            0,
        )