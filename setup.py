from setuptools import setup, find_packages

from pylatexenc.version import version_str

setup(
    name = "pylatexenc",
    version = version_str,

    # metadata for upload to PyPI
    author = "Philippe Faist",
    author_email = "philippe.faist@bluewin.ch",
    description = "Python library for encoding unicode to latex and for parsing LaTeX to generate unicode text",
    license = "MIT",
    keywords = "latex text unicode encode parse expression",
    url = "https://github.com/phfaist/pylatexenc",
    classifiers=[
        'Development Status :: 5 - Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Markup :: LaTeX',
    ],

    # could also include long_description, download_url, classifiers, etc.

    packages = find_packages(),
    scripts = [],

    install_requires = [],

    package_data = {
    },

    
)
