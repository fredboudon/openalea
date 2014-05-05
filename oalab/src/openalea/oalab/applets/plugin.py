
class PluginApplet(object):

    def __init__(self):
        self._applet = None

    def __call__(self, mainwindow):
        pass

    def _fill_menu(self, mainwindow, widget):
        # add actions to menu
        if widget.actions():
            for action in widget.actions():
                # Add actions in PanedMenu
                mainwindow.menu.addBtnByAction(*action)

                # add action in classical menu
                pane_name, group_name, act, btn_type = action
                # print pane_name, group_name, act, btn_type
                mainwindow.add_action_to_existing_menu(action=act, menu_name=pane_name, sub_menu_name=group_name)

        # Show/Hide in menu
        ## TODO
        """
        name = widget.windowTitle()
        btn = QtGui.QCheckBox(name, self)
        btn.setChecked(widget.isVisibleTo(self))
        btn.toggled.connect(widget.setVisible)
        # child.visibilityChanged.connect(btn.setChecked)
        action = [["View", "Show", btn, "smallwidget"], ]
        mainwindow.menu.addBtnByAction(action)"""

    def instance(self):
        return self._applet

