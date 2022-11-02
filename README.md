<!--
SPDX-FileCopyrightText: 2022 Robin Vobruba <hoijui.quaero@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

<div style="text-align: center;">

![OKH Project Porter logo](okh-project-porter-logo.png "OKH Project Porter")

# IoPA OKH Project Porter

</div>


This is a project that provides tooling that takes an OKH-LOSH RDF manifest as input,
and generates a bundle from it, which includes a copy of the original manifest file and 
all of the files that the manifest describes.

There are two version of the tooling: a graphical user interface (GUI) and a command line interface version.

## GUI Tool

There is a version of the tool that allows the user to extract a project's file from a manifest using a GUI. 

This is available for the following platforms:

* Windows: [download](dist/OKH%20Project%20Porter.exe)
* MacOS: [download](dist/MacOS%20Installer/OKH%20Project%20Porter.dmg)
* Linux: [download](dist/okh-project-porter)

The Windows and MacOS version haven't been digitally signed yet so you will need to override the default OS behaviour to allow the files to run.

* For Windows install override, see [change app recommendation settings in Windows](https://support.microsoft.com/en-us/windows/change-your-app-recommendation-settings-in-windows-f21b5c60-e996-4ee4-c2cf-b4a90c0bef9b) to allow for "OKH Project Porter" install.
* For macOS intall override, navigate to macOS [General Security & Privacy Settings](https://support.apple.com/guide/mac-help/change-security-privacy-general-preferences-mh11784/mac) to allow for "OKH Project Porter" install.

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
