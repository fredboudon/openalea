# -*- python -*-
#
#       OpenAlea.Visualea: OpenAlea graphical user interface
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Daniel Barbeau <daniel.barbeau@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################

import sys, numpy, weakref
from PyQt4 import QtCore, QtGui

from .. import gengraphview 
from .. import qtgraphview 
from .. import qtutils

from openalea.core.observer import lock_notify, AbstractListener


"""

"""

class AleaQGraphicalNode(QtGui.QGraphicsWidget, qtgraphview.QtGraphViewNode):

    #color of the small box that indicates evaluation
    eval_color = QtGui.QColor(255, 0, 0, 200)

    def __init__(self, node, parent=None):
        QtGui.QGraphicsWidget.__init__(self, parent)
        qtgraphview.QtGraphViewNode.__init__(self, node)

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(1)

        # ---Small box when the node is being evaluated---
        self.modified_item = QtGui.QGraphicsRectItem(5,5,7,7, self)
        self.modified_item.setBrush(self.eval_color)
        self.modified_item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.modified_item.setVisible(False)

        # ---Sub items layout---
        layout = QtGui.QGraphicsLinearLayout()
        layout.setOrientation(QtCore.Qt.Vertical)
        layout.setSpacing(2)

        self._inConnectorLayout  = QtGui.QGraphicsLinearLayout()
        self._outConnectorLayout = QtGui.QGraphicsLinearLayout()
        self._caption            = QtGui.QLabel(node.internal_data["caption"])
        captionProxy             = qtutils.AleaQGraphicsProxyWidget(self._caption)

        layout.addItem(self._inConnectorLayout)
        layout.addItem(captionProxy)
        layout.addItem(self._outConnectorLayout)

        layout.setAlignment(self._inConnectorLayout, QtCore.Qt.AlignHCenter)
        layout.setAlignment(self._outConnectorLayout, QtCore.Qt.AlignHCenter)
        layout.setAlignment(captionProxy, QtCore.Qt.AlignHCenter)
        self._inConnectorLayout.setSpacing(8)
        self._outConnectorLayout.setSpacing(8)

        self.setLayout(layout)

        #hack around a Qt4.4 limitation
        self.__inPorts=[]
        self.__outPorts=[]
        #do the port layout
        self.__layout_ports()
        #tooltip
        self.set_tooltip(node.__doc__)
        self.initialise_from_model()

    def __layout_ports(self):
        """ Add connectors """
        self.nb_cin = 0
        for i,desc in enumerate(self.observed().input_desc):
            self.__add_in_connection(i, desc)
                
        for i,desc in enumerate(self.observed().output_desc):
            self.__add_out_connection(i, desc)

    def __update_ports_ad_hoc_position(self):
        """the canvas position held in the adhoc dict of the ports has to be changed
        from here since the port items, being childs, don't receive moveEvents..."""
        [port().update_canvas_position() for port in self.__inPorts+self.__outPorts]        

    def __add_connection(self, index, connector, layout):
        graphicalConn = AleaQGraphicalConnector(self, index, connector)
        layout.addItem(graphicalConn)
        layout.setAlignment(graphicalConn, QtCore.Qt.AlignHCenter)
        return graphicalConn
        
    def __add_in_connection(self, index, connector):
        port = weakref.ref(self.__add_connection(index, connector, self._inConnectorLayout))
        self.__inPorts.append(port)

    def __add_out_connection(self, index, connector):
        port = weakref.ref(self.__add_connection(index, connector, self._outConnectorLayout))
        self.__outPorts.append(port)


    ####################
    # Observer methods #
    ####################
    def notify(self, sender, event): 
        """ Notification sent by the node associated to the item """
        if(event and event[0] == "start_eval"):
            self.modified_item.setVisible(self.isVisible())
            self.modified_item.update()
            self.update()
            QtGui.QApplication.processEvents()

        elif(event and event[0] == "stop_eval"):
            self.modified_item.setVisible(False)
            self.modified_item.update()
            self.update()
            QtGui.QApplication.processEvents()

        qtgraphview.QtGraphViewNode.notify(self, sender, event)

    def set_tooltip(self, doc=None):
        """ Sets the tooltip displayed by the node item. Doesn't change
        the data."""
        try:
            node_name = self.observed().factory.name
        except:
            node_name = self.observed().__class__.__name__

        try:
            pkg_name = self.observed().factory.package.get_id()
        except:
            pkg_name = ''

        if doc:
            doc = doc.split('\n')
            doc = [x.strip() for x in doc] 
            doc = '\n'.join(doc)
        else:
            if(self.observed().factory):
                doc = self.observed().factory.description
        
        # here, we could process the doc so that the output is nicer 
        # e.g., doc.replace(":params","Parameters ") and so on

        mydoc = doc

        for name in [':Parameters:', ':Returns:', ':Keywords:']:
            mydoc = mydoc.replace(name, '<b>'+name.replace(':','') + '</b><br/>\n')

        self.setToolTip( "<b>Name</b> : %s <br/>\n" % (node_name) +
                         "<b>Package</b> : %s<br/>\n" % (pkg_name) +
                         "<b>Documentation :</b> <br/>\n%s" % (mydoc,))

    def set_caption(self, caption):
        """Sets the name displayed in the node widget, doesn't change
        the node data"""
        self._caption.setText(caption)

    ###############################
    # ----Qt World overloads----  #
    ###############################
    def select_drawing_strategy(self, state):
        if self.observed().get_ad_hoc_dict().get_metadata("use_user_color"):
            return qtgraphview.QtGraphViewNode.select_drawing_strategy(self, "use_user_color")
        else:
            return qtgraphview.QtGraphViewNode.select_drawing_strategy(self, state)

    def polishEvent(self):
        self.__update_ports_ad_hoc_position()
        qtgraphview.QtGraphViewNode.polishEvent(self)
        QtGui.QGraphicsWidget.polishEvent(self)

    def moveEvent(self, event):
        self.__update_ports_ad_hoc_position()
        qtgraphview.QtGraphViewNode.moveEvent(self, event)
        QtGui.QGraphicsWidget.moveEvent(self, event)

    def mousePressEvent(self, event):
        """Overloaded or else edges are created from the node
        not from the ports"""
        QtGui.QGraphicsWidget.mousePressEvent(self, event)




class AleaQGraphicalConnector(QtGui.QGraphicsWidget):
    """ A node connector """
    WIDTH =  10
    HEIGHT = 10

    __size = QtCore.QSizeF(WIDTH, 
                           HEIGHT)

    def __init__(self, parent, index, connector):
        """
        """
        QtGui.QGraphicsWidget.__init__(self, parent)
        self.__index = index
        self.observed = weakref.ref(connector)
        connector.get_ad_hoc_dict().add_metadata("canvasPosition", list)
        connector.set_id(index)

    def canvas_position(self):
        pos = self.rect().center() + self.scenePos()
        return[pos.x(), pos.y()]
        
    def update_canvas_position(self):
        self.observed().get_ad_hoc_dict().set_metadata("canvasPosition", 
                                                       self.canvas_position())
        
    def get_index(self):
        return self.__index


    ##################
    # QtWorld-Layout #
    ##################
    def size(self):
        return self.__size

    def sizeHint(self, blop, blip):
        return self.__size

    def minimumSizeHint(self):
        return self.__size

    def sizePolicy(self):
        return QtGui.QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    ##################
    # QtWorld-Events #
    ##################
    def mousePressEvent(self, event):
        graphview = self.scene().views()[0]
        if (graphview and event.buttons() & QtCore.Qt.LeftButton):
            graphview.new_edge_start(self.canvas_position())
            return

    def paint(self, painter, option, widget):
        size = self.size()
        
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        gradient = QtGui.QLinearGradient(0, 0, 10, 0)
        gradient.setColorAt(1, QtGui.QColor(QtCore.Qt.yellow).light(120))
        gradient.setColorAt(0, QtGui.QColor(QtCore.Qt.darkYellow).light(120))
        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 0))

        painter.drawEllipse(1,1,size.width()-2,size.height()-2)

