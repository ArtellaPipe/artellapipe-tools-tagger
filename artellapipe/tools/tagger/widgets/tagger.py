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

import logging
import inspect
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import python
from tpDcc.libs.qt.widgets import stack, splitters, breadcrumb

import artellapipe
from artellapipe.tools.tagger.widgets import taggerinfo, taggereditor

LOGGER = logging.getLogger()


class ArtellaTaggerWidget(artellapipe.ToolWidget):
    tagDataCreated = Signal()

    def __init__(self, project, config, settings, parent):
        super(ArtellaTaggerWidget, self).__init__(project=project, config=config, settings=settings, parent=parent)

        self._editors = list()

        self._create_editors()
        self._on_selection_changed()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def post_attacher_set(self):
        self.register_callback(tp.DccCallbacks.NodeSelect, self._on_selection_changed)

    def ui(self):
        super(ArtellaTaggerWidget, self).ui()

        self.resize(300, 300)

        self._error_pixmap = tp.ResourcesMgr().pixmap('error', category='icons').scaled(QSize(24, 24))
        self._warning_pixmap = tp.ResourcesMgr().pixmap('warning', category='icons').scaled(QSize(24, 24))
        self._ok_pixmap = tp.ResourcesMgr().pixmap('ok', category='icons').scaled(QSize(24, 24))

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(5)
        self.main_layout.addLayout(top_layout)
        select_tag_data_btn = QPushButton('Select Tag Data')
        select_tag_data_btn.setMinimumWidth(125)
        select_tag_data_btn.setIcon(tp.ResourcesMgr().icon('tag'))
        remove_tag_data_btn = QPushButton('Remove Tag Data')
        remove_tag_data_btn.setMinimumWidth(125)
        remove_tag_data_btn.setIcon(tp.ResourcesMgr().icon('tag_remove'))
        top_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        # export_tag_data_btn = QPushButton('Export Tag Data')
        # export_tag_data_btn.setEnabled(False)
        # import_tag_data_btn = QPushButton('Import Tag Data')
        # import_tag_data_btn.setEnabled(False)
        top_layout.addWidget(select_tag_data_btn)
        top_layout.addWidget(remove_tag_data_btn)
        # top_layout.addWidget(export_tag_data_btn)
        # top_layout.addWidget(import_tag_data_btn)
        top_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.main_layout.addLayout(splitters.SplitterLayout())

        # ======================================================================================

        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setContentsMargins(2, 2, 2, 2)
        breadcrumb_layout.setSpacing(2)
        self._breadcrumb = breadcrumb.BreadcrumbFrame()
        self._curr_info_image = QLabel()
        self._curr_info_image.setAlignment(Qt.AlignCenter)
        self._curr_info_image.setPixmap(self._error_pixmap)
        breadcrumb_layout.addWidget(self._curr_info_image)
        breadcrumb_layout.addWidget(self._breadcrumb)
        self.main_layout.addLayout(breadcrumb_layout)

        # ======================================================================================

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        # ======================================================================================

        self._tagger_info = taggerinfo.TaggerInfoWidget()
        self._tagger_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.addWidget(self._tagger_info)

        # ======================================================================================

        editors_widget = QWidget()
        editors_layout = QVBoxLayout()
        editors_layout.setContentsMargins(2, 2, 2, 2)
        editors_layout.setSpacing(2)
        editors_widget.setLayout(editors_layout)

        self._tag_types_menu_layout = QHBoxLayout()
        self._tag_types_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._tag_types_menu_layout.setSpacing(0)
        self._tag_types_menu_layout.setAlignment(Qt.AlignTop)
        editors_layout.addLayout(self._tag_types_menu_layout)
        self._tag_types_btn_grp = QButtonGroup(self)
        self._tag_types_btn_grp.setExclusive(True)
        editors_layout.addLayout(self._tag_types_menu_layout)
        self._editors_stack = stack.SlidingStackedWidget()
        editors_layout.addWidget(self._editors_stack)

        self._stack.addWidget(editors_widget)

        # ================================================================================

        self._tagger_info.createTagNode.connect(self._on_create_new_tag_data_node_for_current_selection)
        select_tag_data_btn.clicked.connect(artellapipe.TagsMgr().select_tag_data_node)
        remove_tag_data_btn.clicked.connect(self._on_remove_tag_data_node)

        # ================================================================================

    def create_new_tag_data_node_for_current_selection(self, asset_type=None):
        """
        Creates a new tag data node with the info af all available editors
        :param asset_type: str or None (optional)
        """

        current_selection = artellapipe.TagsMgr().get_current_selection()

        if not current_selection or current_selection == artellapipe.TagsMgr().TagDefinitions.SCENE_SELECTION_NAME \
                or not tp.Dcc.object_exists(current_selection):
            current_selection = tp.Dcc.selected_nodes()
            if current_selection:
                current_selection = current_selection[0]
            else:
                current_selection = artellapipe.TagsMgr().get_current_selection()

        if not artellapipe.TagsMgr().current_selection_has_metadata_node():
            if current_selection != artellapipe.TagsMgr().TagDefinitions.SCENE_SELECTION_NAME:
                new_tag_data_node = tp.Dcc.create_node(
                    node_type='network', node_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_NODE_NAME)
                self._fill_new_tag_data_node(new_tag_data_node, current_selection)

                for editor in self._editors:
                    editor.fill_tag_node(new_tag_data_node)

                # if asset_type is not None and new_tag_data_node:
                #     attr_exists = tp.Dcc.attribute_exists(node=new_tag_data_node, attribute_name='types')
                #     if not attr_exists:
                #         tp.Dcc.add_string_attribute(node=new_tag_data_node, attribute_name='types')
                #     if asset_type == 'Props' or asset_type == 'props':
                #         tp.Dcc.set_string_attribute_value(
                #         node=new_tag_data_node, attribute_name='types', attribute_value='prop')
                #     elif asset_type == 'Background Elements' or asset_type == 'background elements':
                #         tp.Dcc.set_string_attribute_value(
                #         node=new_tag_data_node, attribute_name='types', attribute_value='background_element')
                #     elif asset_type == 'Character' or asset_type == 'character':
                #         tp.Dcc.set_string_attribute_value(
                #         node=new_tag_data_node, attribute_name='types', attribute_value='character')
                #     elif asset_type == 'Light Rig' or asset_type == 'light rig':
                #         tp.Dcc.set_string_attribute_value(
                #         node=new_tag_data_node, attribute_name='types', attribute_value='light_rig')
                #     tp.Dcc.lock_attribute(node=new_tag_data_node, attribute_name='types')

            else:
                new_tag_data_node = tp.Dcc.create_node(
                    node_type='network', node_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_SCENE_NAME)
                tp.Dcc.clear_selection()

        if current_selection == artellapipe.TagsMgr().TagDefinitions.SCENE_SELECTION_NAME:
            tp.Dcc.clear_selection()
        else:
            tp.Dcc.select_object(current_selection)

    def remove_tag_data_node(self):
        """
        Removes the tag data node associated to the current selected Maya object
        """

        tag_data_node = artellapipe.TagsMgr().get_tag_data_node_from_current_selection()
        if tag_data_node is None:
            return
        tp.Dcc.delete_object(tag_data_node)
        self._update_ui()
        self._update_current_info()

        for editor in self._editors:
            editor.update_tag_buttons_state()
            editor.update_data()

    def add_editor(self, editor_widget):
        """
        Adds a new editor to the stack widget
        :param editor_widget: TaggerEditor
        """

        if editor_widget in self._editors:
            LOGGER.warning('Editor with ID {} already exists!'.format(editor_widget.EDITOR_TYPE))
            return

        self._editors.append(editor_widget)
        self._editors_stack.addWidget(editor_widget)

        editor_btn = QPushButton(editor_widget.EDITOR_TYPE.title())
        editor_btn.setCheckable(True)
        self._tag_types_menu_layout.addWidget(editor_btn)
        self._tag_types_btn_grp.addButton(editor_btn)
        editor_index = self._editors.index(editor_widget)
        editor_btn.clicked.connect(partial(self._slide_editors_stack, editor_index))
        if len(self._tag_types_btn_grp.buttons()) <= 1:
            editor_btn.setChecked(True)

        editor_widget.dataUpdated.connect(self._update_current_info)
        editor_widget.initialize()

    def _slide_editors_stack(self, index):
        """
        Internal function that slides editors stack to given index
        :param index: int
        """

        self._editors_stack.slide_in_index(index)

    def _create_editors(self):
        """
        Internal function that creates the editors that should be used by tagger
        Overrides to add custom editors
        """

        if python.is_python2():
            import pkgutil as loader
        else:
            import importlib as loader

        editors_modules = self.config.get('editors_module')
        if not editors_modules:
            LOGGER.warning('No core editors module specified in artellapipe.tools.tagger configuration file!')
            return False

        available_editors = self.config.get('available_editors')
        if not available_editors:
            LOGGER.warning('No available editors defined in artellapipe.tools.tagger configuration file!')
            return False

        LOGGER.info('Loading Available Editors: {}'.format(available_editors))

        modules_to_register = dict()
        all_modules = [editors_modules]
        extra_editors_modules = self.config.get('extra_editors_modules')
        if extra_editors_modules:
            all_modules.extend(extra_editors_modules)

        for module in all_modules:
            try:
                pkg_loader = loader.find_loader(module)
            except Exception:
                continue
            if pkg_loader is not None:
                modules_to_register[module] = pkg_loader

        editors_found = dict()
        for module_path, pkg_loader in modules_to_register.items():
            for sub_module in loader.walk_packages([pkg_loader.filename]):
                importer, sub_module_name, _ = sub_module
                qname = pkg_loader.fullname + '.' + sub_module_name
                editors_found[qname] = list()
                try:
                    mod = importer.find_module(sub_module_name).load_module(sub_module_name)
                except Exception as exc:
                    LOGGER.warning('Impossible to import tagger editors from: "{}" | {}'.format(module_path, exc))
                    continue

                for cname, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, taggereditor.TaggerEditor):
                        if not hasattr(obj, 'EDITOR_TYPE') or not obj.EDITOR_TYPE:
                            LOGGER.warning('Editor "{}" has not EDITOR_TYPE defined')
                            continue
                        editors_found[qname].append(obj)

        loaded_editors = list()

        for available_editor in available_editors:
            if available_editor in loaded_editors:
                LOGGER.warning(
                    'Editor "{}" of type "{}" is already loaded. Skipping ...'.format(editor_class, editor_type))
                continue
            for editor_classes in editors_found.values():
                if not editor_classes:
                    continue
                for editor_class in editor_classes:
                    editor_type = editor_class.EDITOR_TYPE
                    if editor_type == available_editor:
                        new_editor = editor_class(project=self._project)
                        self.add_editor(new_editor)
                        loaded_editors.append(editor_type)

        not_loaded_editors = list()
        for available_editor in available_editors:
            if available_editor not in loaded_editors:
                not_loaded_editors.append(available_editor)

        if not_loaded_editors:
            LOGGER.warning('Was not possible to load following tag editors: {}!'.format(not_loaded_editors))

    def _fill_new_tag_data_node(self, tag_data_node, current_selection):
        """
        Fills given tag data node with proper data
        :param tag_data_node:
        :param tag_data_node:
        """

        tp.Dcc.add_string_attribute(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
        tp.Dcc.set_string_attribute_value(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME,
            attribute_value=self._project.tag_type_id)
        tp.Dcc.unkeyable_attribute(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
        tp.Dcc.hide_attribute(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
        tp.Dcc.lock_attribute(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
        tp.Dcc.add_message_attribute(
            node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.NODE_ATTRIBUTE_NAME)

        if current_selection:
            if not tp.Dcc.attribute_exists(
                    node=current_selection,
                    attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_ATTRIBUTE_NAME):
                tp.Dcc.add_message_attribute(
                    node=current_selection,
                    attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_ATTRIBUTE_NAME)
            tp.Dcc.unlock_attribute(
                node=current_selection, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_ATTRIBUTE_NAME)
            tp.Dcc.unlock_attribute(
                node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.NODE_ATTRIBUTE_NAME)
            tp.Dcc.connect_attribute(
                tag_data_node, artellapipe.TagsMgr().TagDefinitions.NODE_ATTRIBUTE_NAME,
                current_selection, artellapipe.TagsMgr().TagDefinitions.TAG_DATA_ATTRIBUTE_NAME)
            tp.Dcc.lock_attribute(
                node=current_selection, attribute_name=artellapipe.TagsMgr().TagDefinitions.TAG_DATA_ATTRIBUTE_NAME)
            tp.Dcc.lock_attribute(
                node=tag_data_node, attribute_name=artellapipe.TagsMgr().TagDefinitions.NODE_ATTRIBUTE_NAME)
            tp.Dcc.select_object(current_selection)

    def _update_ui(self):
        """
        If a valid Maya object is selected, tagger tabs is show or hide otherwise
        """

        if artellapipe.TagsMgr().current_selection_has_metadata_node():
            self._stack.slide_in_index(1)
        else:
            self._stack.slide_in_index(0)

    def _update_current_info(self):
        """
        Internal callback function that updates the widget that is showed in the Artella Tagger UI
        :return:
        """

        current_selection = artellapipe.TagsMgr().get_current_selection()

        self._breadcrumb.set([current_selection])

        self._tagger_info.update_info()

        if not artellapipe.TagsMgr().current_selection_has_metadata_node():
            self._curr_info_image.setPixmap(self._error_pixmap)
            return
        if not artellapipe.TagsMgr().check_if_current_selected_metadata_node_has_valid_info():
            self._curr_info_image.setPixmap(self._warning_pixmap)
            return

        self._curr_info_image.setPixmap(self._ok_pixmap)

    def _on_selection_changed(self, *args, **kwargs):
        """
        Internal callback function that is called each time the user changes scene selection
        """

        sel = artellapipe.TagsMgr().get_current_selection()

        self._update_current_info()
        self._update_ui()
        for editor in self._editors:
            editor.reset()
            editor.update_tag_buttons_state(sel)

    def _on_create_new_tag_data_node_for_current_selection(self):
        """
        Internal callback function
        :return:
        """
        self.create_new_tag_data_node_for_current_selection()
        self.tagDataCreated.emit()
        self._on_selection_changed()

    def _on_remove_tag_data_node(self):
        """
        Internal callback function that is called when Remove Tag Data button is clicked
        """

        self.remove_tag_data_node()
