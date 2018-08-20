import os
import shutil

import yaml

from paradrop.base import settings
from paradrop.core.chute.builder import build_chute
from paradrop.core.container.downloader import downloader


def download_chute_files(update):
    """
    Download any files or git repositories required by the chute.
    """
    download_args = getattr(update, "download", None)
    if download_args is not None:
        loader = downloader(**download_args)
        workdir, meta = loader.fetch()
        update.workdir = workdir


def load_chute_configuration(update):
    """
    Load and interpret paradrop.yaml file.
    """
    if not update.has_chute_build():
        return

    config = {}

    workdir = getattr(update, "workdir", None)
    if workdir is not None:
        conf_path = os.path.join(workdir, settings.CHUTE_CONFIG_FILE)
        with open(conf_path, "r") as source:
            config = yaml.safe_load(source)

    # Look for additional build information from the update object
    # and merge with the configuration file.
    if hasattr(update, "build"):
        config.update(update.build)

    # Try to set the owner of the chute.
    if hasattr(update, "user"):
        config['owner'] = update.user

    update.new = build_chute(config)


def delete_chute_files(update):
    """
    Delete files that were used to build the chute.
    """
    workdir = getattr(update, "workdir", None)
    if workdir is not None:
        shutil.rmtree(workdir)
