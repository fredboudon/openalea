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
"""Interfaces for the generic graph view module. The graph view widget
won't check for inheritance of the object's it is passed. Instead, it
will check the interfaces match more or less."""


from openalea.core import interface

__all__=["IGraphViewStrategies", "IGraphViewElement", "IGraphViewNode"]


class IGraphViewStrategies(object):
    """Define implementations of this trait 
    class to define the behaviour of the graph.
    For example : DataFlowGraphViewTrait, TreeGraphViewTrait, 
    NetworkGraphViewTrait..."""
    __metaclass__ = interface.IInterfaceMetaClass

    @classmethod
    def get_graph_model_type(cls):
        """Returns the classobj defining the graph type"""
        raise NotImplementedError

    @classmethod
    def get_direction_vector(cls):
        """Returns an (x,y) vector defining the Y direction of the tree.
        (0,-1) is upward, (0,1) is downward."""
        raise NotImplementedError

    @classmethod
    def get_node_widget_type(cls):
        """Return a classobj defining the type of widget 
        that represents a node"""
        raise NotImplementedError

    @classmethod
    def get_edge_widget_type(cls):
        """Return a classobj defining the type of widget 
        that represents an edge"""
        raise NotImplementedError

    @classmethod
    def get_floating_edge_widget_type(cls):
        """Return a classobj defining the type of widget 
        that represents an edge"""
        raise NotImplementedError

    @classmethod
    def get_annotation_widget_type(cls):
        """Return a classobj defining the type of widget
        that represents an annotation"""
        raise NotImplementedError


class IGraphViewElement(object):
    """Base class for elements in a GraphView"""
    __metaclass__ = interface.IInterfaceMetaClass

    def position_changed(self, *args):
        """Place the element's representation in
        the view space"""
        raise NotImplementedError

    def add_to_view(self, view):
        """add this element to the graphical view"""
        raise NotImplementedError

    def remove_from_view(self, view):
        """remove this element from the graphical view"""
        raise NotImplementedError        

    def notify(self, sender, event):
        """called by the observed objects
        Expected event = ("MetaDataChanged", "position", [x,x], list)
        """
        raise NotImplementedError


#yep, it is the same right now, but it might change in the futur
IGraphViewNode = IGraphViewElement 

class IGraphViewAnnotation(IGraphViewElement):
    """Interface for Annotations"""

    def __init__(self, annotation):
        raise NotImplementedError

    def set_text(self, text):
        """to change the visible text"""
        raise NotImplementedError

    def notify(self, sender, event):
        __doc__=IGraphViewElement.notify.__doc__ + \
            """("MetaDataChanged", "text", "a string", str)"""
        raise NotImplementedError


class IGraphViewEdge(IGraphViewElement):
    """Interface for edges between two nodes."""

    def __init__(self, edge, src, dest):
        raise NotImplementedError

    def update_line_source(self, *pos):
        """updates this edge's starting point. Called when
        source point is moved"""
        raise NotImplementedError

    def update_line_destination(self, *pos):
        """updates this edge's ending point. Called when
        dest point is moved"""
        raise NotImplementedError

    def notify(self, sender, event):
        __doc__=IGraphViewElement.notify.__doc__ + \
            """("MetaDataChanged", "canvasPosition", [x,x], list)"""
        raise NotImplementedError

class IGraphFloatingViewEdge(IGraphViewElement):
    """Interface for edges to be drawn during
    creation time, ie while the user drags."""

    def __init__(self, src):
        raise NotImplementedError

    def consolidate(self, model):
        """returns whatever object is under the mouse
        pointer at the time the button was releases"""
        raise NotImplementedError
