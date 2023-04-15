import unittest

### BEGIN_TEST_PYLATEXENC_SKIP

import toml
from pathlib import Path

import pylatexenc


# thanks https://github.com/python-poetry/poetry/issues/144#issuecomment-877835259

class TestHardcodedPackageVersion(unittest.TestCase):

    def test_versions_are_in_sync(self):
        """Checks if the pyproject.toml and package.__init__.py __version__ are in sync."""

        path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with open(str(path)) as fpp:
            pyproject = toml.loads(fpp.read())
        pyproject_version = pyproject["tool"]["poetry"]["version"]

        package_init_version = pylatexenc.__version__

        self.assertEqual(package_init_version, pyproject_version)


if __name__ == '__main__':
    unittest.main()

### END_TEST_PYLATEXENC_SKIP
