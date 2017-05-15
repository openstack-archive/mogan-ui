# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from mogan_ui.api import mogan
from mogan_ui.content.project.servers import tables as project_tables
from mogan_ui.content.project.servers import tabs as project_tabs
from mogan_ui.content.project.servers import workflows as project_workflows

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows


class IndexView(tables.DataTableView):
    table_class = project_tables.ServersTable
    template_name = 'project/servers/index.html'
    page_title = _("Servers")

    def get_data(self):
        try:
            servers = mogan.server_list(self.request)
        except Exception:
            servers = []
            msg = _('Unable to retrieve servers.')
            exceptions.handle(self.request, msg)
        return servers


class LaunchServerView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchServer

    def get_initial(self):
        initial = super(LaunchServerView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.ServerDetailTabs
    template_name = 'horizon/common/_detail.html'
    redirect_url = 'horizon:project:servers:index'
    page_title = "{{ server.name|default:server.uuid }}"
    image_url = 'horizon:project:images:images:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        server = self.get_data()
        if server.image_uuid:
            server.image_url = reverse(self.image_url,
                                       args=[server.image_uuid])
        context["server"] = server
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(server)
        return context

    def _get_actions(self, server):
        table = project_tables.ServersTable(self.request)
        return table.render_row_actions(server)

    @memoized.memoized_method
    def get_data(self):
        server_id = self.kwargs['server_id']

        try:
            server = mogan.server_get(self.request, server_id)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'server "%s".') % server_id,
                              redirect=redirect)
            # Not all exception types handled above will result in a redirect.
            # Need to raise here just in case.
            raise exceptions.Http302(redirect)

        return server

    def get_tabs(self, request, *args, **kwargs):
        server = self.get_data()
        return self.tab_group_class(request, server=server, **kwargs)
