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

__license__ = "Cecill-C"
__revision__ = " $Id$ "

from PyQt4 import QtGui, QtCore, QtSvg
from openalea.grapheditor import qtgraphview, baselisteners
from openalea.grapheditor.qtutils import (mixin_method, safeEffects, AleaQGraphicsColorWheel,
                                          AleaQGraphicsEmitingTextItem, AleaQMenu)
from openalea.visualea.graph_operator import GraphOperator
from openalea.visualea import images_rc


class MemoRects(QtGui.QGraphicsRectItem):

    __handleSize    = 7.5
    __defaultColor  = QtGui.QColor(250, 250, 100)

    def __init__(self, rect, parent=None):
        QtGui.QGraphicsRectItem.__init__(self, rect, parent)
        self.__resizing   = False
        self.__handlePoly = QtGui.QPolygonF([QtCore.QPointF(0, -self.__handleSize),
                                             QtCore.QPointF(0, 0),
                                             QtCore.QPointF(-self.__handleSize,0)])
        self.setFlag(QtGui.QGraphicsItem.ItemStacksBehindParent)
        # -- handle --
        self.__handlePos  = QtCore.QPointF(0,0)
        # -- header --
        self.__headerContentRect = None
        self.__headerRect = None
        # -- color --
        self.__color       = None
        self.__darkerColor = None
        self.__shadowColor = None
        self.setColor(self.__defaultColor.darker(110))
        # -- optionnal cosmetics --
        if safeEffects:
            fx = QtGui.QGraphicsDropShadowEffect()
            fx.setOffset(2,2)
            fx.setBlurRadius(5)
            self.setGraphicsEffect(fx)

    def setColor(self, color):
        self.__color       = color
        self.__darkerColor = color.darker(140)
        self.__shadowColor = color.darker(200)
        self.update()

    def __moveHandleBottomRightTo(self, point):
        delta = point - self.__handlePos
        self.__handlePoly.translate(delta.x(), delta.y())
        self.__handlePos = point

    def setHeaderRect(self, rect):
        myRect = self.boundingRect()
        self.__headerContentRect = rect.adjusted(0,0,0,0)

        rect.setX(0); rect.setY(0)
        myRect.setX(0); myRect.setY(0)

        if rect.bottom() >= (myRect.bottom()-self.__handleSize):
            myRect.setBottom(rect.bottom() + self.__handleSize)
        if rect.right() >= myRect.right():
            myRect.setRight(rect.right())
        else:
            rect.setRight(myRect.right())
        self.__headerRect = rect
        self.__moveHandleBottomRightTo(myRect.bottomRight())
        self.setRect(myRect)
        self.update()

    def mousePressEvent(self, event):
        pos         = event.pos()
        bottomRight = self.boundingRect().bottomRight()
        x, y        = bottomRight.x(), bottomRight.y()
        rect = QtCore.QRectF(x-5, y-5, x+5, y+5)
        if self.__handlePoly.containsPoint(pos, QtCore.Qt.OddEvenFill):
            self.__resizing = True
        else:
            QtGui.QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.__resizing:
            delta = event.pos() - event.lastPos()
            bottomRight = self.boundingRect().bottomRight() + delta
            newRect = QtCore.QRectF(0.,0., bottomRight.x(), bottomRight.y())
            if newRect.contains(self.__headerContentRect.adjusted(0,0,0,self.__handleSize)):
                self.setRect(newRect)
                self.__headerRect = QtCore.QRectF(0.,0., bottomRight.x(), self.__headerContentRect.height())
                self.__moveHandleBottomRightTo(newRect.bottomRight())
        else:
            QtGui.QGraphicsRectItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.__resizing:
            self.__resizing = False
        else:
            QtGui.QGraphicsRectItem.mouseReleaseEvent(self, event)

    def paint(self, painter, paintOptions, widget):
        myRect = self.boundingRect()

        painter.fillRect(self.__headerRect, self.__darkerColor)
        gradTop = self.__headerRect.bottomLeft()
        gradBot = gradTop + QtCore.QPointF(0,4)
        gradient = QtGui.QLinearGradient(gradTop,gradBot)
        gradient.setColorAt(0, self.__shadowColor)
        gradient.setColorAt(1, self.__color)
        brush = QtGui.QBrush(gradient)

        bottomRect = myRect.adjusted(0,self.__headerRect.bottom(),0,0)
        painter.fillRect(bottomRect, brush)

        if not safeEffects:
            oldPen = painter.pen()
            pen = QtGui.QPen()
            pen.setColor(QtGui.QColor(10,10,10,100))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(myRect.adjusted(0.5,0.5,-0.5,-0.5))
            painter.setPen(oldPen)

        painter.setBrush(QtGui.QBrush(self.__darkerColor))
        painter.drawConvexPolygon(self.__handlePoly)



class GraphicalAnnotation(MemoRects, qtgraphview.Vertex):
    """ Text annotation on the data flow """

    __def_string__ = u"click to edit"

    def __init__(self, annotation, graphadapter, parent=None):
        """ Create a nice annotation """
        MemoRects.__init__(self, QtCore.QRectF())
        qtgraphview.Vertex.__init__(self, annotation, graphadapter)
        self.__textItem = AleaQGraphicsEmitingTextItem(self.__def_string__, self)
        self.__textItem.geometryModified.connect(self.setHeaderRect)
        self.__textItem.geometryModified.connect(self.__onTextModified)
        self.__textItem.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)

        self.__colorWheel = AleaQGraphicsColorWheel(radius=6, parent=self)
        self.__colorWheel.colorChanged.connect(self.__onColorWheelChanged)
        self.__colorWheel.setPos(-self.__colorWheel.rect().center())

        self.setZValue(-100)
        self.__textItem.setZValue(-99)
        self.__colorWheel.setZValue(-98)



    annotation = baselisteners.GraphElementListenerBase.get_observed

    def initialise_from_model(self):
        self.annotation().get_ad_hoc_dict().simulate_full_data_change(self, self.annotation())

    #####################
    # ----Qt World----  #
    #####################
    itemChange = mixin_method(qtgraphview.Vertex, QtGui.QGraphicsTextItem,
                              "itemChange")

    def __onTextModified(self):
        self.deaf(True)
        text = unicode(self.__textItem.toPlainText())
        if(text != self.__def_string__):
            self.store_view_data(text=text)
        self.deaf(False)

    def __onColorWheelChanged(self, color):
        self.store_view_data(color=[color.red(),
                                    color.green(),
                                    color.blue()])

    def setRect(self, rect):
        self.deaf(True)
        p2 = rect.width(), rect.height()
        self.store_view_data(rectP2=p2)
        MemoRects.setRect(self, rect)
        self.deaf(False)

    #########################
    # ----Other things----  #
    #########################
    def notify(self, sender, event):
        if event:
            if event[0] == "metadata_changed":
                if event[1] == "text":
                    self.set_text(event[2])
                    return
                elif event[1] == "rectP2":
                    rect = QtCore.QRectF(0,0,event[2][0],event[2][1])
                    MemoRects.setRect(self,rect)
                    self.setHeaderRect(self.__textItem.boundingRect())
                elif event[1] == "color":
                    col = event[2]
                    if col:
                        color = QtGui.QColor(*col)
                        self.setColor(color)
        qtgraphview.Vertex.notify(self, sender, event)

    def set_text(self, text):
        if text == u"" :
            text = self.__def_string__
        self.__textItem.setPlainText(text)

    def store_view_data(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.vertex().get_ad_hoc_dict().set_metadata(k, v)

    def get_view_data(self, key):
        return self.vertex().get_ad_hoc_dict().get_metadata(key)