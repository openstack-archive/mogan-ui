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
    return server_manager.list(detailed=True, all_projects=False)


def server_get(request, server_id):
    """Get a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    :return: Server object.
    """
    server_manager = moganclient(request).server
    return server_manager.get(server_id)


def server_delete(request, server_id):
    """Delete a server.

    :param request: HTTP request.
    :param server_id: The uuid of the server.
    """
    server_manager = moganclient(request).server
    return server_manager.delete(server_id)


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
