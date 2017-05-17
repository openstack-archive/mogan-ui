# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.
#
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from mogan_ui.api import mogan


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "server_overview"
    template_name = ("project/servers/"
                     "_detail_overview.html")

    def get_context_data(self, request):
        return {"server": self.tab_group.kwargs['server'],
                "is_superuser": request.user.is_superuser}


class ConsoleTab(tabs.Tab):
    name = _("Console")
    slug = "console"
    template_name = "project/servers/_detail_console.html"
    preload = False

    def get_context_data(self, request):
        server = self.tab_group.kwargs['server']
        console_url = None
        try:
            console = mogan.console_get(request, server.uuid)
            console_url = console.console['url']
        except Exception:
            exceptions.handle(request, ignore=True, force_log=True)

        return {'console_url': console_url, 'server_id': server.uuid}


class ServerDetailTabs(tabs.DetailTabsGroup):
    slug = "server_details"
    tabs = (OverviewTab, ConsoleTab)
    sticky = True
