import importlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch


class FakePipeline:
    def __init__(self):
        self.attention_slicing = False
        self.sequential_offload = False
        self.components = {}

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

    def enable_attention_slicing(self, _size):
        self.attention_slicing = True

    def enable_sequential_cpu_offload(self):
        self.sequential_offload = True

    def to(self, _device):
        return self


class ModelManagerTests(unittest.TestCase):
    def test_basic_mode_does_not_enable_slow_attention_slicing(self):
        fake_torch = types.SimpleNamespace(
            bfloat16="bfloat16",
            cuda=types.SimpleNamespace(is_available=lambda: False),
            set_float32_matmul_precision=lambda _value: None,
        )
        fake_diffusers = types.SimpleNamespace(ZImagePipeline=FakePipeline)
        with patch.dict(sys.modules, {"torch": fake_torch, "diffusers": fake_diffusers}):
            sys.modules.pop("model_manager", None)
            module = importlib.import_module("model_manager")
            manager = module.ModelManager()
            with tempfile.TemporaryDirectory() as model_dir, redirect_stdout(io.StringIO()):
                success, message = manager.load_model("basic", Path(model_dir))
                self.assertTrue(success, message)
                self.assertFalse(manager.get_pipe().attention_slicing)
                manager.unload_model()
        sys.modules.pop("model_manager", None)

    def test_low_vram_alias_and_unload_lock(self):
        fake_torch = types.SimpleNamespace(
            bfloat16="bfloat16",
            cuda=types.SimpleNamespace(is_available=lambda: False),
        )
        fake_diffusers = types.SimpleNamespace(ZImagePipeline=FakePipeline)

        with patch.dict(sys.modules, {"torch": fake_torch, "diffusers": fake_diffusers}):
            sys.modules.pop("model_manager", None)
            module = importlib.import_module("model_manager")
            manager = module.ModelManager()

            with tempfile.TemporaryDirectory() as model_dir:
                with redirect_stdout(io.StringIO()):
                    success, message = manager.load_model("lowvram", Path(model_dir))
                    self.assertTrue(success, message)
                    self.assertEqual(manager.get_optimization_mode(), "low_vram")
                    self.assertTrue(manager.get_pipe().sequential_offload)

                    pipe = manager.acquire_pipe_for_inference()
                    self.assertIsNotNone(pipe)
                    success, _ = manager.unload_model()
                    self.assertFalse(success)
                    manager.release_pipe_after_inference()

                    success, _ = manager.unload_model()
                    self.assertTrue(success)
                    self.assertFalse(manager.is_model_loaded())

        sys.modules.pop("model_manager", None)


if __name__ == "__main__":
    unittest.main()
