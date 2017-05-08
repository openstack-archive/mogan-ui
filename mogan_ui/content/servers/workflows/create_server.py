# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import json
import logging
import operator

from oslo_utils import units
import six

from django.template.defaultfilters import filesizeformat
from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon.utils import functions
from horizon.utils import memoized
from horizon.utils import validators
from horizon import workflows

from mogan_ui.api import mogan
from openstack_dashboard import api
from openstack_dashboard.api import base

from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


LOG = logging.getLogger(__name__)


class SelectProjectUserAction(workflows.Action):
    project_id = forms.ThemableChoiceField(label=_("Project"))
    user_id = forms.ThemableChoiceField(label=_("User"))

    def __init__(self, request, *args, **kwargs):
        super(SelectProjectUserAction, self).__init__(request, *args, **kwargs)
        # Set our project choices
        projects = [(tenant.id, tenant.name)
                    for tenant in request.user.authorized_tenants]
        self.fields['project_id'].choices = projects

        # Set our user options
        users = [(request.user.id, request.user.username)]
        self.fields['user_id'].choices = users

    class Meta(object):
        name = _("Project & User")
        # Unusable permission so this is always hidden. However, we
        # keep this step in the workflow for validation/verification purposes.
        permissions = ("!",)


class SelectProjectUser(workflows.Step):
    action_class = SelectProjectUserAction
    contributes = ("project_id", "user_id")


class SetServerDetailsAction(workflows.Action):
    availability_zone = forms.ThemableChoiceField(label=_("Availability Zone"),
                                                  required=False)

    name = forms.CharField(label=_("Server Name"),
                           max_length=255)

    flavor = forms.ThemableChoiceField(label=_("Flavor"),
                                       help_text=_("Size of image to launch."))

    count = forms.IntegerField(label=_("Number of Instances"),
                               min_value=1,
                               initial=1)

    image_id = forms.ChoiceField(label=_("Image Name"))

    class Meta(object):
        name = _("Details")

    def __init__(self, request, context, *args, **kwargs):
        self._init_images_cache()
        self.request = request
        self.context = context
        super(SetServerDetailsAction, self).__init__(
            request, context, *args, **kwargs)

    def _check_image(self, cleaned_data):
        if not cleaned_data.get('image_id'):
            msg = _("You must select an image.")
            self._errors['image_id'] = self.error_class([msg])

    def clean(self):
        cleaned_data = super(SetServerDetailsAction, self).clean()

        self._check_image(cleaned_data)

        return cleaned_data

    def populate_flavor_choices(self, request, context):
        try:
            flavors = mogan.flavor_list(request)
        except Exception:
            flavors = []
            exceptions.handle(request,
                              _('Unable to retrieve flavors.'))

        flavor_list = [(flavor.name, flavor.uuid) for flavor in flavors]
        flavor_list.sort()
        if not flavor_list:
            flavor_list.insert(0, ("", _("No flavors found")))
        elif len(flavor_list) > 1:
            flavor_list.insert(0, ("", _("Select Flavor")))
        return flavor_list

    def populate_availability_zone_choices(self, request, context):
        try:
            zones = mogan.availability_zone_list(request)
        except Exception:
            zones = []
            exceptions.handle(request,
                              _('Unable to retrieve availability zones.'))

        zone_list = [(zone, zone) for zone in zones]
        zone_list.sort()
        if not zone_list:
            zone_list.insert(0, ("", _("No availability zones found")))
        elif len(zone_list) > 1:
            zone_list.insert(0, ("", _("Any Availability Zone")))
        return zone_list

    def _init_images_cache(self):
        if not hasattr(self, '_images_cache'):
            self._images_cache = {}

    def populate_image_id_choices(self, request, context):
        choices = []
        images = image_utils.get_available_images(request,
                                                  context.get('project_id'),
                                                  self._images_cache)
        for image in images:
            if image.properties.get("image_type", '') != "snapshot":
                image.bytes = getattr(
                    image, 'virtual_size', None) or image.size
                image.volume_size = max(
                    image.min_disk, functions.bytes_to_gigabytes(image.bytes))
                choices.append((image.id, image))
        if choices:
            choices.sort(key=lambda c: c[1].name or '')
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        return choices


class SetServerDetails(workflows.Step):
    action_class = SetServerDetailsAction
    depends_on = ("project_id", "user_id")
    contributes = ("availability_zone", "name", "count", "flavor", "image_id")


SERVER_KEYPAIR_IMPORT_URL = "horizon:project:server_key_pairs:keypairs:import"


class SetAccessControlsAction(workflows.Action):
    keypair = forms.ThemableDynamicChoiceField(
        label=_("Key Pair"),
        help_text=_("Key pair to use for "
                    "authentication."),
        add_item_link=SERVER_KEYPAIR_IMPORT_URL)

    class Meta(object):
        name = _("Access & Security")
        help_text = _("Control access to your instance via key pairs, "
                      "security groups, and other mechanisms.")

    def __init__(self, request, *args, **kwargs):
        super(SetAccessControlsAction, self).__init__(request, *args, **kwargs)

    def populate_keypair_choices(self, request, context):
        keypairs = mogan.keypair_list(request)
        if len(keypairs) == 2:
            self.fields['keypair'].initial = keypairs[1][0]
        return keypairs


class SetAccessControls(workflows.Step):
    action_class = SetAccessControlsAction
    depends_on = ("project_id", "user_id")
    contributes = ("keypair_id",)

    def contribute(self, data, context):
        if data:
            post = self.workflow.request.POST
            context['keypair_id'] = data.get("keypair", "")
        return context


class CustomizeAction(workflows.Action):
    class Meta(object):
        name = _("Post-Creation")
        help_text_template = ("project/servers/"
                              "_launch_customize_help.html")

    source_choices = [('', _('Select Script Source')),
                      ('raw', _('Direct Input')),
                      ('file', _('File'))]

    attributes = {'class': 'switchable', 'data-slug': 'scriptsource'}
    script_source = forms.ChoiceField(
        label=_('Customization Script Source'),
        choices=source_choices,
        widget=forms.ThemableSelectWidget(attrs=attributes),
        required=False)

    script_help = _("A script or set of commands to be executed after the "
                    "instance has been built (max 16kb).")

    script_upload = forms.FileField(
        label=_('Script File'),
        help_text=script_help,
        widget=forms.FileInput(attrs={
            'class': 'switched',
            'data-switch-on': 'scriptsource',
            'data-scriptsource-file': _('Script File')}),
        required=False)

    script_data = forms.CharField(
        label=_('Script Data'),
        help_text=script_help,
        widget=forms.widgets.Textarea(attrs={
            'class': 'switched',
            'data-switch-on': 'scriptsource',
            'data-scriptsource-raw': _('Script Data')}),
        required=False)

    def __init__(self, *args):
        super(CustomizeAction, self).__init__(*args)

    def clean(self):
        cleaned = super(CustomizeAction, self).clean()

        files = self.request.FILES
        script = self.clean_uploaded_files('script', files)

        if script is not None:
            cleaned['script_data'] = script

        return cleaned

    def clean_uploaded_files(self, prefix, files):
        upload_str = prefix + "_upload"

        has_upload = upload_str in files
        if has_upload:
            upload_file = files[upload_str]
            log_script_name = upload_file.name
            LOG.info('got upload %s', log_script_name)

            if upload_file._size > 16 * units.Ki:  # 16kb
                msg = _('File exceeds maximum size (16kb)')
                raise forms.ValidationError(msg)
            else:
                script = upload_file.read()
                if script != "":
                    try:
                        normalize_newlines(script)
                    except Exception as e:
                        msg = _('There was a problem parsing the'
                                ' %(prefix)s: %(error)s')
                        msg = msg % {'prefix': prefix,
                                     'error': six.text_type(e)}
                        raise forms.ValidationError(msg)
                return script
        else:
            return None


class PostCreationStep(workflows.Step):
    action_class = CustomizeAction
    contributes = ("script_data",)


class SetNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(
        label=_("Networks"),
        widget=forms.ThemableCheckboxSelectMultiple(),
        error_messages={
            'required': _(
                "At least one network must"
                " be specified.")},
        help_text=_("Launch server with these networks"))

    def __init__(self, request, *args, **kwargs):
        super(SetNetworkAction, self).__init__(request, *args, **kwargs)
        network_list = self.fields["network"].choices
        if len(network_list) == 1:
            self.fields['network'].initial = [network_list[0][0]]

    class Meta(object):
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your server.")

    def populate_network_choices(self, request, context):
        return instance_utils.network_field_data(request)


class SetNetwork(workflows.Step):
    action_class = SetNetworkAction
    template_name = "project/servers/_update_networks.html"
    contributes = ("network_id",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            if networks:
                context['network_id'] = networks
        return context


class LaunchServer(workflows.Workflow):
    slug = "launch_server"
    name = _("Launch Server")
    finalize_button_name = _("Launch")
    success_message = _('Request for launching %(count)s named "%(name)s" '
                        'has been submitted.')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:servers:index"
    multipart = True
    default_steps = (SelectProjectUser,
                     SetServerDetails,
                     SetAccessControls,
                     SetNetwork,
                     PostCreationStep)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown server')
        count = self.context.get('count', 1)
        if int(count) > 1:
            return message % {"count": _("%s servers") % count,
                              "name": name}
        else:
            return message % {"count": _("server"), "name": name}

    @sensitive_variables('context')
    def handle(self, request, context):
        custom_script = context.get('script_data', '')
        image_id = context.get('image_id', None)
        netids = context.get('network_id', None)
        if netids:
            nics = [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            nics = None

        avail_zone = context.get('availability_zone', None)

        try:
            mogan.server_create(request,
                                name=context['name'],
                                image=image_id,
                                flavor=context['flavor'],
                                key_name=context['keypair_id'],
                                user_data=normalize_newlines(custom_script),
                                nics=nics,
                                availability_zone=avail_zone,
                                server_count=int(context['count']))
            return True
        except Exception:
            exceptions.handle(request)
        return False
