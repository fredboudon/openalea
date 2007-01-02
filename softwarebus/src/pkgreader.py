# -*- python -*-
#
#       OpenAlea.SoftwareBus: OpenAlea software bus
#
#       Copyright or (C) or Copr. 2006 INRIA - CIRAD - INRA  
#
#       File author(s): Christophe Pradal <christophe.prada@cirad.fr>
#                       Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
# 
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#

__doc__="""
This module contains abstration to read and write configuration files.
Configuration can be read from python files or XML files and written to xml file

"""

__license__= "Cecill-C"
__revision__=" $Id$ "


from core import Package, NodeFactory
from subgraph import SubGraphFactory
import os
import sys


class FormatError(Exception):
    def __init__(self, str):
        Exception.__init__(self, str)

################################################################################

# READERS


class PackageReader :
    """ Default base class (define the interface) """

    def __init__(self, filename):
        """ """
        
        self.filename = filename


    def get_packages(self, pkgmanager):
        """ Return a list of package object """

        # Function must be overloaded
        raise RuntimeError()



class PyPackageReader(PackageReader):
    """ Read package as a Python file """

    def __init__(self, filename):
        """ 
        Filename must be relative to a python sys path
        """
        
        PackageReader.__init__(self, filename)


    def filename_to_module (self, filename):
        """ Transform the filename ending with .py to the module name """

        # delete the .py at the end
        if(filename.endswith('.py')):
            modulename = filename[:-3]

        l = modulename.split(os.path.sep)
        modulename = '.'.join(l)

        return modulename


    def get_packages(self, pkgmanager):
        """ Return a list of package objects """

        retlist = []

        import sys, os

        basename = os.path.basename(self.filename)
        basedir = os.path.abspath( os.path.dirname( self.filename ))

        
        if(not basedir in sys.path):
            sys.path.append(basedir)
            oldsyspath = sys.path[:]
        else :
            oldsyspath = None


        modulename = self.filename_to_module(basename)

        exec('import %s as wralea') % (modulename)

        
        # Call the function  in the wralea.py
        ret = wralea.register_packages( pkgmanager )

        if(oldsyspath):
            sys.path = oldsyspath

        return ret



class XmlPackageReader(PackageReader):
    """ Read package as a XML file """

    def __init__(self, filename):
        PackageReader.__init__(self, filename)

        self.__currentNode__ = None
        self.doc = None

        print self.filename


    def __del__(self):
        """ Release DOM objects """
        if(self.doc):
            self.doc.unlink()

    def load_xml(self, filename):
        
        from xml.dom.minidom import parse

        if(self.doc): self.doc.unlink()
        self.doc = parse(filename)

    def get_attribute(self, attr_dict, name):
        """ Return the ascii string of an attribute
        @param attr dict : minidom attribute dictionnary
        @param name : name of the attribute (string)
        """
        return attr_dict[name].value.encode('ascii')

    def getText(self, xmlnode):
        """ Return the text of an xmlnode"""
        val = xmlnode.childNodes[0].nodeValue
        return val.strip()

 
    def get_root_element(self):

	if self.__currentNode__ == None:
            self.__currentNode__ = self.doc.documentElement

        return self.__currentNode__

    def get_xml_wraleapath(self, pkgmanager):
        """ parse Xml to retrieve wraleapath
        The new path are added to the pkgmanager
        """

        for path in self.get_root_element().getElementsByTagName("wraleapath"):

            attr = path.attributes
            try:
                value = self.get_attribute(attr, "value")
            except:
                raise FormatError("<wraleapath> must have value attribute")


            pkgmanager.add_wraleapath(value)


    def get_xml_packages(self, pkgmanager):
        """ Parse Xml to retrieve package info, nodefactory and subgraph
        return the created package list
        """
    
        packagelist = []

        for package in self.get_root_element().getElementsByTagName("package"):

            attr = package.attributes
            try:
                name = self.get_attribute(attr, "name")
            except:
                raise FormatError("<package> must have name attribute")

            metainfo = {}

            for info in ("license", "version",
                         "authors", "institute", "description", "publication"):
                try:
                    value = self.getText(package.getElementsByTagName(info)[0])
                    print value
                    metainfo[info] = value
                except:
                    pass

            pkg = Package(name, metainfo)

            # Build the node factories and add them to the package
            nf_list = self.get_xml_nodefactory(package, pkgmanager)
            if(nf_list) : map( pkg.add_nodefactory, nf_list)

            # Build the subgraph factories and add them to the package
            sg_list = self.get_xml_subgraphfactory(package, pkgmanager)
            if(sg_list) : map( pkg.add_nodefactory, sg_list)

            packagelist.append(pkg)

        return packagelist


    def get_xml_nodefactory(self, xmlnode, pkgmanager):
        """ Parse Xml to retrieve nodefactory info
        Return a list of node factory
        """

        factorylist = []
        for nodefactory in xmlnode.getElementsByTagName("nodefactory"):

            attr = nodefactory.attributes
            try:
                name = self.get_attribute(attr, "name")
                module = self.get_attribute(attr, "module")
                category = self.get_attribute(attr, "category")
            except:
                raise FormatError("<nodefactory> must have name, module and category attributes")

            try: desc = self.getText(nodefactory.getElementsByTagName("description")[0])
            except: desc = "" 

            try: doc = self.getText(nodefactory.getElementsByTagName("doc")[0])
            except: doc = ""

            try:
                node = nodefactory.getElementsByTagName("node")[0]
                nodename = self.get_attribute(node.attributes, "class")
                print nodename
                
                widget = nodefactory.getElementsByTagName("widget")[0]
                widgetname = self.get_attribute(widget.attributes, "class")
            except:
                raise FormatError('<nodefactory> must have <node class="..."/> and <widget class="..."/>')
            
            nf = NodeFactory(name = name, 
                             desc = desc, 
                             doc = doc, 
                             cat  = category, 
                             module = module,
                             nodeclass = nodename, 
                             widgetclass = widgetname, 
                             )

            factorylist.append(nf)

        return factorylist




    def get_xml_subgraphfactory(self, xmlnode, pkgmanager):
        """ Parse Xml to retrieve subgraphfactory info """

        factorylist = []
        map_id = {} # mapping between xml id and subgraph id
        
        for subgraph in xmlnode.getElementsByTagName("subgraph"):
            
            attr = subgraph.attributes
            try:
                name = self.get_attribute(attr, "name")
                category = self.get_attribute(attr, "category")
            except :
                raise FormatError("<subgraph> must have name and category attributes")

            try: desc = self.getText(subgraph.getElementsByTagName("description")[0])
            except: desc = "" 

            try: doc = self.getText(subgraph.getElementsByTagName("doc")[0])
            except: doc = ""

            sg = SubGraphFactory(pkgmanager, name = name, desc = desc, 
                             doc = doc, cat  = category)

            for element in subgraph.getElementsByTagName("element"):
                attr = element.attributes
                try:
                    package_id = self.get_attribute(attr, "package_id")
                    factory_id = self.get_attribute(attr, "factory_id")
                    id = self.get_attribute(attr, "id")
                except:
                    raise FormatError("<element> must have package_id and factory_id attributes")


                elt_id =  sg.add_nodefactory(package_id, factory_id)

                map_id[id] = elt_id

            for connection in subgraph.getElementsByTagName("connect"):
                attr = connection.attributes
                try:
                    src_id = self.get_attribute(attr, "src_id")
                    src_port = self.get_attribute(attr, "src_port")
                    dst_id = self.get_attribute(attr, "dst_id")
                    dst_port = self.get_attribute(attr, "dst_port")
                except:
                    raise FormatError("<connect> must have src_id, src_port, dst_id, dst_port attributes")
                

                sg.connect (map_id[src_id], int(src_port), map_id[dst_id], int(dst_port) )

            factorylist.append(sg)

            return factorylist
                

    def get_packages(self, pkgmanager):
        """ Return a list of package object """

        from xml.dom.minidom import parse
        self.doc = parse(self.filename)

        self.get_xml_wraleapath(pkgmanager)
        pkglist = self.get_xml_packages(pkgmanager)

        # Add package to the manager
        map(pkgmanager.add_package, pkglist)

        return pkglist



################################################################################

    # WRITERS



class XmlWriter:
    """ base class for all XML Writer """

    def fill_structure(self, newdoc, top_element):
        """ Fill XML structure in newdoc with top_element as Root """

        raise RuntimeError()

class NodeFactoryXmlWriter(XmlWriter):
    """ Class to write a node factory to XML """

    def __init__(self, factory):
        """ Constructor :
        @param factory : the instance to serialize
        """
        
        self.factory = factory
        

    def fill_structure(self, newdoc, top_element):
        """ Fill XML structure in newdoc with top_element as Root """

        nodefactory = self.factory
    
        # <nodefactory>
        nf_elt = newdoc.createElement ('nodefactory')
        nf_elt.setAttribute("name", nodefactory.name)
        nf_elt.setAttribute("category", nodefactory.category)
        nf_elt.setAttribute("module", nodefactory.module )
    
        top_element.appendChild(nf_elt) 

        elt = newdoc.createElement("description")
        node = newdoc.createTextNode(nodefactory.description)
        elt.appendChild(node)
        nf_elt.appendChild(elt)

        elt = newdoc.createElement("doc")
        node = newdoc.createTextNode(nodefactory.doc)
        elt.appendChild(node)
        nf_elt.appendChild(elt)

        elt = newdoc.createElement("node")
        elt.setAttribute("class", str(nodefactory.nodeclass_name))
        nf_elt.appendChild(elt)
        
        elt = newdoc.createElement("widget")
        elt.setAttribute("class", str(nodefactory.widgetclass_name))
        nf_elt.appendChild(elt)

    

class SubGraphFactoryXmlWriter(XmlWriter):
    """ Class to write a subgraph to XML """

    def __init__(self, factory):
        """ Constructor :
        @param factory : the instance to serialize
        """
        
        self.factory = factory

    def fill_structure(self, newdoc, top_element):
        """ Fill XML structure in newdoc with top_element as Root """

        factory = self.factory
    
        # <subgraph>
        sg_elt = newdoc.createElement ('subgraph')
        sg_elt.setAttribute("name", factory.name)
        sg_elt.setAttribute("category", factory.category)
        top_element.appendChild(sg_elt) 

        elt = newdoc.createElement('description')
        node = newdoc.createTextNode(factory.description)
        elt.appendChild(node)
        sg_elt.appendChild(elt)

        elt = newdoc.createElement('doc')
        node = newdoc.createTextNode(factory.doc)
        elt.appendChild(node)
        sg_elt.appendChild(elt)

        for (id, (package_id, factory_id)) in factory.elt_factory.items():

            elt = newdoc.createElement ('element')
            elt.setAttribute("package_id", package_id)
            elt.setAttribute("factory_id", factory_id)
            elt.setAttribute("id", id)
            sg_elt.appendChild(elt)

        for ( (dst_id, dst_port), (src_id, src_port) ) in factory.connections.items():

            elt = newdoc.createElement ('connect')
            elt.setAttribute("src_id", src_id)
            elt.setAttribute("src_port", str(src_port))
            elt.setAttribute("dst_id", dst_id)
            elt.setAttribute("dst_port", str(dst_port))
            sg_elt.appendChild(elt)


class PackageXmlWriter(XmlWriter):
    """ Class to write a subgraph to XML """

    def __init__(self, package):
        """ Constructor :
        @param package : the package to serialize
        """
        self.pkg = package

        
    def fill_structure(self, newdoc, top_element):
        """ Fill Xml structure with package data """

        package = self.pkg
        
        # <package>
        pkg_elt = newdoc.createElement('package')
        pkg_elt.setAttribute("name", package.name)
        top_element.appendChild(pkg_elt) 

        for info in package.metainfo:

            elt = newdoc.createElement(info)
            node = newdoc.createTextNode(package.metainfo[info])
            elt.appendChild(node)
            pkg_elt.appendChild(elt)

        for n in package.get_node_names():
            nf = package.get_nodefactory(n)

            writer = nf.get_xmlwriter()
            writer.fill_structure(newdoc, pkg_elt)



class OpenAleaWriter(XmlWriter):
    """ Class to write the whole system configuration """

    def __init__(self, pkgmanager):
        """ Constructor:
        @param pkgmanager : a package manager instance
        """
        self.pmanager = pkgmanager

    def fill_structure(self, newdoc, top_element):
        """ Fill XML structure in newdoc with top_element as Root """

        for path in self.pmanager.wraleapath:
            elt = newdoc.createElement('wraleapath')
            elt.setAttribute("value", str(path))
            top_element.appendChild(elt) 

        # for each package object
        for p in self.pmanager.values():
            writer= PackageXmlWriter(p)
            writer.fill_structure(newdoc, top_element)
            

        
    def write_config(self, filename):
        """ Write configuration on filename """

        from xml.dom.minidom import getDOMImplementation

        impl = getDOMImplementation()

        newdoc = impl.createDocument(None, "openalea", None)
        top_element = newdoc.documentElement

        self.fill_structure(newdoc, top_element)

        f = open(filename, 'w')
        f.write(newdoc.toprettyxml())
        f.close()

