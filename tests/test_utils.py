import unittest

from utils import validate_file_extension, validate_integer


class UtilsTests(unittest.TestCase):
    def test_filename_rejects_paths_and_reserved_names(self):
        for filename in ["../escape.png", "folder/file.png", "folder\\file.png", "CON.png", "bad:name.png", ".."]:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                validate_file_extension(filename)

    def test_filename_adds_default_extension(self):
        self.assertEqual(validate_file_extension("示例图片"), "示例图片.png")

    def test_dimension_validation_rejects_invalid_values(self):
        for value in [None, True, "abc", 255, 4097, 300]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_integer("宽度", value, 256, 4096, multiple_of=64)

    def test_dimension_validation_accepts_numeric_string(self):
        self.assertEqual(validate_integer("宽度", "1024", 256, 4096, multiple_of=64), 1024)


if __name__ == "__main__":
    unittest.main()
