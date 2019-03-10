import re
from typing import Any, Dict


JsonDict = Dict[str, Any]


class InputError(Exception):
    pass


class TemplateError(Exception):
    pass


def type_matches(value: Any, expected_type: str) -> bool:
    """Checks whether value has the type expected_type.

    If yes, returns True, otherwise False.

    Allowed types T are: 'str', 'int', 'float', 'complex', 'bool',
                         as well as 'List[T]'.

    Raises
    ------
    ValueError
        If expected_type is not among the allowed types.
    """
    allowed_basic_types = ['str', 'int', 'float', 'complex', 'bool']
    allowed_list_types = ['List[{}]'.format(t) for t in allowed_basic_types]
    allowed_types = allowed_basic_types + allowed_list_types

    # first verify whether expected_type is allowed
    if expected_type not in allowed_types:
        raise ValueError('could not recognize expected_type: {}'.format(expected_type))

    expected_type_is_list = re.match(r"^List\[\w+\]$", expected_type) is not None

    if expected_type_is_list:
        # make sure that value is actually a list
        if not type(value).__name__ == 'list':
            return False

        # iterate over each element of the list
        # and check whether it matches T
        list_element_type = re.search(r"^List\[(\w+)\]$", expected_type).group(1)
        for element in value:
            if not type(element).__name__ == list_element_type:
                return False

        return True
    else:
        # expected type is a basic type
        # this is the simpler case
        return type(value).__name__ == expected_type


def validate_node(input_dict: JsonDict, template_dict: JsonDict) -> JsonDict:
    """Validate a node.

    A node is either the root of the input or it is a section.  The node can
    contain keywords or other sections which we traverse recursively.

    Parameters
    ----------
    input_dict: JsonDict
        Contains the input to be checked.
    template_dict: JsonDict
        Contains the input template to be checked against.

    Returns
    -------
    input_dict: JsonDict
        This function modifies input_dict (e.g. fills in defaults).

    Raises
    ------
    InputError
        This signals an error in the input that is to be parsed.
    TemplateError
        This signals an error in the input template.
    """
    input_sections = [x for x in input_dict if type(input_dict[x]).__name__ == 'dict']
    input_keywords = list(filter(lambda x: x not in input_sections, input_dict.keys()))

    if 'sections' in template_dict:
        template_sections = [x['section'] for x in template_dict['sections']]
    else:
        template_sections = []

    if 'keywords' in template_dict:
        template_keywords = [x['keyword'] for x in template_dict['keywords']]
    else:
        template_keywords = []

    # stop if we find a keyword without documentation
    keywords_no_doc = [x['keyword'] for x in template_dict['keywords']
                       if 'documentation' not in x or x['documentation'].strip() == '']
    if len(keywords_no_doc) > 0:
        raise TemplateError('keyword(s) without any documentation: {}'.format(keywords_no_doc))

    # make sure that we did not receive keywords
    # or sections which we did not expect
    difference = set(input_keywords).difference(set(template_keywords))
    if difference != set():
        raise InputError('found unexpected keyword(s): {}'.format(difference))
    difference = set(input_sections).difference(set(template_sections))
    if difference != set():
        raise InputError('found unexpected section(s): {}'.format(difference))

    # check that keywords without a default are set in the input
    keywords_no_default = [x['keyword'] for x in template_dict['keywords'] if 'default' not in x]
    difference = set(keywords_no_default).difference(set(input_keywords))
    if difference != set():
        raise InputError('the following keyword(s) must be set: {}'.format(difference))

    # for each keyword verify the type of the value
    for keyword in input_keywords:
        template_keyword = list(filter(lambda x: x['keyword'] == keyword, template_dict['keywords']))[0]
        _type = template_keyword['type']
        if not type_matches(input_dict[keyword], _type):
            raise InputError("incorrect type for keyword: {0}, expected '{1}' type".format(keyword, _type))

    # fill missing input keywords with template defaults
    for keyword in set(template_keywords).difference(set(input_keywords)):
        template_keyword = list(filter(lambda x: x['keyword'] == keyword, template_dict['keywords']))[0]
        _default = template_keyword['default']
        input_dict[keyword] = _default

    # if this node contains sections, we descend into these and verify these in turn
    for section in template_sections:
        input_section = input_dict[section]
        template_section = list(filter(lambda x: x['section'] == section, template_dict['sections']))[0]
        input_dict[section] = validate_node(input_section, template_section)

    return input_dict


def check_predicates_node(input_dict: JsonDict,
                          input_dict_node: JsonDict,
                          template_dict_node: JsonDict) -> None:
    """Check keyword predicates in a node.

    A node is either the root of the input or it is a section.  The node can
    contain keywords or other sections which we traverse recursively.

    This function does not modify input arguments.

    Parameters
    ----------
    input_dict: JsonDict
        Contains the entire input tree.
    input_dict_node: JsonDict
        Contains the input to be checked: only current node.
    template_dict: JsonDict
        Contains the input template which holds the predicates.

    Returns
    -------
    None

    Raises
    ------
    InputError
        This signals an error in the input that is to be parsed.
    TemplateError
        This signals an error in the input template.
    """
    input_sections = [x for x in input_dict_node if type(input_dict_node[x]).__name__ == 'dict']
    input_keywords = list(filter(lambda x: x not in input_sections, input_dict_node.keys()))

    if 'sections' in template_dict_node:
        template_sections = [x['section'] for x in template_dict_node['sections']]
    else:
        template_sections = []

    # go through the predicates
    for keyword in input_keywords:
        template_keyword = list(filter(lambda x: x['keyword'] == keyword, template_dict_node['keywords']))[0]
        # this value is used by eval() so we skip E841 warning of flake8
        value = input_dict_node[keyword]  # noqa
        if 'predicates' in template_keyword:
            for predicate in template_keyword['predicates']:
                try:
                    r = eval(predicate)
                except SyntaxError:
                    raise TemplateError('syntax error in predicate {} in keyword {}'.format(predicate, keyword))
                if not r:
                    raise InputError('predicate {} failed in keyword {}'.format(predicate, keyword))

    # if this node contains sections, we descend into these and verify these in turn
    for section in template_sections:
        input_section = input_dict_node[section]
        template_section = list(filter(lambda x: x['section'] == section, template_dict_node['sections']))[0]
        check_predicates_node(input_dict, input_section, template_section)
