#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf import settings

from horizon.utils.memoized import memoized
from moganclient.v1 import client as mogan_client
from openstack_dashboard.api import base


@memoized
def moganclient(request):
    """Returns a client connected to the Mogan backend.

    :param request: HTTP request.
    :return: Mogan client.
    """
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    mogan_url = base.url_for(request, 'baremetal_compute')

    return mogan_client.Client(mogan_url,
                               project_id=request.user.project_id,
                               token=request.user.token.id,
                               insecure=insecure,
                               cacert=cacert)


def server_list(request):
    """Retrieve a list of servers.

    :param request: HTTP request.
    :return: A list of servers.
    """
    server_manager = moganclient(request).server
    servers = server_manager.list(detailed=True, all_projects=False)
    for server in servers:
        full_flavor = flavor_get(request, server.flavor_uuid)
        server.full_flavor = full_flavor
    return servers


def server_create(request, name, image, flavor, nics, availability_zone,
                  user_data, key_name, server_count):
    """Create a server.

    :param request: HTTP request.
    :return: Server object.
    """
    server_manager = moganclient(request).server
    return server_manager.create(
        name=name, image_uuid=image, flavor_uuid=flavor,
        networks=nics, availability_zone=availability_zone,
        userdata=user_data, key_name=key_name, min_count=server_count,
        max_count=server_count,
    )


def server_get(request, server_id):
    """Get a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    :return: Server object.
    """
    server_manager = moganclient(request).server
    server = server_manager.get(server_id)
    full_flavor = flavor_get(request, server.flavor_uuid)
    server.full_flavor = full_flavor
    return server


def server_delete(request, server_id):
    """Delete a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    """
    server_manager = moganclient(request).server
    return server_manager.delete(server_id)


def server_start(request, server_id):
    """Start a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    """
    server_manager = moganclient(request).server
    return server_manager.set_power_state(server_id, 'on')


def server_stop(request, server_id):
    """Stop a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    """
    server_manager = moganclient(request).server
    return server_manager.set_power_state(server_id, 'off')


def server_reboot(request, server_id, soft_reboot=False):
    """Reboot a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    """
    server_manager = moganclient(request).server
    if soft_reboot:
        target = 'soft_reboot'
    else:
        target = 'reboot'
    return server_manager.set_power_state(server_id, target)


def keypair_list(request):
    """Retrieve a list of keypairs.

    :param request: HTTP request.
    :return: A list of keypairs.
    """
    keypair_manager = moganclient(request).keypair
    return keypair_manager.list()


def keypair_create(request, name):
    """Create a keypair.

    :param request: HTTP request.
    :param name: The name of the keypair.
    """
    keypair_manager = moganclient(request).keypair
    return keypair_manager.create(name=name)


def keypair_import(request, name, public_key):
    """Import a keypair.

    :param request: HTTP request.
    :param name: The name of the keypair.
    :param public_key: The public key used to generate keypair.
    """
    keypair_manager = moganclient(request).keypair
    return keypair_manager.create(name=name, public_key=public_key)


def keypair_get(request, name):
    """Get a keypair.

    :param request: HTTP request.
    :param name: The name of the keypair.
    """
    keypair_manager = moganclient(request).keypair
    return keypair_manager.get(name)


def keypair_delete(request, name):
    """Delete a keypair.

    :param request: HTTP request.
    :param name: The name of the keypair.
    """
    keypair_manager = moganclient(request).keypair
    return keypair_manager.delete(name)


def availability_zone_list(request):
    """Retrieve a list of availability zones.

    :param request: HTTP request.
    :return: A list of availability zones.
    """
    az_manager = moganclient(request).availability_zone
    return az_manager.list()


def flavor_list(request):
    """Retrieve a list of flavors.

    :param request: HTTP request.
    :return: A list of flavors.
    """
    flavor_manager = moganclient(request).flavor
    return flavor_manager.list()


def flavor_get(request, flavor_id):
    """Get a flavor.

    :param request: HTTP request.
    :param server_id: The uuid of the flavor.
    :return: Flavor object.
    """
    flavor_manager = moganclient(request).flavor
    return flavor_manager.get(flavor_id)
