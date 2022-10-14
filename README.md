<!--
SPDX-FileCopyrightText: 2022 Robin Vobruba <hoijui.quaero@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

# IoPA OKH Project Porter

[![GitHub license](
    https://img.shields.io/github/license/hoijui/BundleBuilder.svg?style=flat)](
    ./LICENSE)
[![REUSE status](
    https://api.reuse.software/badge/github.com/iop-alliance/okh-project-porter)](
    https://api.reuse.software/info/github.com/iop-alliance/okh-project-porter)

This is a project that provides tooling that takes an OKH-LOSH RDF manifest as input,
and generates a bundle from it, which includes a copy of the original manifest file and 
all of the files that the manifest describes.

There are two version of the tooling: a graphical user interface (GUI) and a commang line interface version.

## GUI Tool

There is a version of the tool that allows the user to extract a project's file from a manifest using a GUI. 

This is avialable for the following platforms:

* Windows: [download](dist/OKH%20Project%20Porter.exe)
* MacOS: [download](dist/MacOS%20Installer/OKH%20Project%20Porter.dmg)
* Linux: [download](dist/okh-project-porter)

The Windows and MacOS version haven't been digitally signed yet so you will need to override the default OS behaviour to allow the files to run.

## Command Line Tool

The command line tool can extract the project's files either as a folder on the file system or a zip file, each respectively containing the manifest file and all the files linked to by it.

### Usage

Either with a local manifest-file:

```shell
wget https://gitlab.opensourceecology.de/verein/projekte/losh-rdf/-/raw/main/RDF/wikifactory.com/@rwbowman/openflexure-microscope/project.ttl
python3 src/man2bndl.py project.ttl bundle/
```

or with a URL

```shell
python3 src/man2bndl.py \
    https://gitlab.opensourceecology.de/verein/projekte/losh-rdf/-/raw/main/RDF/wikifactory.com/@rwbowman/openflexure-microscope/project.ttl \
    bundle/
```

Though, the output can not only be a folder like in the above examples,
but also a ZIP file;
the `.zip` suffix is required in this case:

```shell
python3 src/man2bndl.py project.ttl bundle.zip
```
