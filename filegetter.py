import os
import re
import rdflib
from rdflib.namespace import DC, DCTERMS, DOAP, FOAF, SKOS, OWL, RDF, RDFS, VOID, XMLNS, XSD
import logging
import tempfile
import shutil
import hashlib
import requests
from urllib.parse import urlparse

OKH = rdflib.Namespace('https://github.com/OPEN-NEXT/OKH-LOSH/raw/master/OKH-LOSH.ttl#')

debug_enabled = False

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

def is_debug():
    '''
    Returns True if debugging is enabled, False otherwise.
    '''
    global debug_enabled
    return debug_enabled

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

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
        hashed_files_dir = os.path.join(files_dir, 'hashed')
        subj_files_dir = os.path.join(files_dir, 'subjects')
        subj_name_files_dir = os.path.join(files_dir, 'subject_names')
        named_files_dir = os.path.join(files_dir, 'name')
        path_files_dir = os.path.join(files_dir, 'path')
        flat_path_files_dir = os.path.join(files_dir, 'flat_path')
        labeled_files_dir = os.path.join(files_dir, 'label')

        if is_debug():
            os.mkdir(url_files_dir)
            os.mkdir(hashed_files_dir)
            os.mkdir(subj_files_dir)
            os.mkdir(subj_name_files_dir)
            os.mkdir(named_files_dir)
            os.mkdir(path_files_dir)
            os.mkdir(flat_path_files_dir)
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
            if is_debug():
                print(f"\tsubject name: '{subj_name}'")
                print(f"\thash:           {url_hash}")
                print(f"\tfile name:      '{file_name}'")
                print(f"\tfile path:      '{file_path}'")
                print(f"\tfile path flat: '{file_path_flat}'")
                print(f"\tlabel:          '{label}'")
                print(f"\tsubject:        '{s}'")
            print(f"\tokh:permaURL:   '{perma_url}'")
            print(f"\t...")
            
            main_file = os.path.join(files_dir, url_to_path(perma_url))

            if self.dry:
                touch(main_file)
            else:
                download(perma_url, main_file)

            file_index = file_index + 1

    def copy_manifest(self, dst_dir):
        dst = os.path.join(dst_dir, 'okh.ttl')
        shutil.copyfile(self.manifest, dst)

    def create_bundle(self, b_dir):
        self.download_files(b_dir)
        self.copy_manifest(b_dir)

    def create(self):
        if self.is_zip:
            with tempfile.TemporaryDirectory(suffix='_zip_content', prefix='man2bndl_') as temp_dir:
                self.create_bundle(temp_dir)
                zip_file_base = re.sub('\.zip$', '', self.output)
                shutil.make_archive(zip_file_base, 'zip', temp_dir)
        else:
            self.create_bundle(self.output)

        print('done.')


def download(url, file):
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(file, 'wb').write(r.content)
    else:
        raise RuntimeError(f'URL not reachable: "{url}"')

def get_files_from_url(manifest_url, files_path):
    okh_ttl_tmp = tempfile.NamedTemporaryFile(prefix='okh', suffix='.ttl')
    okh_ttl_tmp_name = okh_ttl_tmp.name
    okh_ttl_tmp.close()
    download(manifest_url, okh_ttl_tmp_name)
    manifest = okh_ttl_tmp_name

    creator = BundleCreator(manifest, files_path, False, False)
    creator.create()

def get_files_from_file(manifest, files_path):
    creator = BundleCreator(manifest, files_path, False, False)
    creator.create()
