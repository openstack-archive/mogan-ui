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
from openstack_dashboard.api import base
from moganclient.v1 import client as mogan_client


@memoized
def moganclient(request):
    """Returns a client connected to the Mogan backend.

    :param request: HTTP request.
    :return: Mogan client.
    """
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', DEFAULT_INSECURE)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', DEFAULT_CACERT)
    mogan_url = base.url_for(request, 'baremetal_compute')

    return client.Client(mogan_url,
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
