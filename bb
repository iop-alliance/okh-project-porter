#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2022 Robin Vobruba <hoijui.quaero@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# See the output of "$0 -h" for more details.

# Exit immediately on each error and unset variable;
# see: https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/
set -Eeuo pipefail
#set -Eeu

#script_dir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# initial default values
APP_NAME="Bundle Builder"
script_name="$(basename "$0")"
fetch=true

function print_help() {

	echo "$APP_NAME - Builds IoPA(-OKH) bundles from OKH(-LOSH) RDF manifests."
	echo "Such a bundle is either a folder on the file-system or a ZIP file,"
	echo "each respectively containing the manifest file and all the files linked to by it."
	echo
	echo "Usage:"
	echo "  $script_name [OPTION...] <path-to-turtle-manifest> <output-dir|output-zip-file>"
	echo "Options:"
	echo "  -h, --help              Show this help message"
	echo "  -n, --no-fetch          Do not fetch the remotes"
	echo "Examples:"
	echo "  $script_name 'project.ttl' 'bundle-dir/'"
	echo "  $script_name 'project.ttl' 'bundle.zip'"
}

function path2abs() {
	echo "$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"
}

# read command-line args
POSITIONAL=()
while [[ $# -gt 0 ]]
do
	arg="$1"
	shift # $2 -> $1, $3 -> $2, ...

	case "$arg" in
		-h|--help)
			print_help
			exit 0
			;;
		-n|--no-fetch)
			fetch=false
			;;
		*) # non-/unknown option
			POSITIONAL+=("$arg") # save it in an array for later
			;;
	esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

manifest="${1:-}"
output="${2:-}"

if [ -z "$manifest" ]
then
	>&2 echo "WARNING: No manifest file provided!"
	print_help
	exit 1
fi

if [ -z "$output" ]
then
	>&2 echo "WARNING: No output dir/zip-file provided!"
	print_help
	exit 1
fi

rgx_zip=".*\.[zZ][iI][pP]$"
output_is_dir=$(if [[ "$output" =~ $rgx_zip ]]; then echo false; else echo true; fi)
output_type=$(if $output_is_dir; then echo "dir"; else echo "ZIP-file"; fi)
output_dir=$(if $output_is_dir; then echo "$output"; else echo "/tmp/${script_name}_$RANDOM"; fi)

if [ -e "$output" ]
then
	>&2 echo "WARNING: Output destination already exists!"
	exit 2
fi

echo "Constructing bundle $output_type from manifest '$manifest' at '$output'."
echo "Downloading files ..."
echo "(you have 3s to abort with [Ctrl-C])"
sleep 0 # FIXME Set to 3

mkdir -p "$output_dir/files"

for url in $(grep "okh:permaURL" | sed -e "s|.*okh:permaURL[ ]\+<||" -e "s|>[ ]*[.;]*$||")
do
	hash=$(echo "$url" | sha1sum | sed -e 's|[ ]*-$||')
	out_file="$output_dir/files/$hash"
	if $fetch
	then
		echo "Downloading '$url' ..."
		wget --quiet -O "$out_file" "$url"
	else
		echo "FAKE Downloading '$url' ..."
		touch "$out_file"
	fi
done < "$manifest"

cp "$manifest" "$output_dir"

if ! $output_is_dir
then
	cur_dir="$(pwd)"
	abs_output="$(path2abs "$output")"
	cd "$output_dir"
	zip -r "$abs_output" .
	cd "$cur_dir"
fi
