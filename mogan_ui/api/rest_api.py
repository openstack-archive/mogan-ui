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

from django.views import generic

from mogan_ui.api import client

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Servers(generic.View):
    """API for Mogan Servers"""
    url_regex = r'mogan/servers/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of the servers.

        :param request: HTTP request.
        :return: servers.
        """
        servers = client.server_list(request)
        return {'servers': [s.to_dict() for s in servers]}
