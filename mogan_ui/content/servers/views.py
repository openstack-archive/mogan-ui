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

from django.utils.translation import ugettext_lazy as _

from mogan_ui.api import mogan
from mogan_ui.content.servers.tables import ServersTable

from horizon import exceptions
from horizon import tables


class IndexView(tables.DataTableView):
    table_class = ServersTable
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
