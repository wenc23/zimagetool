import tempfile
import unittest
import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import image_processing
from PIL import Image


class FakeImage:
    def save(self, path):
        Path(path).write_bytes(b"image")


class ImageProcessingTests(unittest.TestCase):
    def test_thumbnail_is_bounded_webp(self):
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "large.png"
            source = Image.new("RGB", (1600, 900), "red")
            source.save(image_path)
            thumbnail_path = image_processing.create_gallery_thumbnail(source, image_path)

            self.assertEqual(thumbnail_path.suffix, ".webp")
            self.assertTrue(thumbnail_path.exists())
            with Image.open(thumbnail_path) as thumbnail:
                self.assertLessEqual(thumbnail.width, 640)
                self.assertLessEqual(thumbnail.height, 640)

    def test_cancelled_save_removes_partial_folder(self):
        calls = 0

        def cancel_after_save():
            nonlocal calls
            calls += 1
            if calls >= 2:
                raise RuntimeError("cancelled")

        with tempfile.TemporaryDirectory() as gallery:
            with patch.object(image_processing.config_manager, "get", return_value=gallery):
                with redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        image_processing.save_to_gallery(
                            FakeImage(), "test.png", "prompt", 1024, 1024, 9, 1.0, "basic",
                            cancellation_check=cancel_after_save,
                        )
            self.assertEqual(list(Path(gallery).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
