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
"""Documentation generation."""

from typing import List  # noqa: F401

from .utils import JSONDict


def documentation_generator(template: JSONDict, header: str = "") -> str:
    """Generates documentation from a valid template.

    Parameters
    ----------
    template : JSONDict

    Returns
    -------
    docs : str

    Raises
    ------
    :exc:`ParselglossyError`
    """

    docs = rec_documentation_generator(template=template)

    info = (
        ".. This documentation was autogenerated using parselglossy."
        " Editing by hand is not recommended.\n"
    )

    if not header:
        header = "\n================\nInput parameters\n================\n\n"
    header += (
        "Keywords without a default value are **required**.\n"
        "Sections where all keywords have a default value can be omitted.\n"
    )

    return info + header + docs


def document_keyword(keyword: JSONDict) -> str:
    kw_fmt = """
 :{0:s}: {1:s}

  **Type** ``{2:s}``
"""

    doc = kw_fmt.format(keyword["name"], keyword["docstring"], keyword["type"])

    if "default" in keyword.keys():
        doc += """
  **Default** {}""".format(
            keyword["default"]
        )

    return doc


def rec_documentation_generator(template, *, level: int = 0) -> str:
    """Generates documentation from a valid template.

    Parameters
    ----------
    template : JSONDict
    level : int

    Returns
    -------
    docs : str
    """

    docs = []  # type: List[str]

    keywords = template["keywords"] if "keywords" in template.keys() else []
    if keywords:
        doc = "\n**Keywords**"
    for k in keywords:
        doc += document_keyword(k)
        docs.extend(indent(doc, level))

    sections = template["sections"] if "sections" in template.keys() else []
    if sections:
        doc = "\n" if level == 0 else "\n\n"
        doc += "**Sections**"
        fmt = r"""
 :{0:s}: {1:s}
"""
        for s in sections:
            doc += fmt.format(s["name"], s["docstring"])
            doc += rec_documentation_generator(s, level=level + 1)
            docs.extend(indent(doc, level))

    return "".join(docs)


def indent(in_str: str, level: int = 0) -> str:
    return in_str.replace("\n", "\n" + ("  " * level))
