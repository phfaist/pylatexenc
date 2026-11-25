import ast
import os

import pytest

pytest.importorskip('yaml')

from tools import preprocess_lib


@pytest.mark.parametrize('separator', ['/', '\\'])
def test_wildcard_modules_keep_package_paths(tmp_path, monkeypatch, separator):
    source = tmp_path / 'source'
    target = tmp_path / 'output'
    package = source / 'sample' / 'nested'
    package.mkdir(parents=True)
    (package / 'helper.py').write_text('answer = 42\n', encoding='utf-8')
    (package / 'example.py').write_text(
        'from .helper import answer\nresult = answer\n', encoding='utf-8')
    original_glob = preprocess_lib.glob.glob

    def platform_glob(pattern):
        return [path.replace(os.sep, separator).replace('/', separator)
                for path in original_glob(pattern)]

    monkeypatch.setattr(preprocess_lib.glob, 'glob', platform_glob)
    processor = preprocess_lib.Preprocess(
        source_dir=str(source), target_dir=str(target),
        module_list=['sample.nested.*'],
        enabled_features={'keep_relative_imports': False},
    )
    processor.preprocess()

    assert (target / 'sample/nested/helper.py').is_file()
    output = (target / 'sample/nested/example.py').read_text(encoding='utf-8')
    imported = ast.parse(output).body[0]
    assert imported.module == 'sample.nested.helper'
    assert imported.names[0].name == 'answer'
    assert not processor.modules_skipped
