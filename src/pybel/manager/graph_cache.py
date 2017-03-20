# -*- coding: utf-8 -*-

"""This module contains the Graph Cache Manager"""

import logging

from . import models
from .base_cache import BaseCacheManager
from .cache import CacheManager
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import *
from ..graph import BELGraph
from ..io import to_bytes, from_bytes
from ..utils import subdict_matches, parse_datetime

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger(__name__)


class GraphCacheManager(BaseCacheManager):
    """The PyBEL graph cache manager has utilities for inserting and querying the graph store and edge store"""

    def insert_graph(self, graph, store_parts=False):
        """Inserts a graph in the database.

        :param graph: a BEL network
        :type graph: pybel.BELGraph
        :param store_parts: Should the graph be stored in the edge store?
        :type store_parts: bool
        :return: A Network object
        :rtype: models.Network
        """
        graph_bytes = to_bytes(graph)

        network = models.Network(blob=graph_bytes, **graph.document)

        if store_parts:
            # TODO maybe make this part of the cache manager's init function?
            CacheManager(connection=self.connection).ensure_namespace(GOCC_LATEST)
            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        return network

    def store_graph_parts(self, network, graph):
        """Stores the given graph into the edge store.

        :param network: A SQLAlchemy PyBEL Network object
        :type network: models.Network
        :param graph: A BEL Graph
        :type graph: pybel.BELGraph
        """
        nc = {node: self.get_or_create_node(graph, node) for node in graph.nodes_iter()}

        for u, v, graphKey, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]

            if CITATION not in data or EVIDENCE not in data:
                continue

            citation = self.get_or_create_citation(**data[CITATION])
            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            bel = decanonicalize_edge(graph, u, v, graphKey)
            edge = self.get_or_create_edge(
                graphKey=graphKey,
                source=source,
                target=target,
                relation=data[RELATION],
                evidence=evidence,
                bel=bel,
                blob=pickle.dumps(data)
            )

            for key, value in data[ANNOTATIONS].items():
                if key in graph.annotation_url:
                    url = graph.annotation_url[key]
                    annotation = self.get_bel_annotation_entry(url, value)
                    if annotation not in edge.annotations:
                        edge.annotations.append(annotation)

            properties = self.get_or_create_property(graph, data)
            for property in properties:
                if property not in edge.properties:
                    edge.properties.append(property)

            if edge not in network.edges:
                network.edges.append(edge)

    def get_bel_namespace_entry(self, url, value):
        """Gets a given NamespaceEntry object.

        :param url: The url of the namespace source
        :type url: str
        :param value: The value of the namespace from the given url's document
        :type value: str
        :return: An NamespaceEntry object
        :rtype: models.NamespaceEntry
        """
        namespace = self.session.query(models.Namespace).filter_by(url=url).one()
        return self.session.query(models.NamespaceEntry).filter_by(namespace=namespace, name=value).one()

    def get_bel_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry object.

        :param url: The url of the annotation source
        :type url: str
        :param value: The value of the annotation from the given url's document
        :type value: str
        :return: An AnnotationEntry object
        :rtype: models.AnnotationEntry
        """
        annotation = self.session.query(models.Annotation).filter_by(url=url).one()
        return self.session.query(models.AnnotationEntry).filter_by(annotation=annotation, name=value).one()

    def get_or_create_evidence(self, citation, text):
        """Creates entry and object for given evidence if it does not exist.

        :param citation: Citation object obtained from :func:`get_or_create_citation`
        :type citation: models.Citation
        :param text: Evidence text
        :type text: str
        :return: An Evidence object
        :rtype: models.Evidence
        """

        result = self.session.query(models.Evidence).filter_by(text=text).one_or_none()

        if result is None:
            result = models.Evidence(text=text, citation=citation)
            self.session.add(result)
            self.session.flush()

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry and object for given node if it does not exist.

        :param graph: A BEL graph
        :type graph: pybel.BELGraph
        :param node: Key for the node to insert.
        :type node: tuple
        :return: A Node object
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)
        blob = pickle.dumps(graph.node[node])
        node_data = graph.node[node]

        result = self.session.query(models.Node).filter_by(bel=bel).one_or_none()
        if result is None:
            type = node_data[FUNCTION]

            if NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_url:
                namespace = node_data[NAMESPACE]
                url = graph.namespace_url[namespace]
                namespaceEntry = self.get_bel_namespace_entry(url, node_data[NAME])
                result = models.Node(type=type, namespaceEntry=namespaceEntry, bel=bel, blob=blob)

            elif NAMESPACE in node_data and node_data[NAMESPACE] in graph.namespace_pattern:
                namespacePattern = graph.namespace_pattern[node_data[NAMESPACE]]
                result = models.Node(type=type, namespacePattern=namespacePattern, bel=bel, blob=blob)

            else:
                result = models.Node(type=type, bel=bel, blob=blob)

            if VARIANTS in node_data or FUSION in node_data:
                result.is_variant = True
                result.fusion = FUSION in node_data
                result.modifications = self.get_or_create_modification(graph, node_data)

            self.session.add(result)
            self.session.flush()

        return result

    def get_or_create_edge(self, graphKey, source, target, evidence, bel, relation, blob):
        """Creates entry for given edge if it does not exist.

        :param graphKey: Key that identifies the order of edges and weather an edge is artificially created or extracted
                        from a valid BEL statement.
        :type graphKey: tuple
        :param source: Source node of the relation
        :type source: models.Node
        :param target: Target node of the relation
        :type target: models.Node
        :param evidence: Evidence object that proves the given relation
        :type evidence: models.Evidence
        :param bel: BEL statement that describes the relation
        :type bel: str
        :param relation: Type of the relation between source and target node
        :type relation: str
        :param blob: A blob of the edge data object.
        :type blob: blob
        :return: An Edge object
        :rtype: models.Edge
        """
        result = self.session.query(models.Edge).filter_by(bel=bel).one_or_none()

        if result is None:
            result = models.Edge(graphIdentifier=graphKey, source=source, target=target, evidence=evidence, bel=bel,
                                 relation=relation, blob=blob)

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None):
        """Creates entry for given citation if it does not exist.

        :param type: Citation type (e.g. PubMed)
        :type type: str
        :param name: Title of the publication that is cited
        :type name: str
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :type reference: str
        :param date: Date of publication in ISO 8601 format
        :type date: str
        :param authors: List of authors separated by |
        :type authors: str
        :return: A Citation object
        :rtype: models.Citation
        """

        result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one_or_none()

        if result is None:
            if date:
                date = parse_datetime(date)
            else:
                date = None

            result = models.Citation(type=type, name=name, reference=reference, date=date)

            if authors is not None:
                for author in authors.split('|'):
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)
            self.session.flush()

        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param name: An author's name
        :type name: str
        :return: An Author object
        :rtype: models.Author
        """
        result = self.session.query(models.Author).filter_by(name=name).one_or_none()

        if result is None:
            result = models.Author(name=name)
            self.session.add(result)

        return result

    def get_or_create_modification(self, graph, node_data):
        """Creates a list of modification objects (models.Modification) that belong to the node described by
        node_data.

        :param graph: a BEL graph
        :type graph: pybel.BELGraph
        :param node_data: Describes the given node and contains is_variant information
        :type node_data: dict
        :return: A list of modification objects belonging to the given node
        :rtype: list of models.Modification
        """
        modification_list = []
        if FUSION in node_data:
            modType = FUSION
            node_data = node_data[FUSION]
            p3namespace_url = graph.namespace_url[node_data[PARTNER_3P][NAMESPACE]]
            p3namespaceEntry = self.get_bel_namespace_entry(p3namespace_url, node_data[PARTNER_3P][NAME])

            p5namespace_url = graph.namespace_url[node_data[PARTNER_5P][NAMESPACE]]
            p5namespaceEntry = self.get_bel_namespace_entry(p5namespace_url, node_data[PARTNER_5P][NAME])

            fusion_dict = {
                'modType': modType,
                'p3Partner': p3namespaceEntry,
                'p5Partner': p5namespaceEntry,
            }

            if FUSION_MISSING in node_data[RANGE_3P]:
                fusion_dict.update({
                    'p3Missing': node_data[RANGE_3P][FUSION_MISSING]
                })
            else:
                fusion_dict.update({
                    'p3Reference': node_data[RANGE_3P][FUSION_REFERENCE],
                    'p3Start': node_data[RANGE_3P][FUSION_START],
                    'p3Stop': node_data[RANGE_3P][FUSION_STOP],
                })

            if FUSION_MISSING in node_data[RANGE_5P]:
                fusion_dict.update({
                    'p5Missing': node_data[RANGE_5P][FUSION_MISSING]
                })
            else:
                fusion_dict.update({
                    'p5Reference': node_data[RANGE_5P][FUSION_REFERENCE],
                    'p5Start': node_data[RANGE_3P][FUSION_START],
                    'p5Stop': node_data[RANGE_3P][FUSION_STOP],
                })

            modification_list.append(fusion_dict)
        else:
            for variant in node_data[VARIANTS]:
                modType = variant[KIND]
                if modType == HGVS:
                    modification_list.append({
                        'modType': modType,
                        'variantString': variant[IDENTIFIER]
                    })

                elif modType == FRAGMENT:
                    if FRAGMENT_MISSING in variant:
                        modification_list.append({
                            'modType': modType,
                            'p3Missing': variant[FRAGMENT_MISSING]
                        })
                    else:
                        modification_list.append({
                            'modType': modType,
                            'p3Start': variant[FRAGMENT_START],
                            'p3Stop': variant[FRAGMENT_STOP]
                        })

                elif modType == GMOD:
                    modification_list.append({
                        'modType': modType,
                        'modName': variant[IDENTIFIER][NAME]
                    })

                elif modType == PMOD:
                    modification_list.append({
                        'modType': modType,
                        'modName': variant[IDENTIFIER][NAME],
                        'aminoA': variant[PMOD_CODE] if PMOD_CODE in variant else None,
                        'position': variant[PMOD_POSITION] if PMOD_POSITION in variant else None
                    })

        modifications = []
        for modification in modification_list:
            mod = self.session.query(models.Modification).filter_by(**modification).one_or_none()
            if not mod:
                mod = models.Modification(**modification)
            modifications.append(mod)

        return modifications

    def get_or_create_property(self, graph, edge_data):
        """Creates a list of all subject and object related properties of the edge.

        :param graph: A BEL graph
        :type graph: pybel.BELGraph
        :param edge_data: Describes the context of the given edge.
        :type edge_data: dict
        :return: A list of all subject and object properties of the edge
        :rtype: list of models.Property
        """
        properties = []
        property_list = []
        for participant in (SUBJECT, OBJECT):
            if participant not in edge_data:
                continue

            participant_data = edge_data[participant]
            modifier = participant_data[MODIFIER] if MODIFIER in participant_data else LOCATION
            property_dict = {
                'participant': participant,
                'modifier': modifier
            }

            if modifier in (ACTIVITY, TRANSLOCATION) and EFFECT in participant_data:
                for effect_type, effect_value in participant_data[EFFECT].items():
                    property_dict['relativeKey'] = effect_type
                    if NAMESPACE in effect_value:
                        if effect_value[NAMESPACE] == GOCC_KEYWORD:
                            namespace_url = GOCC_LATEST
                        else:
                            namespace_url = graph.namespace_url[effect_value[NAMESPACE]]
                        property_dict['namespaceEntry'] = self.get_bel_namespace_entry(namespace_url,
                                                                                       effect_value[NAME])
                    else:
                        property_dict['propValue'] = effect_value

                    property_list.append(property_dict)

            elif modifier == LOCATION:
                namespace_url = graph.namespace_url[participant_data[LOCATION][NAMESPACE]]
                property_dict['namespaceEntry'] = self.get_bel_namespace_entry(namespace_url,
                                                                               participant_data[LOCATION][NAME])
                property_list.append(property_dict)

            else:
                property_list.append(property_dict)

        for property_def in property_list:
            property = self.session.query(models.Property).filter_by(**property_def).one_or_none()
            if property is None:
                property = models.Property(**property_def)

            if property not in properties:
                properties.append(property)

        return properties

    def get_graph_versions(self, name):
        """Returns all of the versions of a graph with the given name"""
        return {x for x, in self.session.query(models.Network.version).filter(models.Network.name == name).all()}

    def get_graph(self, name, version=None):
        """Loads most recent graph, or allows for specification of version

        :param name: The name of the graph
        :type name: str
        :param version: The version string of the graph. If not specified, loads most recent graph added with this name
        :type version: None or str
        :return: A BEL Graph
        :rtype: pybel.BELGraph
        """
        if version is not None:
            n = self.session.query(models.Network).filter(models.Network.name == name,
                                                          models.Network.version == version).one()
        else:
            n = self.session.query(models.Network).filter(models.Network.name == name).order_by(
                models.Network.created.desc()).first()

        return from_bytes(n.blob)

    def get_graph_by_id(self, id):
        """Gets the graph from the database by its identifier

        :param id: The graph's database ID
        :type id: int
        :return: A Network object
        :rtype: models.Network
        """
        return self.session.query(models.Network).get(id)

    def drop_graph(self, network_id):
        """Drops a graph by ID

        :param network_id: The network's database id
        :type network_id: int
        """

        # TODO delete with cascade
        self.session.query(models.Network).filter(models.Network.id == network_id).delete()
        self.session.commit()

    def ls(self):
        """Lists network id, network name, and network version triples"""
        return [(network.id, network.name, network.version) for network in self.session.query(models.Network).all()]

    def rebuild_by_edge_filter(self, **annotations):
        """Gets all edges matching the given query annotation values

        :param annotations: dictionary of {key: value}
        :type annotations: dict
        :return: A graph composed of the filtered edges
        :rtype: pybel.BELGraph
        """
        graph = BELGraph()
        for annotation_key, annotation_value in annotations.items():

            annotation_def = self.session.query(models.Annotation).filter_by(keyword=annotation_key).first()
            annotation = self.session.query(models.AnnotationEntry).filter_by(annotation=annotation_def,
                                                                              name=annotation_value).first()
            # Add Annotations to belGraph.annotation_url
            # Add Namespaces to belGraph.namespace_url
            # What about meta information?
            edges = self.session.query(models.Edge).filter(models.Edge.annotations.contains(annotation)).all()
            for edge in edges:
                edge_data = edge.data

                if len(edge_data['source']['key']) == 1:
                    edge_data['source'] = self.help_rebuild_list_components(edge.source)

                if len(edge_data['target']['key']) == 1:
                    edge_data['target'] = self.help_rebuild_list_components(edge.target)

                graph.add_nodes_from((edge_data['source']['node'], edge_data['target']['node']))
                graph.add_edge(edge_data['source']['key'], edge_data['target']['key'], key=edge_data['key'],
                               attr_dict=edge_data['data'])

        return graph

    def help_rebuild_list_components(self, node_object):
        """Builds data and identifier for list node objects.

        :param node_object: Node object defined in models.

        :return: Dictionary with 'key' and 'node' keys.
        """
        node_info = node_object.data
        key = list(node_info['key'])
        data = node_info['data']
        if node_object.type in (COMPLEX, COMPOSITE):
            components = self.session.query(models.Edge).filter_by(source=node_object, relation=HAS_COMPONENT).all()
            for component in components:
                component_key = component.target.data['key']
                key.append(component_key)

        elif node_object.type == REACTION:
            reactant_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                            relation=HAS_REACTANT).all()
            product_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                           relation=HAS_PRODUCT).all()
            reactant_keys = tuple(reactant.target.data['key'] for reactant in reactant_components)
            product_keys = tuple(product.target.data['key'] for product in product_components)
            key.append(reactant_keys)
            key.append(product_keys)

        return {'key': tuple(key), 'node': (tuple(key), data)}

    def get_edge_iter_by_filter(self, **annotations):
        """Returns an iterator over models.Edge object that match the given annotations

        :param annotations: dictionary of {URL: values}
        :type annotations: dict
        :return: An iterator over models.Edge object that match the given annotations
        :rtype: iter of models.Edge
        """
        # TODO make smarter
        for edge in self.session.query(models.Edge).all():
            ad = {a.annotation.name: a.name for a in edge.annotations}
            if subdict_matches(ad, annotations):
                yield edge

    def get_graph_by_filter(self, **annotations):
        """Fills a BEL graph with edges retrieved from a filter

        :param annotations: dictionary of {URL: values}
        :type annotations: dict
        :return: A BEL Graph
        :rtype: pybel.BELGraph
        """
        graph = BELGraph()

        for edge in self.get_edge_iter_by_filter(**annotations):
            if edge.source.id not in graph:
                graph.add_node(edge.source.id, attr_dict=pickle.loads(edge.source.blob))

            if edge.target.id not in graph:
                graph.add_node(edge.target.id, attr_dict=pickle.loads(edge.target.blob))

            graph.add_edge(edge.source.id, edge.target.id, attr_dict=pickle.loads(edge.blob))

        return graph

    def query_node(self, bel=None, type=None, namespace=None, name=None, modification_type=None,
                   modification_name=None, as_dict_list=False):
        """Run a query over all nodes in the PyBEL cache.

        :param bel: BEL term that describes the biological entity. e.g. p(HGNC:APP)
        :param bel: str
        :param type: Type of the biological entity. e.g. Protein
        :type type: str
        :param namespace: Namespace keyword that is used in BEL. e.g. HGNC
        :type namespace: str
        :param name: Name of the biological entity. e.g. APP
        :type name: str
        :param modification_name:
        :type modification_name: str
        :param modification_type:
        :type modification_type: str
        :param as_dict_list:
        :type as_dict_list: bool
        :return:
        """
        q = self.session.query(models.Node)

        if bel:
            q = q.filter(models.Node.bel.like(bel))

        if type:
            q = q.filter(models.Node.type.like(type))

        if namespace or name:
            q = q.join(models.NamespaceEntry)
            if namespace:
                q = q.join(models.Namespace).filter(models.Namespace.keyword.like(namespace))
            if name:
                q = q.filter(models.NamespaceEntry.name.like(name))

        if modification_type or modification_name:
            q = q.join(models.Modification)
            if modification_type:
                q = q.filter(models.Modification.modType.like(modification_type))
            if modification_name:
                q = q.filter(models.Modification.modName.like(modification_name))

        result = q.all()

        if as_dict_list:
            dict_list = [node.data for node in result]
            return dict_list
        else:
            return result

    def query_edge(self, bel=None, source=None, target=None, relation=None, citation=None,
                   evidence=None, annotation=None, property=None, as_dict_list=False):
        """Builds a query to be run against all edges in the PyBEL cache.

        :param bel: BEL statement that represents the desired edge.
        :type bel: str
        :param source: BEL term of source node e.g. p(HGNC:APP) or models.Node object.
        :type source: str or models.Node
        :param target: BEL term of target node e.g. p(HGNC:APP) or models.Node object.
        :type target: str or models.Node
        :param relation: The relation that should be present between source and target node.
        :type relation: str
        :param citation: The citation that backs the edge up. It is possible to use the reference_id
                         or a models.Citation object.
        :type citation: str or models.Citation
        :param evidence: The supporting text of the edge. It is possible to use a snipplet of the text
                         or a models.Evidence object.
        :type evidence: str or models.Evidence
        :param annotation:
        :param property:
        :param as_dict_list:
        :return:
        """
        q = self.session.query(models.Edge)

        if bel:
            q = q.filter(models.Edge.bel.like(bel))

        if relation:
            q = q.filter(models.Edge.relation.like(relation))

        if annotation:
            q = q.join(models.AnnotationEntry, models.Edge.annotations)
            if isinstance(annotation, dict):
                q = q.join(models.Annotation).filter(models.Annotation.keyword.in_(list(annotation.keys())))
                q = q.filter(models.AnnotationEntry.name.in_(list(annotation.values())))

            elif isinstance(annotation, str):
                q = q.filter(models.AnnotationEntry.name.like(annotation))

        if source:
            if isinstance(source, str):
                source = self.query_node(bel=source)[0]

            if isinstance(source, models.Node):
                q = q.filter(models.Edge.source == source)

                # ToDo: in_() not yet supported for relations
                # elif isinstance(source, list) and len(source) > 0:
                #    if isinstance(source[0], models.Node):
                #        q = q.filter(models.Edge.source.in_(source))

        if target:
            if isinstance(target, str):
                target = self.query_node(bel=target)[0]

            if isinstance(target, models.Node):
                q = q.filter(models.Edge.target == target)

                # elif isinstance(target, list) and len(target) > 0:
                #    if isinstance(target[0], models.Node):
                #        q = q.filter(models.Edge.source.in_(target))

        if citation or evidence:
            q = q.join(models.Evidence)

            if citation:
                if isinstance(citation, models.Citation):
                    q = q.filter(models.Evidence.citation == citation)

                elif isinstance(citation, str):
                    q = q.join(models.Citation).filter(models.Citation.reference.like(citation))

            if evidence:
                if isinstance(evidence, models.Evidence):
                    q = q.filter(models.Edge.evidence == evidence)

                elif isinstance(evidence, str):
                    q = q.filter(models.Evidence.text.like(evidence))

        if property:
            q = q.join(models.Property)

        result = q.all()

        if as_dict_list:
            dict_result = [edge.data for edge in result]
            return dict_result
        else:
            return result

    def query_citation(self, type=None, reference=None, name=None, author=None, date=None, evidence=False,
                       evidence_text=None, as_dict_list=False):
        """Run a query over all citations in the PyBEL cache.

        :param type: Type of the citation. e.g. PubMed
        :type type: str
        :param reference: The identifier used for the citation. e.g. PubMed_ID
        :type reference: str
        :param name: Title of the citation.
        :type name: str
        :param author: The name or a list of names of authors participated in the citation.
        :type author: str or list
        :param date: Publishing date of the citation.
        :type date: str or date
        :param evidence: Weather or not supporting text should be included in the return.
        :type evidence: bool
        :param evidence_text:
        :param as_dict_list:
        :type as_dict_list: bool
        :return: List of PyBEL.manager.models.Citation objects.
        :rtype: list
        """
        q = self.session.query(models.Citation)

        if author:
            q = q.join(models.Author, models.Citation.authors)
            if isinstance(author, str):
                q = q.filter(models.Author.name.like(author))
            elif isinstance(author, list):
                q = q.filter(models.Author.name.in_(author))

        if type:
            q = q.filter(models.Citation.type.like(type))

        if reference:
            q = q.filter(models.Citation.reference == reference)

        if name:
            q = q.filter(models.Citation.name.like(name))

        if date:
            if isinstance(date, date):
                q = q.filter(models.Citation.date == date)

            if isinstance(date, str):
                d = parse_datetime(date)
                q = q.filter(models.Citation.date == d)

        if evidence_text:
            q = q.join(models.Evidence).filter(models.Evidence.text.like(evidence_text))

        result = q.all()

        if as_dict_list:
            dict_result = []
            if evidence or evidence_text:
                for citation in result:
                    for evidence in citation.evidences:
                        dict_result.append(evidence.data)
            else:
                dict_result = [cit.data for cit in result]

            return dict_result

        else:
            return result
