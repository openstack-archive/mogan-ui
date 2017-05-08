# Copyright 2016 Cisco Systems
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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.template.defaultfilters import slugify
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views
from mogan_ui.api import mogan
from mogan_ui.content.key_pairs import forms as key_pairs_forms
from mogan_ui.content.key_pairs import tables as key_pairs_tables


class IndexView(tables.DataTableView):
    table_class = key_pairs_tables.KeyPairsTable
    page_title = _("Server Key Pairs")

    def get_data(self):
        try:
            keypairs = mogan.keypair_list(self.request)
        except Exception:
            keypairs = []
            exceptions.handle(self.request,
                              _('Unable to retrieve key pair list.'))
        return keypairs


class CreateView(forms.ModalFormView):
    form_class = key_pairs_forms.CreateKeypair
    template_name = 'project/server_key_pairs/create.html'
    submit_url = reverse_lazy(
        "horizon:project:server_key_pairs:create")
    success_url = 'horizon:project:server_key_pairs:download'
    submit_label = page_title = _("Create Server Key Pair")
    cancel_url = reverse_lazy("horizon:project:server_key_pairs:index")

    def get_success_url(self):
        return reverse(self.success_url,
                       kwargs={"keypair_name": self.request.POST['name']})


class ImportView(forms.ModalFormView):
    form_class = key_pairs_forms.ImportKeypair
    template_name = 'project/server_key_pairs/import.html'
    submit_url = reverse_lazy(
        "horizon:project:server_key_pairs:import")
    success_url = reverse_lazy('horizon:project:server_key_pairs:index')
    submit_label = page_title = _("Import Server Key Pair")

    def get_object_id(self, keypair):
        return keypair.name


class DetailView(views.HorizonTemplateView):
    template_name = 'project/server_key_pairs/detail.html'
    page_title = _("Server Key Pair Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            keypair = mogan.keypair_get(self.request,
                                        self.kwargs['keypair_name'])
        except Exception:
            redirect = reverse('horizon:project:server_key_pairs:index')
            msg = _('Unable to retrieve details for keypair "%s".')\
                % (self.kwargs['keypair_name'])
            exceptions.handle(self.request, msg,
                              redirect=redirect)
        return keypair

    def get_context_data(self, **kwargs):
        """Gets the context data for keypair."""
        context = super(DetailView, self).get_context_data(**kwargs)
        context['keypair'] = self._get_data()
        return context


class DownloadView(views.HorizonTemplateView):
    template_name = 'project/server_key_pairs/download.html'
    page_title = _("Download Server Key Pair")

    def get_context_data(self, keypair_name=None):
        return {'keypair_name': keypair_name}


class GenerateView(views.HorizonTemplateView):
    # TODO(Itxaka): Remove cache_control in django >= 1.9
    # https://code.djangoproject.com/ticket/13008
    @method_decorator(cache_control(max_age=0, no_cache=True,
                                    no_store=True, must_revalidate=True))
    @method_decorator(never_cache)
    def get(self, request, keypair_name=None, optional=None):
        try:
            if optional == "regenerate":
                mogan.keypair_delete(request, keypair_name)

            keypair = mogan.keypair_create(request, keypair_name)
        except Exception:
            redirect = reverse('horizon:project:server_key_pairs:index')
            exceptions.handle(self.request,
                              _('Unable to create key pair: %(exc)s'),
                              redirect=redirect)

        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = ('attachment; filename=%s.pem'
                                           % slugify(keypair.name))
        response.write(keypair.private_key)
        response['Content-Length'] = str(len(response.content))
        return response
