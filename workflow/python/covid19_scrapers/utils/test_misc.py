from covid19_scrapers import utils as utils


def test_as_list():
    assert utils.misc.as_list('') == ['']
    assert utils.misc.as_list(['']) == ['']
