import io
import re

import uuid
import xml.etree.ElementTree as ET
from typing import Optional, TextIO, Union

from .util import Error, _normalize_arguments

class SemanticService:
    def __init__(self, hive):
        self.hive = hive

    semantic_service = property(lambda self:self.hive.api.GetSemanticService(), doc="Get the semantic service")

    def load_namespace(self, nodeset: Union[TextIO, str], module_name: Optional[str]=None, properties=None, **kw):
        """
        Load a namespace from an nodeset-file. The `nodeset` must either be
        an open, file-like object or a string containing the nodeset definition.

        The loader will search for a Semantics module that has the appropriate URI.
        If the module is not found, a module will be created. The created module
        will have the name given in the `modulename` argument. If the modulename
        is not given. the module will be named based on the URI. The created module
        will have properties given by the `properties` argument

        Arguments:
        nodeset: The nodeset XML source. Either a open, file-like object or a string
        URI: The nodeset model-URI. If not given it is extracted from the source
        modulename: The name of the created module
        properties: The properties of the created module

        Returns:
        The created or exisiting Semantics module corresponding to the URI
        """
        node_xml_str = self.load_xml(nodeset)

        props = _normalize_arguments(properties, kw)
        uri = props.get('uri') or self.find_URI(node_xml_str)


        def sem_module():
            for mod in self.hive.modules:
                for prop in mod.properties:
                    if prop.name == 'Uri' and prop.value==uri:
                        return mod

            mod_name = module_name or re.sub(r"\W+", "_", uri).strip('_')
            return self.hive.add_module("ApisSemantics", mod_name, props, Uri=uri)

        module = sem_module()

        def nodeset_chunker(max_len:int=4096)->str:
            buff = []
            chunk_len=0

            with io.StringIO(node_xml_str) as inputf:
                for line in inputf:
                    if chunk_len+len(line)>max_len:
                        yield ''.join(buff)
                        buff = [line]
                        chunk_len = len(line)
                    else:
                        buff.append(line)
                        chunk_len += len(line)
                yield ''.join(buff)

        accessLoader = self.semantic_service.AccessLoader()

        filename = uuid.uuid4().hex + ".xml"
        if accessLoader.CreateXmlFile(filename, "") != 0:
            raise Error('Access loader unable to create temp file for loading')

        for chunk in nodeset_chunker(): 
            accessLoader.AppendXmlFile(filename, chunk)
            
        importResult = accessLoader.ImportAndCheckNamespace(uri, [], False, filename, False)
        # print(f"Import namespace result '{importResult.Value}' on ({self.hive.name})")

        res = accessLoader.DeleteXmlFile(filename)
        return module

    def load_xml(self, nodeset):
        """
        Load an xml file given in the `nodeset` argument. 
        nodeset: The nodeset XML source. Either a open, file-like object or a string

        Returns:
        The nodeset file as string
        """
        if isinstance(nodeset, io.IOBase):
            return nodeset.read()
        elif isinstance(nodeset, str):
            return nodeset
        raise Error('nodeset must be file-like or string')


    def find_URI(self, nodeset:str):
        """
        Find the model URI in a nodeset file.
        """
        root = ET.fromstring(nodeset)

        model = root.find('./{*}Models/{*}Model/[@ModelUri]')
        if model is not None:
            return model.attrib['ModelUri']
        
        
        model=root.find('./{*}NamespaceUris/{*}Uri')
        if model is not None:
            return model.text

        raise Error('Malformed nodeset file.')





