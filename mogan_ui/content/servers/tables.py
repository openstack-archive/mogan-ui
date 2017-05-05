# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.
#
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

from django.template.defaultfilters import title
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from mogan_ui.api import mogan

from horizon import tables
from horizon.utils import filters


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, server_id):
        server = mogan.server_get(request, server_id)
        return server


STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Server", u"Active")),
    ("stopped", pgettext_lazy("Current status of a Server", u"Stopped")),
    ("error", pgettext_lazy("Current status of a Server", u"Error")),
    ("rebuilding", pgettext_lazy("Current status of a Server",
                                 u"Rebuilding")),
    ("building", pgettext_lazy("Current status of a Server", u"Building")),
    ("powering-on", pgettext_lazy("Current status of a Server",
                                  u"Powering On")),
    ("powering-off", pgettext_lazy("Current status of a Server",
                                   u"Powering Off")),
    ("rebooting", pgettext_lazy("Current status of a Server",
                                u"Rebooting")),
    ("deleting", pgettext_lazy("Current status of a Server",
                               u"Deleting")),
    ("soft-powering-off", pgettext_lazy("Current status of a Server",
                                        u"Soft Powering Off")),
    ("soft-rebooting", pgettext_lazy("Current status of a Server",
                                     u"Soft Rebooting")),
    ("maintenance", pgettext_lazy("Current status of a Server",
                                  u"Maintenance")),
)


class ServersTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("stopped", True),
        ("building", None),
        ("error", False),
        ("maintenance", False),
    )
    name = tables.WrappingColumn(
        "name",
        verbose_name=_("Server Name"))
    image = tables.Column("image_uuid",
                          verbose_name=_("Image"))
    flavor = tables.Column("flavor_uuid",
                           sortable=False,
                           verbose_name=_("Flavor"))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    az = tables.Column("availability_zone",
                       verbose_name=_("Availability Zone"))
    state = tables.Column("power_state",
                          verbose_name=_("Power State"))
    created = tables.Column("created_at",
                            verbose_name=_("Time since created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    def get_object_id(self, obj):
        return obj.uuid

    class Meta(object):
        name = "servers"
        verbose_name = _("Servers")
        status_columns = ["status"]
        row_class = UpdateRow
