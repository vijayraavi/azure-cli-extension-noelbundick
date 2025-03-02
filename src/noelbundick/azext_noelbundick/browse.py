import json
import operator
import os
import platform
import re
import requests
import shutil
import subprocess
import tarfile

from azure.cli.core.api import get_config_dir
from azure.cli.core.commands import CliCommandType
from io import BytesIO
from knack.log import get_logger
from zipfile import ZipFile

logger = get_logger(__name__)


def load_command_table(self, _):
    custom = CliCommandType(operations_tmpl='{}#{{}}'.format(__name__))

    with self.command_group('', custom_command_type=custom) as g:
        g.custom_command('browse', 'launch_azbrowse')


def load_arguments(self, _):
    pass


def get_latest_azbrowse(current_platform):
    target_platform = '{}_amd64'.format(current_platform.lower())

    r = requests.get('https://api.github.com/repos/lawrencegripper/azbrowse/releases')
    releases = r.json()

    releases = sorted(releases, key=lambda x: x['published_at'], reverse=True)
    latest = (x['browser_download_url'] for x in releases[0]['assets'])
    download = next(x for x in latest if target_platform in x)
    return download


def launch_azbrowse():
    config_dir = get_config_dir()
    executable = 'azbrowse'
    
    current_platform = platform.system()
    if current_platform == 'Windows':
        executable += '.exe'
    
    azbrowse = os.path.join(config_dir, executable)

    # azbrowse is self-updating
    if not os.path.isfile(azbrowse):
        latest_azbrowse = get_latest_azbrowse(current_platform)
        logger.warn('Downloading latest azbrowse from {}'.format(latest_azbrowse))
        r = requests.get(latest_azbrowse, allow_redirects=True, stream=True)

        if latest_azbrowse.endswith('.zip'):
            with ZipFile(BytesIO(r.content)) as zipfile:
                zipfile.extract(executable, path=config_dir)
        elif latest_azbrowse.endswith('.tar.gz'):
            with tarfile.open(fileobj=BytesIO(r.content), mode='r:gz') as tar:
                tar.extract(executable, path=config_dir)
        os.chmod(azbrowse, 0o755)

    logger.warn('Launching azbrowse, hit `Ctrl+C` to close')
    os.system(azbrowse)