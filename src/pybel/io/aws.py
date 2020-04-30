# -*- coding: utf-8 -*-

"""Transport functions for Amazon Web Services (AWS).

AWS has a cloud-based file storage service called S3 that can be programatically
accessed using the :mod:`boto3` package. This module provides functions for quickly
wrapping upload/download of BEL graphs using the gzipped Node-Link schema.
"""

import logging
from io import BytesIO
from typing import Any, Optional

from .nodelink import from_nodelink_gz_io, to_nodelink_gz_io
from ..struct import BELGraph

__all__ = [
    'to_s3',
    'from_s3',
]

logger = logging.getLogger(__name__)
S3Client = Any


def to_s3(graph: BELGraph, *, bucket: str, key: str, client: Optional[S3Client] = None) -> None:
    """Save BEL to S3 as gzipped node-link JSON.

    If you don't specify an instantiated client, PyBEL will do its best to load a default
    one using :func:`boto3.client` like in the following example:

    .. code-block:: python

        import pybel
        from pybel.examples import sialic_acid_graph

        graph = pybel.to_s3(
            sialic_acid_graph,
            bucket='your bucket',
            key='your file name.bel.nodelink.json.gz',
        )

    However, if you would like to configure your own, you can do it with something like this:

    .. code-block:: python

        import boto3
        s3_client = boto3.client('s3')

        import pybel
        from pybel.examples import sialic_acid_graph

        graph = pybel.to_s3(
            sialic_acid_graph,
            client=s3_client,
            bucket='your bucket',
            key='your file name.bel.nodelink.json.gz',
        )

    .. warning:: This assumes you already have credentials set up on your machine

    If you don't already have a bucket, you can create one using ``boto3`` by following
    this tutorial: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-creating-buckets.html
    """
    if client is None:
        import boto3
        client = boto3.client('s3')
    io = to_nodelink_gz_io(graph)
    client.upload_fileobj(io, bucket, key)


def from_s3(*, bucket: str, key: str, client: Optional[S3Client] = None) -> BELGraph:
    """Get BEL from gzipped node-link JSON from Amazon S3.

    If you don't specify an instantiated client, PyBEL will do its best to load a default
    one using :func:`boto3.client` like in the following example:

    .. code-block:: python

        graph = pybel.from_s3(bucket='your bucket', key='your file name.bel.nodelink.json.gz')

    However, if you would like to configure your own, you can do it with something like this:

    .. code-block:: python

        import boto3
        s3_client = boto3.client('s3')

        import pybel
        graph = pybel.from_s3(
            client=s3_client,
            bucket='your bucket',
            key='your file name.bel.nodelink.json.gz',
        )
    """
    if client is None:
        import boto3
        client = boto3.client('s3')
    io = BytesIO()
    client.download_fileobj(bucket, key, io)
    io.seek(0)
    return from_nodelink_gz_io(io)
