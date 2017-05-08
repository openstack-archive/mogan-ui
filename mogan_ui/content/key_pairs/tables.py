# Copyright 2012 Nebula, Inc.
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

from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from mogan_ui.api import mogan


class DeleteKeyPairs(tables.DeleteAction):
    help_text = _("Removing a key pair can leave OpenStack resources orphaned."
                  " You should not remove a key pair unless you are certain it"
                  " is not being used anywhere.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Server Key Pair",
            u"Delete Server Key Pairs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Server Key Pair",
            u"Deleted Server Key Pairs",
            count
        )

    def delete(self, request, obj_id):
        mogan.keypair_delete(request, obj_id)


class ImportKeyPair(tables.LinkAction):
    name = "import"
    verbose_name = _("Import Server Key Pair")
    url = "horizon:project:server_key_pairs:import"
    classes = ("ajax-modal",)
    icon = "upload"


class CreateKeyPair(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Server Key Pair")
    url = "horizon:project:server_key_pairs:create"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, keypair=None):
        # TODO(zhenguo): Add quotas support
        return True


class KeypairsFilterAction(tables.FilterAction):

    def filter(self, table, keypairs, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [keypair for keypair in keypairs
                if query in keypair.name.lower()]


class KeyPairsTable(tables.DataTable):
    detail_link = "horizon:project:server_key_pairs:detail"
    name = tables.Column("name", verbose_name=_("Key Pair Name"),
                         link=detail_link)
    fingerprint = tables.Column("fingerprint", verbose_name=_("Fingerprint"))

    def get_object_id(self, keypair):
        return keypair.name

    class Meta(object):
        name = "keypairs"
        verbose_name = _("Key Pairs")
        table_actions = (CreateKeyPair, ImportKeyPair, DeleteKeyPairs,
                         KeypairsFilterAction,)
        row_actions = (DeleteKeyPairs,)
