#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 Robin Vobruba <hoijui.quaero@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

'''
Converts an OKH LOSH RDF /Turtle manifest into an IoPA OKH LOSH Bundle,
which is either a directory or a zip file,
each respectively containing the manifest file itsself,
and all the files it links to.
'''

import os
import re
import rdflib
from rdflib.namespace import DC, DCTERMS, DOAP, FOAF, SKOS, OWL, RDF, RDFS, VOID, XMLNS, XSD
import click
import logging
import tempfile
import shutil
import hashlib
import requests
from urllib.parse import urlparse

OKH = rdflib.Namespace('https://github.com/OPEN-NEXT/OKH-LOSH/raw/master/OKH-LOSH.ttl#')
# OBO = rdflib.Namespace('http://purl.obolibrary.org/obo/')
# SCHEMA = rdflib.Namespace('http://schema.org/')
# SPDX = rdflib.Namespace('http://spdx.org/rdf/terms#')
# EPO = rdflib.Namespace('http://data.epo.org/linked-data/def/patent/')
# NPG = rdflib.Namespace('http://ns.nature.com/terms/')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def version_token():
    '''
    Stub to set context settings and version info.
    '''
    #pass

debug_enabled = False

def enable_debug():
    '''
    Enabling debugging at http.client level (requests->urllib3->http.client)
    you will see the REQUEST, including HEADERS and DATA,
    and RESPONSE with HEADERS but without DATA.
    the only thing missing will be the response.body which is not logged.
    '''
    global debug_enabled
    # HTTPConnection.debuglevel = 1

    # you need to initialize logging,
    # otherwise you will not see anything from requests
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    debug_enabled = True

def is_debug():
    '''
    Returns True if debugging is enabled, False otherwise.
    '''
    global debug_enabled
    return debug_enabled

def get_filepath_from_url(url):
    """Get a file-path from a URL.

    >>> from planet.api import utils
    >>> urls = [
    ...     'https://planet.com/',
    ...     'https://planet.com/path/to/',
    ...     'https://planet.com/path/to/example.tif',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux'
    ... ]
    >>> for url in urls:
    ...     print('{} -> {}'.format(url, utils.get_filename_from_url(url)))
    ...
    https://planet.com/ -> None
    https://planet.com/path/to/ -> path/to/
    https://planet.com/path/to/example.tif -> path/to/example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz -> path/to/example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux -> path/to/example.tif
    >>>

    :returns: a file-path
    :rtype: str or None
    """
    path = re.sub('^/', '', urlparse(url).path)
    return path or None

def get_filename_from_url(url):
    """Get a filename from a URL.

    >>> from planet.api import utils
    >>> urls = [
    ...     'https://planet.com/',
    ...     'https://planet.com/path/to/',
    ...     'https://planet.com/path/to/example.tif',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux'
    ... ]
    >>> for url in urls:
    ...     print('{} -> {}'.format(url, utils.get_filename_from_url(url)))
    ...
    https://planet.com/ -> None
    https://planet.com/path/to/ -> None
    https://planet.com/path/to/example.tif -> example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz -> example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux -> example.tif
    >>>

    :returns: a filename (i.e. ``basename``)
    :rtype: str or None
    """
    path = get_filepath_from_url(url)
    name = path[path.rfind('/')+1:]
    return name or None

def url_to_path(url):
    return url.replace('https://', '').replace('/', '_')

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def download(url, file):
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(file, 'wb').write(r.content)
    else:
        raise RuntimeError(f'URL not reachable: "{url}"')

def create_link(src, dst):
    # create all parent/ancestor dirs, if necessary
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # make path relative
    rel_path_src = os.path.relpath(src, os.path.dirname(dst))
    # create the link
    os.symlink(rel_path_src, dst)

class BundleCreator:

    def __init__(self, manifest, output, is_zip, dry):
        self.manifest = manifest
        self.graph = rdflib.Graph()
        self.graph.parse(manifest, format='turtle')
        self.output = output
        self.is_zip = is_zip
        self.dry = dry

    def download_files(self, output_dir):

        files_dir = os.path.join(output_dir, 'files')
        os.mkdir(files_dir)

        url_files_dir = os.path.join(files_dir, 'url')
        os.mkdir(url_files_dir)

        hashed_files_dir = os.path.join(files_dir, 'hashed')
        os.mkdir(hashed_files_dir)

        subj_files_dir = os.path.join(files_dir, 'subjects')
        os.mkdir(subj_files_dir)

        subj_name_files_dir = os.path.join(files_dir, 'subject_names')
        os.mkdir(subj_name_files_dir)

        named_files_dir = os.path.join(files_dir, 'name')
        os.mkdir(named_files_dir)

        path_files_dir = os.path.join(files_dir, 'path')
        os.mkdir(path_files_dir)

        flat_path_files_dir = os.path.join(files_dir, 'flat_path')
        os.mkdir(flat_path_files_dir)

        labeled_files_dir = os.path.join(files_dir, 'label')
        os.mkdir(labeled_files_dir)

        file_index = 0
        for s, p, perma_url in self.graph.triples((None, OKH.permaURL, None)):
            url_hash = hashlib.sha1(perma_url.encode()).hexdigest()
            label = None
            for _, _, o in self.graph.triples((s, RDFS.label, None)):
                label = o
            subj_name = get_filename_from_url(s)
            file_name = get_filename_from_url(perma_url)
            file_path = get_filepath_from_url(perma_url)
            file_path_flat = file_path.replace('/', '_')
            print(f"Downloading file {file_index}:")
            print(f"\tsubject name: '{subj_name}'")
            print(f"\thash:           {url_hash}")
            print(f"\tfile name:      '{file_name}'")
            print(f"\tfile path:      '{file_path}'")
            print(f"\tfile path flat: '{file_path_flat}'")
            print(f"\tlabel:          '{label}'")
            print(f"\tsubject:        '{s}'")
            print(f"\tokh:permaURL:   '{perma_url}'")
            print(f"\t...")
            
            hashed_file = os.path.join(hashed_files_dir, url_hash)
            url_file = os.path.join(url_files_dir, url_to_path(perma_url))
            labeled_file = os.path.join(labeled_files_dir, label)
            subj_file = os.path.join(subj_files_dir, url_to_path(s))
            subj_name_file = os.path.join(subj_name_files_dir, subj_name)
            named_file = os.path.join(named_files_dir, file_name)
            path_file = os.path.join(path_files_dir, file_path)
            path_flat_file = os.path.join(flat_path_files_dir, file_path_flat)

            if self.dry:
                touch(hashed_file)
            else:
                download(perma_url, hashed_file)

            create_link(hashed_file, url_file)
            create_link(hashed_file, subj_file)
            create_link(hashed_file, subj_name_file)
            create_link(hashed_file, named_file)
            create_link(hashed_file, path_file)
            create_link(hashed_file, path_flat_file)
            create_link(hashed_file, labeled_file)

            file_index = file_index + 1

    def copy_manifest(self, dst_dir):
        dst = os.path.join(dst_dir, 'okh.ttl')
        shutil.copyfile(self.manifest, dst)

    def create_bundle(self, b_dir):
        self.download_files(b_dir)
        self.copy_manifest(b_dir)

    def create(self):
        if self.is_zip:
            with tempfile.TemporaryDirectory(suffix='_zip_content', prefix='man2bndl_', ignore_cleanup_errors=True) as temp_dir:
                self.create_bundle(temp_dir)
                zip_file_base = re.sub('\.zip$', '', self.output)
                shutil.make_archive(zip_file_base, 'zip', temp_dir)
        else:
            os.mkdir(self.output)
            self.create_bundle(self.output)

        print('done.')

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('manifest', envvar='MANIFEST')#, help='Path to the OKH LOSH RDF/Turtle manifest file (input), e.g. "project.ttl"')
@click.argument('output', envvar='OUTPUT', type=click.Path(exists=False))#, help='Path to the output dir or ZIP file, eg. "bundle/" or "bundle.zip". This dir/file may not yet exist!')
@click.option('-d', '--dry', default=False, is_flag=True)
@click.option('-d', '--debug', default=False, is_flag=True)
@click.version_option("0.1.0")
def cli(manifest, output, dry, debug):

    is_zip = output.endswith(".zip")

    # Run as a CLI script
    if debug:
        enable_debug()

    if not os.path.exists(manifest):
        okh_ttl_tmp = tempfile.NamedTemporaryFile(prefix='okh', suffix='.ttl')
        okh_ttl_tmp_name = okh_ttl_tmp.name
        okh_ttl_tmp.close()
        print(f'Not an existing, local (mainifest) file: "{manifest}"; interpreting it as a URL ...')
        download(manifest, okh_ttl_tmp_name)
        manifest = okh_ttl_tmp_name

    creator = BundleCreator(manifest, output, is_zip, dry)
    creator.create()

if __name__ == "__main__":
    cli()
