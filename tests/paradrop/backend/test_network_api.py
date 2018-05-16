import json
import os
import tarfile

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.backend import network_api


@patch('__builtin__.open')
def test_read_leases(open):
    file_object = MagicMock()
    file_object.__enter__.return_value = [
        "1480650200 00:11:22:33:44:55 192.168.128.130 android-ffeeddccbbaa9988 *",
        "1480640500 00:22:44:66:88:aa 192.168.128.170 someones-iPod 01:00:22:44:66:88:aa"
    ]
    open.return_value = file_object

    leases = network_api.read_leases("/")
    assert len(leases) == 2
    assert leases[0]['ip_addr'] == "192.168.128.130"


def test_update_lease():
    leases = {
        '00:11:22:33:44:55': {
            'as_of': 100,
            'mac_addr': '00:11:22:33:44:55'
        },
        '00:22:44:66:88:aa': {
            'as_of': 100,
            'mac_addr': '00:22:44:66:88:aa'
        }
    }

    # An old entry should not replace a newer one.
    old_entry = {
        'as_of': 50,
        'mac_addr': '00:11:22:33:44:55'
    }
    result = network_api.update_lease(leases, old_entry)
    assert result['as_of'] == 100
    assert leases['00:11:22:33:44:55']['as_of'] == 100

    # A newer entry should take the place of an older one.
    old_entry = {
        'as_of': 200,
        'mac_addr': '00:11:22:33:44:55'
    }
    result = network_api.update_lease(leases, old_entry)
    assert result['as_of'] == 200
    assert leases['00:11:22:33:44:55']['as_of'] == 200

    # A previously-unseen address should be added.
    old_entry = {
        'as_of': 0,
        'mac_addr': '00:33:66:99:cc:ff'
    }
    result = network_api.update_lease(leases, old_entry)
    assert result['as_of'] == 0
    assert len(leases) == 3


def test_NetworkApi_get_devices():
    api = network_api.NetworkApi()

    request = MagicMock()

    data = api.get_devices(request)
    assert data is not None
