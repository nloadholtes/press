import logging
import uuid
import ipaddress
from collections import OrderedDict

from press import helpers
from press.helpers.package import get_press_version

# TODO: Form base class for sysconfig/network-scripts under redhat

log = logging.getLogger(__name__)

# Type: func
lookup_methods = {'mac': helpers.networking.get_device_by_mac,
                  'dev': helpers.networking.get_device_by_dev}


class InterfaceTemplate(OrderedDict):
    def __init__(self,
                 device,
                 type='Ethernet',
                 bootproto='none',
                 default_route=False,
                 ipv4_failure_fatal=False,
                 ipv6init=True,
                 ipv6_autoconf=False,
                 ipv6_failure_fatal=False,
                 uid='',
                 name='',
                 on_boot=True,
                 ip_address='',
                 prefix='',
                 gateway='',
                 nameservers=(),
                 domain='',
                 peer_dns=False):
        super(InterfaceTemplate, self).__init__()
        self['DEVICE'] = device
        self['NAME'] = name or device
        self['TYPE'] = type
        self['BOOTPROTO'] = bootproto
        self['DEFROUTE'] = self.yes_no(default_route)
        self['IPV4_FAILURE_FATAL'] = self.yes_no(ipv4_failure_fatal)
        self['IPV6INIT'] = self.yes_no(ipv6init)
        self['IPV6_AUTOCONF'] = self.yes_no(ipv6_autoconf)
        self['IPV6_FAILURE_FATAL'] = self.yes_no(ipv6_failure_fatal)
        if not uid:
            uid = str(uuid.uuid4())
        self['UUID'] = uid
        self['ONBOOT'] = self.yes_no(on_boot)
        self['PEERDNS'] = self.yes_no(peer_dns)
        self['IPV6_PEERDNS'] = self.yes_no(peer_dns)

        if ip_address:
            self['IPADDR'] = ip_address
            self['PREFIX'] = prefix

        if gateway:
            self['GATEWAY'] = gateway

        for idx in range(len(nameservers)):
            self['DNS%d' % idx] = nameservers[idx]

        if domain:
            self['DOMAIN'] = domain

    def generate(self):
        script = '# Generated by press v%s\n' % get_press_version()
        for k, v in self.items():
            script += '%s=%s\n' % (k, v)
        return script

    @staticmethod
    def yes_no(b):
        return b and 'yes' or 'no'


class IPv6InterfaceTemplate(InterfaceTemplate):
    def __init__(self, *args, **kwargs):
        # Remove ip_address and gateway from kwargs if they are set
        ip_address = '' if 'ip_address' not in kwargs else kwargs.pop("ip_address")
        gateway = '' if 'gateway' not in kwargs else kwargs.pop("gateway")
        kwargs['ipv6init'] = True

        super(IPv6InterfaceTemplate, self).__init__(*args, **kwargs)
        # Following the logic in parent class of not setting them if not defined
        if ip_address:
            self['IPV6ADDR'] = ip_address
        if gateway:
            self['IPV6_DEFAULTGW'] = gateway


class DummyInterfaceTemplate(InterfaceTemplate):
    def __init__(self, device):
        dummy_dict = dict(type='Ethernet',
                          bootproto='none',
                          default_route=True,
                          ipv4_failure_fatal=False,
                          ipv6init=True,
                          ipv6_autoconf=True,
                          ipv6_failure_fatal=False,
                          on_boot=False,
                          peer_dns=True)
        super(DummyInterfaceTemplate, self).__init__(device, **dummy_dict)


def generate_routes(routes):
    script = '# Generated by press v%s\n' % get_press_version()
    d = OrderedDict()
    for idx in range(len(routes)):
        i = ipaddress.ip_network(routes[idx]['cidr'].decode("utf-8"))
        d['ADDRESS%d' % idx] = str(i.network_address)
        d['NETMASK%d' % idx] = i.netmask
        d['GATEWAY%d' % idx] = routes[idx]['gateway']
    for k, v in d.items():
        script += '%s=%s\n' % (k, v)
    return script