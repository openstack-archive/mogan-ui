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

from django.http import HttpResponse
from django import template
from django.template.defaultfilters import title
from django.utils.translation import npgettext_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from mogan_ui.api import mogan
from mogan_ui import exceptions

from horizon import tables
from horizon.utils import filters


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Server")
    url = "horizon:project:servers:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    ajax = True

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(LaunchLink, self).__init__(attrs, **kwargs)

    def allowed(self, request, datum):
        # TODO(zhenguo): Add quotas check
        return True  # The action should always be displayed

    def single(self, table, request, object_id=None):
        self.allowed(request, None)
        return HttpResponse(self.render(is_table_action=True))


class DeleteServer(tables.DeleteAction):
    help_text = _("Deleted servers are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Server",
            u"Delete Servers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Server",
            u"Scheduled deletion of Servers",
            count
        )

    def allowed(self, request, server=None):
        """Allow delete action

        if server is in error state or not currently being deleted.
        """
        error_state = deleting = False
        if server:
            error_state = (server.status == 'error')
            deleting = (server.status.lower() == "deleting")
        return error_state or not deleting

    def action(self, request, obj_id):
        mogan.server_delete(request, obj_id)


class StartServer(tables.BatchAction):
    name = "start"
    classes = ('btn-confirm',)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Server",
            u"Start Servers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Server",
            u"Started Servers",
            count
        )

    def allowed(self, request, server):
        return ((server is None) or
                (server.status in ("stopped",)))

    def action(self, request, obj_id):
        mogan.server_start(request, obj_id)


class StopServer(tables.BatchAction):
    name = "stop"
    help_text = _("The server(s) will be shut off.")
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return npgettext_lazy(
            "Action to perform (the server is currently running)",
            u"Shut Off Server",
            u"Shut Off Servers",
            count
        )

    @staticmethod
    def action_past(count):
        return npgettext_lazy(
            "Past action (the server is currently already Shut Off)",
            u"Shut Off Server",
            u"Shut Off Servers",
            count
        )

    def allowed(self, request, server):
        return ((server is None)
                or ((server.power_state in ("power on",))
                    and (server.status != "deleting")))

    def action(self, request, obj_id):
        mogan.server_stop(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, server_id):
        try:
            server = mogan.server_get(request, server_id)
            return server
        except exceptions.ResourceNotFound:
            raise exceptions.NOT_FOUND


def get_ips(server):
    template_name = 'project/servers/_server_ips.html'
    ip_groups = {}

    for nic in server.nics:
        net_id = nic['network_id']
        ip_groups[net_id] = {}
        ip_groups[net_id]["floating"] = []
        ip_groups[net_id]["non_floating"] = []
        if nic.get('floating_ip'):
            ip_groups[net_id]["floating"].append(nic.floating_ip)

        for ip in nic['fixed_ips']:
            ip_groups[net_id]["non_floating"].append(ip['ip_address'])

    context = {
        "ip_groups": ip_groups,
    }
    return template.loader.render_to_string(template_name, context)


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

SERVER_FILTER_CHOICES = (
    ('name', _("Server Name"), True),
    ('status', _("Status ="), True),
    ('availability_zone', _("Availability Zone"), True),
)


class ServersFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = SERVER_FILTER_CHOICES


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
        link="horizon:project:servers:detail",
        verbose_name=_("Server Name"))
    image = tables.Column("image_uuid",
                          verbose_name=_("Image"))
    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
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
        table_actions_menu = (StartServer, StopServer)
        table_actions = (LaunchLink, DeleteServer, ServersFilterAction)
        row_actions = (StartServer, StopServer, DeleteServer,)
