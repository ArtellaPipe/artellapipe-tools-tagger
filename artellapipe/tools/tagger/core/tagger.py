#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool used to manage metadata for Artella Assets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import artellapipe

# Defines ID of the tool
TOOL_ID = 'artellapipe-tools-tagger'

# We skip the reloading of this module when launching the tool
no_reload = True


class ArtellaTaggerTool(artellapipe.Tool, object):
    def __init__(self, *args, **kwargs):
        super(ArtellaTaggerTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = artellapipe.Tool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Tagger',
            'id': 'artellapipe-tools-tagger',
            'logo': 'tagger_logo',
            'icon': 'tag',
            'tooltip': 'Tool to manage metadata information for assets',
            'tags': ['assets', 'tag'],
            'sentry_id': 'https://d8790b372a8f4c7a9c98870b8a691918@sentry.io/1764597',
            'import_order': ['widgets', 'core'],
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {
                'label': 'Tagger', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [
                {'label': 'TD',
                 'type': 'menu', 'children': [{'id': 'artellapipe-tools-tagger', 'type': 'tool'}]}],
            'shelf': [
                {'name': 'TD',
                 'children': [{'id': 'artellapipe-tools-tagger', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config


class ArtellaTaggerToolset(artellapipe.Toolset, object):
    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(ArtellaTaggerToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from artellapipe.tools.tagger.widgets import tagger

        tagger_widget = tagger.ArtellaTaggerWidget(
            project=self._project, config=self._config, settings=self._settings, parent=self)
        return [tagger_widget]
