from mock import MagicMock, patch
from nose.tools import assert_raises


@patch("paradrop.lib.utils.pdosq.makedirs")
@patch("paradrop.lib.utils.pdos.remove")
def test_createVolumeDirs(remove, makedirs):
    from paradrop.core.config.dockerconfig import createVolumeDirs

    # A delete update should call remove but not makedirs.
    update = MagicMock()
    update.updateType = "delete"
    createVolumeDirs(update)
    remove.assert_called()
    makedirs.assert_not_called()

    remove.reset_mock()

    # A "update" update should call makedirs, not remove.
    update = MagicMock()
    update.updateType = "update"
    createVolumeDirs(update)
    remove.assert_not_called()
    makedirs.assert_called()


@patch("paradrop.lib.utils.pdos.remove")
def test_abortCreateVolumeDirs(remove):
    from paradrop.core.config.dockerconfig import abortCreateVolumeDirs

    # Rolling back an update where the old chute exists should not call remove.
    update = MagicMock()
    update.old = MagicMock()
    abortCreateVolumeDirs(update)
    remove.assert_not_called()

    # Rolling back an update with no old chute should call remove.
    update = MagicMock()
    update.old = None
    abortCreateVolumeDirs(update)
    remove.assert_called()
