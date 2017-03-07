# -*- coding: utf-8 -*-

"""

This module contains the Graph Cache Manager

"""

import logging
import time

from sqlalchemy.orm.exc import NoResultFound

from . import models
from .base_cache import BaseCacheManager
from .utils import parse_datetime
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import *
from ..graph import BELGraph
from ..io import to_bytes, from_bytes
from ..constants import * # PYBEL_AUTOEVIDENCE
from ..parser.utils import subdict_matches

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger(__name__)


class GraphCacheManager(BaseCacheManager):
    def store_graph(self, graph, store_parts=False):
        """Stores a graph in the database

        :param graph: a BEL network
        :type graph: pybel.BELGraph
        :param store_parts: Should the graph be stored in the Edge Store?
        :type store_parts: bool
        :return: A Network object
        :rtype: models.Network
        """
        graph_bytes = to_bytes(graph)

        network = models.Network(blob=graph_bytes, **graph.document)

        if store_parts:
            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        log.info('Stored graph %s in %s seconds', network.name, time.time() - t)

        return network

#    def store_graph_parts(self, network, graph):
#        """

#        :param network:
#        :type network: models.Network
#        :param graph:
#        :type graph: BELGraph
#        :return:
#        """
#        # nc = {node: self.get_or_create_node(decanonicalize_node(graph, node)) for node in graph}

#        self.cache_manager = CacheManager(connection=self.connection)
#        for key, ns_url in graph.namespace_url.items():
#            self.cache_manager.ensure_namespace(ns_url)
#        for key, anno_url in graph.annotation_url.items():
#            self.cache_manager.ensure_annotation(anno_url)

        # FIXME add GOCC ensurement to creation of graph.namespace_url ? --> Extract to constans!!!!
        # GOCC = 'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component.belns'
        # self.cache_manager.ensure_namespace(GOCC)
        # graph.namespace_url['GOCC'] = GOCC

#        nc = {node: self.get_or_create_node(graph, node) for node in graph}

#        for u, v, k, data in graph.edges_iter(data=True, keys=True):
#            source, target = nc[u], nc[v]
#            edge_bel = decanonicalize_edge(graph, u, v, k)

#            if CITATION not in data and BEL_KEYWORD_SUPPORT not in data:  # have to assume it's a valid graph at this point
#                data[CITATION] = dict(type='Other', name=PYBEL_AUTOEVIDENCE, reference='0')
#                data[BEL_KEYWORD_SUPPORT] = PYBEL_AUTOEVIDENCE

#            citation = self.get_or_create_citation(**data[CITATION])
#            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])
#            edge = self.get_or_create_edge(k, source, target, evidence, edge_bel, data[RELATION])

#            # edge.properties = self.get_or_create_property(graph, data)
#            properties = self.get_or_create_property(graph, data)
#            for property in properties:
#                if property not in edge.properties:
#                    edge.properties.append(property)

#            for key, value in data[ANNOTATIONS].items():
#                if key not in graph.annotation_url:
#                    # FIXME not sure how to handle local annotations. Maybe show warning that can't be cached?
#                    continue

#                annotation_url = graph.annotation_url[key]
#                annotation_id = self.cache_manager.annotation_id_cache[annotation_url][value]
#                if self.get_annotation(annotation_id) not in edge.annotations:
#                    edge.annotations.append(self.get_annotation(annotation_id))

#            if edge not in network.edges:
#                network.edges.append(edge)#

                # self.session.commit()

    def store_graph_parts(self, network, graph):
        """Stores the given graph into the Edge Store

        :param network: A SQLAlchemy PyBEL Network objet
        :type network: models.Network
        :param graph: A BEL Graph
        :type graph: pybel.BELGraph
        """
        nc = {node: self.get_or_create_node(graph, node) for node in graph.nodes_iter()}

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]

            if CITATION not in data or EVIDENCE not in data:
                continue

            citation = self.get_or_create_citation(**data[CITATION])
            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            bel = decanonicalize_edge(graph, u, v, k)
            edge = models.Edge(
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
                    edge.annotations.append(self.get_bel_annotation_entry(url, value))

            network.edges.append(edge)

    def get_bel_annotation_entry(self, url, value):
        """Gets a given AnnotationEntry

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
        """Creates entry for given evidence if it does not exist.

        :param citation: Citation object obtained from get_or_create_citation()
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
            # self.session.commit()  # TODO remove?

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry for given node if it does not exist.

        :param graph: A BEL network
        :type graph: pybel.BELGraph
        :param node: Key for the node to insert.
        :type node: tuple
        :return: A Node object
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)
        blob = pickle.dumps(graph.node[node])

        result = self.session.query(models.Node).filter_by(bel=bel).one_or_none()

        if result is None:
            result = models.Node(bel=bel, blob=blob)
            self.session.add(result)

        return result

    def get_or_create_edge(self, source, target, evidence, bel, relation):
        """Creates entry for given edge if it does not exist.

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
        :return: An Edge object
        :rtype: models.Edge
        """
        result = self.session.query(models.Edge).filter_by(bel=bel).one_or_none()

        if result:
            return result

        result = models.Edge(source=source, target=target, relation=relation, evidence=evidence, bel=bel)

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None, comments=None):
        """Creates entry for given citation if it does not exist.

        :param type: Citation type (e.g. PubMed)
        :type type: str
        :param name: Title of the publication that is cited
        :type name: str
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :type reference: str
        :param date: Date of publication
        :type date: date
        :param authors: List of authors separated by |
        :type authors: str
        :param comments: Comments on the citation
        :type comments: str
        :return: A Citation object
        :rtype: models.Citation
        """

        result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one_or_none()

        if result is None:
            if date is not None:
                date = parse_datetime(date)

            result = models.Citation(type=type, name=name, reference=reference, date=date, comments=comments)

            if authors is not None:
                for author in authors.split('|'):
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)

        return result

    def get_or_create_author(self, name):
        """Gets an author by name, or creates one

        :param name: An author's name
        :type name: str
        :return: An Author object
        :rtype: models.Author
        """
        result = self.session.query(models.Author).filter_by(name=name).one_or_none()

        if result:
            return result

        result = models.Author(name=name)
        self.session.add(result)

        return result

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

    def get_or_create_edge(self, key, source, target, evidence, bel, relation):
        """Creates entry for given edge if it does not exist.

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
        :rtype: models.Edge
        """
        try:
            result = self.session.query(models.Edge).filter_by(bel=bel).one()
        except:
            result = models.Edge(graphIdentifier=key, source=source, target=target, evidence=evidence, bel=bel,
                                 relation=relation)

        return result

    def get_or_create_node(self, graph, node):
        """Creates entry for given node if it does not exist.

        :param graph: A BEL network
        :type graph: :class:`pybel.BELGraph`
        :param node: Key for the node to insert.
        :type node: tuple
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)
        node_data = graph.node[node]

        try:
            result = self.session.query(models.Node).filter_by(bel=bel).one()
        except NoResultFound:
            type = node_data[FUNCTION]

            if NAMESPACE in node_data:
                url = graph.namespace_url[node_data[NAMESPACE]]
                name_id = self.cache_manager.namespace_id_cache[url][node_data[NAME]]
                namespaceEntry = self.get_name(name_id)

                result = models.Node(bel=bel, namespaceEntry=namespaceEntry, type=type)

            else:
                result = models.Node(bel=bel, type=type)

            if type in ('ProteinVariant', 'ProteinFusion'):
                result.modification = True
                result.modifications = self.get_or_create_modification(graph, node_data)

            self.session.add(result)
            self.session.flush()

        return result

    def get_or_create_modification(self, graph, node_data):
        """Creates a list of modification object (models.Modification) that belong to the node described by
        node_data.

        :param graph: a BEL network
        :type graph: :class:`pybel.BELGraph`
        :param node_data: Describes the given node and contains modification information
        :type node_data: dict
        :return:
        :rtype: list
        """
        modification_list = []
        if node_data['type'] == 'ProteinFusion':
            modType = 'ProteinFusion'
            p3namespace_url = graph.namespace_url[node_data[PARTNER_3P][NAMESPACE]]
            p3name_id = self.cache_manager.namespace_id_cache[p3namespace_url][node_data[PARTNER_3P][NAME]]
            p3namespaceEntry = self.get_name(p3name_id)

            p5namespace_url = graph.namespace_url[node_data[PARTNER_5P][NAMESPACE]]
            p5name_id = self.cache_manager.namespace_id_cache[p5namespace_url][node_data[PARTNER_5P][NAME]]
            p5namespaceEntry = self.get_name(p5name_id)

            modification_list.append({
                'modType': modType,
                'p3Partner': p3namespaceEntry,
                'p3Range': node_data[RANGE_3P][0],
                'p5Partner': p5namespaceEntry,
                'p5Range': node_data[RANGE_5P][0],
            })
        else:
            for variant in node_data[VARIANTS]:
                modType = variant[0]
                if modType == 'Variant':
                    modification_list.append({
                        'modType': modType,
                        'variantString': variant[1]
                    })
                elif modType == 'ProteinModification':
                    modification_list.append({
                        'modType': modType,
                        'pmodName': variant[1] if len(variant) > 1 else None,
                        'aminoA': variant[2] if len(variant) > 2 else None,
                        'position': variant[3] if len(variant) > 3 else None
                    })
                elif modType == 'GeneModification':
                    # ToDo: Do GeneModifications look like ProteinModifications?
                    modification_list.append({
                        'modType': modType,
                        'variantString': str(variant[1])
                    })

                    # ToDo: What are the possible modifications?

        modifications = []
        for modification in modification_list:
            mod = self.session.query(models.Modification).filter_by(**modification).first()
            if not mod:
                mod = models.Modification(**modification)
            modifications.append(mod)

        return modifications

    def get_or_create_citation(self, type, name, reference, date=None, authors=None, comments=None):
        """Creates entry for given citation if it does not exist.

        :param type: Citation type (e.g. PubMed)
        :type type: str
        :param name: Title of the publication that is cited
        :type name: str
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :type reference: str
        :param date: Date of publication
        :type date: date
        :param authors: List of authors separated by |
        :type authors: str
        :param comments: Comments on the citation
        :type comments: str
        :return:
        :rtype: models.Citation
        """

        try:
            result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one()
        except NoResultFound:
            result = models.Citation(type=type, name=name, reference=reference)
            self.session.add(result)
            self.session.flush()
        return result

    def get_or_create_evidence(self, citation, evidence):
        """Creates entry for given evidence if it does not exist.

        :param citation: Citation object obtained from get_or_create_citation()
        :type citation: models.Citation
        :param evidence: Evidence text
        :type evidence: str
        :return:
        :rtype: models.Evidence
        """
        try:
            result = self.session.query(models.Evidence).filter_by(text=evidence).one()
        except NoResultFound:
            result = models.Evidence(text=evidence, citation=citation)
            self.session.add(result)
            self.session.flush()
        return result

    def get_or_create_property(self, graph, edge_data):
        """Creates a list of all subject and object related properties of the edge.

        :param graph: A BEL network
        :type graph: :class:`pybel.BELGraph`
        :param edge_data: Describes the context of the given edge.
        :type edge_data: dict
        :return:
        :rtype: list
        """
        properties = []
        property_list = []
        for participant in (SUBJECT, OBJECT):
            if participant in edge_data:
                participant_data = edge_data[participant]
                modifier = participant_data[MODIFIER]
                property_dict = {
                    'participant': participant,
                    'modifier': modifier
                }

                if modifier in (ACTIVITY, TRANSLOCATION):
                    for effect_type, effect_value in participant_data[EFFECT].items():
                        property_dict['relativeKey'] = effect_type
                        if NAMESPACE in effect_value:
                            namespace_url = graph.namespace_url[effect_value[NAMESPACE]]
                            namespaceEntry_id = self.cache_manager.namespace_id_cache[namespace_url][
                                effect_value[NAME]]
                            property_dict['namespaceEntry'] = self.get_name(namespaceEntry_id)
                        else:
                            property_dict['propValue'] = effect_value

                        property_list.append(property_dict)

                else:
                    property_list.append(property_dict)

        for property_def in property_list:
            property = self.session.query(models.Property).filter_by(**property_def).first()
            if not property:
                property = models.Property(**property_def)
            properties.append(property)
            # properties = [models.Property(**property_def) for property_def in property_list]

        return properties

    def get_annotation(self, anno_id):
        """

        :param anno_key:
        :return:
        :rtype: models.AnnotationEntry
        """
        return self.session.query(models.AnnotationEntry).filter_by(id=anno_id).one()

    def get_name(self, name_id):
        return self.session.query(models.NamespaceEntry).filter_by(id=name_id).one()

    def get_by_edge_filter(self, annotation_dict):
        """Gets all edges matching the given query annotation values

        :param annotation_dict: annotation/value pairs to filter edges
        :type annotation_dict: dict
        :return: A graph composed of the filtered edges
        :rtype: BELGraph
        """
        from pybel import BELGraph
        belGraph = BELGraph()
        for annotation_key, annotation_value in annotation_dict.items():
            annotation_def = self.session.query(models.Annotation).filter_by(keyword=annotation_key).first()
            annotation = self.session.query(models.AnnotationEntry).filter_by(annotation=annotation_def,
                                                                              name=annotation_value).first()
            # Add Annotations to belGraph.annotation_url
            # Add Namespaces to belGraph.namespace_url
            # What about meta information?
            edges = self.session.query(models.Edge).filter(models.Edge.annotations.contains(annotation)).all()
            for edge in edges:
                edge_data = edge.forGraph()

                if len(edge_data['source']['key']) == 1:
                    edge_data['source'] = self.help_get_list_components(edge.source)

                elif len(edge_data['target']['key']) == 1:
                    edge_data['target'] = self.help_get_list_components(edge.target)

                belGraph.add_nodes_from((edge_data['source']['node'], edge_data['target']['node']))
                belGraph.add_edge(edge_data['source']['key'], edge_data['target']['key'], edge_data['key'],
                                  edge_data['data'])

        return belGraph

    def help_get_list_components(self, node_object):
        """Builds data and identifier for list node objects.

        :param node_object: Node object defined in models.

        :return: Dictionary with 'key' and 'node' keys.
        """
        node_info = node_object.forGraph()
        key = list(node_info['key'])
        data = node_info['data']
        if node_object.type in ('Complex', 'Composite', 'List'):
            components = self.session.query(models.Edge).filter_by(source=node_object, relation=HAS_COMPONENT).all()
            for component in components:
                component_key = component.target.forGraph()['key']
                key.append(component_key)

        elif node_object.type == REACTION:
            reactant_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                            relation=HAS_REACTANT).all()
            product_components = self.session.query(models.Edge).filter_by(source=node_object,
                                                                           relation=HAS_PRODUCT).all()
            reactant_keys = tuple([reactant.target.forGraph()['key'] for reactant in reactant_components])
            product_keys = tuple([product.target.forGraph()['key'] for product in product_components])
            key.append(reactant_keys)
            key.append(product_keys)

        return {'key': tuple(key), 'node': (tuple(key), data)}


def to_database(graph, connection=None):
    """Stores a graph in a database

    :param graph: a BEL graph
    :type graph: BELGraph
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL
    :type connection: str
    """
    if isinstance(connection, GraphCacheManager):
        connection.store_graph(graph)
    else:
        GraphCacheManager(connection).store_graph(graph)


def from_database(name, version=None, connection=None):
    """Loads a BEL graph from a database


    :param name: The name of the graph
    :type name: str
    :param version: The version string of the graph. If not specified, loads most recent graph added with this name
    :type version: str
    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL.
    :type connection: str
    :return: a BEL graph loaded from the database
    :rtype: BELGraph
    """
    return GraphCacheManager(connection).get_graph(name, version)

#    def get_edge_iter_by_filter(self, **annotations):
#        """Returns an iterator over models.Edge object that match the given annotations

#        :param annotations: dictionary of {URL: values}
#        :type annotations: dict
#        :return: An iterator over models.Edge object that match the given annotations
#        :rtype: iter of models.Edge
#        """

        # TODO make smarter
#        for edge in self.session.query(models.Edge).all():
#            ad = {a.annotation.name: a.name for a in edge.annotations}
#            if subdict_matches(ad, annotations):
#                yield edge

#    def get_graph_by_filter(self, **annotations):
#        """Fills a BEL graph with edges retrieved from a filter
#
#        :param annotations: dictionary of {URL: values}
#        :type annotations: dict
#        :return: A BEL Graph
#        :rtype: pybel.BELGraph
#        """
#        graph = BELGraph()

#        for edge in self.get_edge_iter_by_filter(**annotations):
#            if edge.source.id not in graph:
#                graph.add_node(edge.source.id, attr_dict=pickle.loads(edge.source.blob))

#            if edge.target.id not in graph:
#                graph.add_node(edge.target.id, attr_dict=pickle.loads(edge.target.blob))

 #           graph.add_edge(edge.source.id, edge.target.id, attr_dict=pickle.loads(edge.blob))

#        return graph
