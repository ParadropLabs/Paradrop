from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.core.config import dhcp
from paradrop.core.update.update_object import UpdateObject


def test_getVirtDHCPSettings():
    networkInterfaces = [{
        'name': 'wlan0',
        'externalIntf': 'vwlan0',
        'externalIpaddr': '192.168.0.1',
        'internalIpaddr': '192.168.0.2',
        'dhcp': {
            'lease': '12h',
            'start': 20,
            'limit': 200
        }
    }, {
        'name': 'wlan1',
        'externalIntf': 'vwlan1',
        'externalIpaddr': '192.168.1.1',
        'internalIpaddr': '192.168.1.2',
        'dhcp': {
            'lease': '12h',
            'start': 20,
            'limit': 200,
            'relay': '1.2.3.4'
        }
    }, {
        'name': 'wlan2',
        'externalIntf': 'vwlan2',
        'externalIpaddr': '192.168.2.1',
        'internalIpaddr': '192.168.2.2',
        'dhcp': {
            'lease': '12h',
            'start': 20,
            'limit': 200,
            'relay': ['192.168.2.1,1.2.3.4,eth0']
        }
    }]

    update = UpdateObject({'name': 'test'})
    update.new.setCache('externalSystemDir', '/tmp')
    update.new.setCache('networkInterfaces', networkInterfaces)

    dhcp.getVirtDHCPSettings(update)

    virtDHCPSettings = update.new.getCache('virtDHCPSettings')

    # Convert the results to a dictionary for easy validation.
    results = dict()
    for header, contents in virtDHCPSettings:
        key = header['type']
        if 'name' in header:
            key += '-' + header['name']
        results[key] = contents

    # Verify that the DHCP relay options are properly formed.
    assert results['dhcp-vwlan0'].get('relay', None) is None
    assert results['dhcp-vwlan1']['relay'] == ['192.168.1.1,1.2.3.4']
    assert results['dhcp-vwlan2']['relay'] == networkInterfaces[2]['dhcp']['relay']
