def test_PDAPIError():
    """
    Test the PDAPIError class
    """
    from paradrop.lib.api.pdapi import PDAPIError

    error = PDAPIError("etype", "msg")
    assert str(error) == "PDAPIError etype: msg"


def test_isPDError():
    """
    Test paradrop.lib.api.pdapi.isPDError
    """
    from paradrop.lib.api import pdapi

    assert pdapi.isPDError(pdapi.OK)
    assert pdapi.isPDError(pdapi.ERR_BADPARAM)

    assert pdapi.isPDError(0) is False
    assert pdapi.isPDError("bad") is False
    assert pdapi.isPDError(None) is False


def test_getErrorToken():
    """
    Test paradrop.lib.api.pdapi.getErrorToken
    """
    from paradrop.lib.api.pdapi import getErrorToken

    # Should be a random token every time.
    token1 = getErrorToken()
    token2 = getErrorToken()
    assert token1 != token2
