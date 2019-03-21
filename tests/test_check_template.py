#
# parselglossy -- Generic input parsing library, speaking in tongues
# Copyright (C) 2019 Roberto Di Remigio, Radovan Bast, and contributors.
#
# This file is part of parselglossy.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# For information on the complete list of contributors to the
# parselglossy library, see: <http://parselglossy.readthedocs.io/>
#

# -*- coding: utf-8 -*-
"""Tests for `parselglossy` package.

Tests that the template is not malformed.
"""

import pytest

from parselglossy.exceptions import ParselglossyError
from parselglossy.validation import check_template

# Well formed keyword and section
keyword = {"name": "title", "type": "str", "docstring": "Title of the calculation."}
section = {"name": "scf", "docstring": "SCF input parameters.", "keywords": [keyword]}

# Malformed keywords
keyword_with_section = dict(keyword)
keyword_with_section["sections"] = [section]

keyword_with_invalid_type = dict(keyword)
keyword_with_invalid_type["type"] = "fooffa"

keyword_without_type = dict(keyword)
keyword_without_type.pop("type")

keyword_without_docstring = dict(keyword)
keyword_without_docstring.pop("docstring")

keyword_with_nothing = dict(keyword_without_type)
keyword_with_nothing.pop("docstring")

# Malformed sections
section_without_docstring = dict(section)
section_without_docstring.pop("docstring")

nested_sections_without_docstring = {
    "sections": [
        {
            "name": "foo",
            "keywords": [
                {
                    "name": "title",
                    "type": "str",
                    "docstring": "Title of the calculation.",
                }
            ],
            "sections": [{"name": "bar"}],
        }
    ]
}

nested_sections_with_malformed_keyword = {
    "sections": [
        {
            "name": "foo",
            "keywords": [keyword_with_section, keyword_with_nothing],
            "sections": [{"name": "bar"}],
        }
    ]
}

error_preamble = r"Error(?:\(s\))? occurred when checking the template:\n"
check_template_data = [
    (
        {"keywords": [keyword_with_section]},
        r"- At user\['title'\]:\s+Sections cannot be nested under keywords.",
    ),
    (
        {"keywords": [keyword_with_invalid_type]},
        r"- At user\['title'\]:\s+Keywords must have a valid type.",
    ),
    (
        {"keywords": [keyword_without_type]},
        r"- At user\['title'\]:\s+Keywords must have a valid type.",
    ),
    (
        {"keywords": [keyword_without_docstring]},
        r"- At user\['title'\]:\s+Keywords must have a non-empty docstring.",
    ),
    (
        {"keywords": [keyword_with_nothing]},
        r"- At user\['title'\]:\s+Keywords must have a valid type.\n"
        r"- At user\['title'\]:\s+Keywords must have a non-empty docstring.",
    ),
    (
        {"sections": [section_without_docstring]},
        r"- At user\['scf'\]:\s+Sections must have a non-empty docstring.",
    ),
    (
        nested_sections_without_docstring,
        r"- At user\['foo'\]:\s+Sections must have a non-empty docstring.\n"
        r"- At user\['foo'\]\['bar'\]:\s+Sections must have a non-empty docstring.",
    ),
    (
        nested_sections_with_malformed_keyword,
        r"- At user\['foo'\]:\s+Sections must have a non-empty docstring.\n"
        r"- At user\['foo'\]\['title'\]:\s+Sections cannot be nested under keywords.\n"
        r"- At user\['foo'\]\['title'\]:\s+Keywords must have a valid type.\n"
        r"- At user\['foo'\]\['title'\]:\s+Keywords must have a non-empty docstring.\n"
        r"- At user\['foo'\]\['bar'\]:\s+Sections must have a non-empty docstring.",
    ),
]


@pytest.mark.parametrize(
    "template,error_message",
    [pytest.param(*args) for args in check_template_data],
    ids=[
        "section_under_keyword",
        "keyword_no_type",
        "keyword_invalid_type",
        "keyword_no_docstring",
        "keyword_nothing",
        "section_no_docstring",
        "nested_no_docstring",
        "nested_bad_keyword",
    ],
)
def test_check_template(template, error_message):
    with pytest.raises(ParselglossyError, match=(error_preamble + error_message)):
        outgoing = check_template(template)  # type: Optional[JSONDict]