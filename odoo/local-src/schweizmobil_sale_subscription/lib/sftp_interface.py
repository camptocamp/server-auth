# Copyright 2018-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import os
import re
from contextlib import contextmanager
from datetime import date
from io import BytesIO

import paramiko
from odoo.addons.server_environment import serv_config

SERV_CONFIG_SECTION = 'sftp'
_logger = logging.getLogger('SFTP')

# Paramiko sftp client doc on
# http://docs.paramiko.org/en/2.0/api/sftp.html


class _SFTPInterface:
    def __init__(self):

        self._server = os.environ.get("SFTP_SERVER") or serv_config.get(
            SERV_CONFIG_SECTION, 'server'
        )
        self._port = os.environ.get("SFTP_PORT") or int(
            serv_config.get(SERV_CONFIG_SECTION, 'port')
        )
        self._username = os.environ.get("SFTP_USERNAME") or serv_config.get(
            SERV_CONFIG_SECTION, 'username'
        )
        self._password = os.environ.get("SFTP_PASSWORD") or serv_config.get(
            SERV_CONFIG_SECTION, 'password'
        )
        self._ssh_client = None
        self._sftp_client = None

    def _open_sftp_client(self):
        _logger.info('open connection')
        if self._sftp_client:
            return
        if self._server != 'localhost':
            trnsprt = paramiko.Transport((self._server, self._port))
            trnsprt.connect(username=self._username, password=self._password)
            trnsprt.set_keepalive(10)
            self._sftp_client = paramiko.SFTPClient.from_transport(trnsprt)
        else:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            self._ssh_client.connect(hostname=self._server, timeout=3)
            self._ssh_client.get_transport().set_keepalive(10)
            self._sftp_client = self._ssh_client.open_sftp()

    def close(self):
        self._close_sftp_client(True)

    def _close_sftp_client(self, force=False):
        if force and self._sftp_client is not None:
            _logger.info('close connection')
            self._sftp_client.close()
            self._sftp_client = None
            if self._ssh_client:
                self._ssh_client.close()
                self._ssh_client = None

    def save_output_to_sftp(self, output, filename):
        _logger.info('save to %s', filename)
        try:
            self._sftp_client.chdir(os.path.dirname(filename))
        except paramiko.SSHException as exc:
            _logger.error(
                'Error while trying to cd to sftp directory %s: %s',
                filename,
                exc,
            )
            _logger.info('Trying to reconnect')
            self._close_sftp_client(force=True)
            self._open_sftp_client()
            self._sftp_client.chdir(os.path.dirname(filename))
        self._sftp_client.putfo(output, os.path.basename(filename))

    def get_file_list_from_sftp(self, filepath):
        _logger.info('ls %s', filepath)

        filename_list = []

        try:
            filepath_content_list = self._sftp_client.listdir(filepath)
        except paramiko.SSHException as exc:
            _logger.error(
                'Error while trying to list sftp directory %s: %s',
                filepath,
                exc,
            )
            _logger.info('Trying to reconnect')
            self._close_sftp_client(force=True)
            self._open_sftp_client()
            filepath_content_list = self._sftp_client.listdir(filepath)

        for content in filepath_content_list:
            lstat = self._sftp_client.lstat(filepath + content)
            if 'd' not in str(lstat).split()[0]:
                filename_list.append(content)

        return filename_list

    def move_files_on_sftp(self, files, destination_path):
        _logger.info('mv %s %s', files, destination_path)
        for sftp_file in files:
            dest_file_path = destination_path + os.path.basename(sftp_file)
            # Remove existing file at the destination path (an error is raised
            # otherwise)
            try:
                self._sftp_client.lstat(dest_file_path)
            except FileNotFoundError:
                _logger.debug("destination %s is free", dest_file_path)
            else:
                self._sftp_client.unlink(dest_file_path)
            # Move the file
            self._sftp_client.rename(sftp_file, dest_file_path)

    def read_file(self, filename):
        _logger.info('read %s', filename)

        opened_file = self._sftp_client.open(filename, mode='rb')
        file_content = base64.encodestring(opened_file.read())
        opened_file.close()

        return file_content

    def mkdirs(self, dirname):
        paths = []
        while dirname:
            dirname, tail = os.path.split(dirname)
            paths.append(tail)
        if paths:
            # paths[-1] = "/" + paths[-1]
            for path in reversed(paths):
                try:
                    self._sftp_client.chdir(path)
                except IOError:
                    _logger.info("sftp mkdir %s", path)
                    self._sftp_client.mkdir(path)
                    self._sftp_client.chdir(path)


_interface = None


@contextmanager
def SFTPInterface():
    global _interface
    if _interface is None:
        _interface = _SFTPInterface()
    _interface._open_sftp_client()
    try:
        yield _interface
    finally:
        _interface.close()


def sftp_upload(content, document_type, filename):
    # sanitize filename
    filename = re.sub(r"[/\:]", "_", filename)
    root_path = serv_config.get('sftp', 'root_path') or 'DUMMY'
    dirname = os.path.join(
        root_path, date.today().strftime('%Y-%V'), document_type
    )
    if os.environ.get('CI', '') == 'True':
        _logger.info(
            'CI Mode: would have uploaded to sftp %s/%s', dirname, filename
        )
        return
    with SFTPInterface() as sftp:
        sftp.mkdirs(dirname)
        fobj = BytesIO(content)
        sftp.save_output_to_sftp(fobj, os.path.join('/', dirname, filename))
