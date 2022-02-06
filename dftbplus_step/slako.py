#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility program to scan the Slater-Koster potential files and
extract the metadata from them.
"""

import hashlib
import json  # noqa: F401
import logging
from pathlib import Path

import xmltodict

logger = logging.getLogger(__name__)


def parse_file(filename):
    with open(filename, "r") as fd:
        lines = fd.readlines()

    data = []
    xml = []
    in_xml = False
    for line in lines:
        if in_xml:
            xml.append(line)
        elif line[0] == "<":
            in_xml = True
            xml.append(line)
        else:
            data.append(line)
    metadata = dict(**xmltodict.parse("\n".join(xml)))

    data = "".join(data)
    m = hashlib.md5(data.encode())
    md5sum = m.hexdigest()

    return md5sum, metadata


def test_one(filename="data/slako/3ob/3ob-3-1/Br-Br.skf"):
    md5sum, metadata = parse_file(filename)

    # print(f'md5sum = {md5sum}')
    # print(json.dumps(metadata, indent=4))

    general = metadata["Documentation"]["General"]
    if general["Md5sum"] != md5sum:
        print("md5 checksums differ!")

    compatibility = general["Compatibility"]
    partners = compatibility["Partner"]
    for partner in partners:
        print(f"{partner['@Identifier']:>9} {partner['Md5sum']}")

    SK_table = metadata["Documentation"]["SK_table"]
    print(f"Shells = {SK_table['Basis']['Shells']}")


def analyze_directory(root="data/slako"):
    """Find all the Slater-Koster files under a given directory
    and analyze their metadata.
    """
    if not isinstance(root, Path):
        root = Path(root)
    root = root.expanduser().resolve()
    print(f"Analyzing directory {root}")

    comments = []
    metadata = {
        "bad_md5s": {},
        "same": {},
        "parameterizations": [],
        "potentials": {},
    }
    bad = metadata["bad_md5s"]
    same = metadata["same"]
    parameterizations = metadata["parameterizations"]
    all_potentials = metadata["potentials"]

    sk_files = root.glob("**/*.skf")
    for path in sk_files:
        # Assume the parent directory is the parameterization + version
        # and grandparent is the parameterization.
        parent = path.parent
        # Handle the ob2 files...
        if parent.name == "split" or parent.name == "shift":
            continue
        if parent.name == "base":
            parent = parent.parent
        grandparent = parent.parent
        parameterization = grandparent.name
        logger.debug(f"{path}: {parameterization}")
        version = ".".join(parent.name.split("-")[1:])
        if parameterization not in parameterizations:
            parameterizations.append(parameterization)

        md5sum, data = parse_file(path)

        data = data["Documentation"]
        general = data["General"]

        data["parameterization"] = parameterization
        data["version"] = version
        data["filename"] = str(path)

        if md5sum in all_potentials:
            if "filename" not in all_potentials[md5sum]:
                comments.append(
                    f"{path} metadata already exists for {md5sum} "
                    "but there is no filename !?!"
                )
            else:
                same[str(path)] = md5sum
        else:
            all_potentials[md5sum] = data

        if general["Md5sum"] != md5sum:
            md5 = general["Md5sum"]

            data["md5 mismatch"] = True
            bad[md5] = md5sum
            comments.append(f"{path} md5 checksums differ! {md5} {md5sum}")
        else:
            data["md5 mismatch"] = False

        if parameterization not in metadata:
            logger.info(f"   adding {parameterization}")
            pdata = metadata[parameterization] = {}
        else:
            pdata = metadata[parameterization]
        if version not in pdata:
            vdata = pdata[version] = {"potentials": {}, "sets": []}
        else:
            vdata = pdata[version]
        potentials = vdata["potentials"]
        el1 = general["Element1"]
        if "Element2" in general:
            el2 = general["Element2"]
        else:
            el2 = el1
        # Check the file name
        if "-" in path.stem:
            try:
                tmp1, tmp2 = path.stem.split("_")[0].split("-")
                if tmp1 != el1 or tmp2 != el2:
                    comments.append(f"Element error in {path}: should be {el1}-{el2}")
                data["elements"] = [tmp1, tmp2]
            except Exception:
                print(f"Odd filename: {path} -- elements {el1}-{el2}")
                comments.append(f"Odd filename: {path} -- elements {el1}-{el2}")
            # Believe the filename
            potentials[path.stem] = md5sum
        else:
            if path.stem != el1 + el2:
                print(f"Odd filename: {path} -- elements {el1}-{el2}")
                comments.append(f"Odd filename: {path} -- elements {el1}-{el2}")
            # Believe the elements
            potentials[f"{el1}-{el2}"] = md5sum
            data["elements"] = [el1, el2]

    # The files that have the same potential
    if len(same) > 0:
        comments.append("")
        comments.append("The following files have the same data:")
        for f1, md5sum in same.items():
            f2 = all_potentials[md5sum]["filename"]
            if Path(f1).parent == Path(f2).parent:
                # comments.append(f'    {f1} {Path(f2).name}')
                pass
            else:
                comments.append(f"    {md5sum} {f1} {f2}")

    # Check on the bad md5 sums from in the file
    comments.append("")
    for other, good in bad.items():
        good_file = Path(all_potentials[good]["filename"]).relative_to(root)
        if other in metadata:
            other_file = Path(all_potentials[other]["filename"]).relative_to(root)
            comments.append(f"file {good_file} has the MD5 sum from {other_file}")
        else:
            comments.append(
                f"file {good_file} has an MD5 sum internally that doesnt "
                "match anything"
            )

    return metadata, comments


def find_sets(metadata, parameterizations):
    """Find the sets of atoms with complete parameterizations
    from one or more parameterizations
    """
    # Find the pairs in all the parameterizations
    elements = []
    for parameterization in parameterizations:
        if parameterization in metadata:
            pdata = metadata[parameterization]
            version = [*pdata.keys()][0]
            vdata = pdata[version]
            potentials = vdata["potentials"]
            for stem in potentials.keys():
                el1, el2 = stem.split("-")
                if el1 not in elements:
                    elements.append(el1)
                if el2 not in elements:
                    elements.append(el2)

    elements.sort()
    pairs = {el: [] for el in elements}

    for parameterization in parameterizations:
        if parameterization in metadata:
            pdata = metadata[parameterization]
            version = [*pdata.keys()][0]
            vdata = pdata[version]
            potentials = vdata["potentials"]
            for stem in potentials.keys():
                el1, el2 = stem.split("-")
                if el2 not in pairs[el1]:
                    pairs[el1].append(el2)
                if el1 not in pairs[el2]:
                    pairs[el2].append(el1)

    # Build up sets element by element, starting with pairs
    sets = {}
    sets[2] = []
    for el1 in elements:
        for el2 in pairs[el1]:
            if el2 >= el1:
                continue
            sets[2].append({el2, el1})

    for n in range(3, len(elements) + 1):
        sets[n] = []
        nm1 = n - 1
        for nm1_set in sets[nm1]:
            for el2 in elements:
                if el2 in nm1_set:
                    continue
                add = True
                for el1 in nm1_set:
                    if el2 not in pairs[el1]:
                        add = False
                        break
                if add:
                    new_set = set(nm1_set)
                    new_set.add(el2)
                    found = False
                    for nset in sets[n]:
                        if new_set == nset:
                            found = True
                            break
                    if not found:
                        sets[n].append(new_set)

    # Now remove all sets that are subsets of larger ones
    result = []
    for n in range(3, len(elements) + 1):
        nm1 = n - 1
        for nm1_set in sets[nm1]:
            is_subset = False
            for n_set in sets[n]:
                if nm1_set < n_set:
                    is_subset = True
                    break
            if not is_subset:
                tmp = [*nm1_set]
                tmp.sort()
                result.append(tmp)

    # Add any sets with all the atoms ... they are not a subset!
    if len(elements) == 1:
        result.append(elements)
    else:
        for n_set in sets[len(elements)]:
            result.append(sorted([*n_set]))

    if "sets" not in metadata:
        metadata["sets"] = {}
    key = " -- ".join(sorted(parameterizations))
    metadata["sets"][key] = result
    return result


def partners2(metadata, parameterization):
    """Find the listed partners"""
    pdata = metadata[parameterization]
    all_potentials = metadata["potentials"]
    version = [*pdata.keys()][0]
    vdata = pdata[version]
    potentials = vdata["potentials"]

    for key, md5sum in potentials.items():
        print(f"\n{key}")
        data = all_potentials[md5sum]
        data["partners"] = []
        general = data["General"]
        if "Compatibility" not in general:
            print(f"{data['filename']} has no compatibility data")
            continue
        compatibility = general["Compatibility"]
        for partner in compatibility["Partner"]:
            md5 = partner["Md5sum"]
            if md5 in all_potentials:
                data["partners"].append(md5)
                tmp = all_potentials[md5]
                print(
                    f"     {tmp['parameterization']} {tmp['version']} "
                    f"{partner['@Identifier']}"
                )
            elif md5 in metadata["bad_md5s"]:
                good_md5 = metadata["bad_md5s"][md5]
                data["partners"].append(good_md5)
                tmp = all_potentials[good_md5]
                print(
                    f"     {tmp['parameterization']} {tmp['version']} "
                    f"{partner['@Identifier']}"
                )
            else:
                el1 = partner["Element1"]
                if "Element2" in partner:
                    el2 = partner["Element2"]
                else:
                    el2 = el1
                if f"{el1}-{el2}" in potentials:
                    correct_md5 = potentials[f"{el1}-{el2}"]
                    data["partners"].append(correct_md5)
                    print(
                        f"    {el1}-{el2} {data['filename']} "
                        f"{partner['@Identifier']} "
                        f"{partner['Md5sum']} {correct_md5} "
                        f"{all_potentials[correct_md5]['elements']}"
                    )
                else:
                    correct_md5 = "unknown"
                    print(
                        f"    {el1}-{el2} {data['filename']} "
                        f"{partner['@Identifier']} "
                        f"{partner['Md5sum']} {correct_md5} "
                    )
                # pprint.pprint(partner)


def partners(metadata):
    """Find the listed partners"""
    all_potentials = metadata["potentials"]

    for md5sum, data in all_potentials.items():
        data = all_potentials[md5sum]
        general = data["General"]
        if "Compatibility" not in general:
            print(f"{data['filename']} has no compatibility data")
            continue
        compatibility = general["Compatibility"]
        partners = []
        for partner in compatibility["Partner"]:
            md5 = partner["Md5sum"]
            if md5 in all_potentials:
                partners.append(md5)
            elif md5 in metadata["bad_md5s"]:
                good_md5 = metadata["bad_md5s"][md5]
                partners.append(good_md5)
            else:
                parameterization = data["parameterization"]
                version = data["version"]
                el1 = partner["Element1"]
                el2 = partner["Element1"]
                potentials = metadata[parameterization][version]["potentials"]
                if f"{el1}-{el2}" in potentials:
                    correct_md5 = potentials[f"{el1}-{el2}"]
                else:
                    correct_md5 = "unknown"
                print(
                    f"    {data['filename']} {partner['@Identifier']} "
                    f"{partner['Md5sum']} {correct_md5} bad partner md5sum"
                )
                # pprint.pprint(partner)
        data["partners"] = partners


def list_partners(metadata, parameterization):
    """Find the listed partners"""
    pdata = metadata[parameterization]
    all_potentials = metadata["potentials"]
    version = [*pdata.keys()][0]
    vdata = pdata[version]
    potentials = vdata["potentials"]

    outside = {}
    inside = []
    for key, md5sum in potentials.items():
        data = all_potentials[md5sum]
        for partner in data["partners"]:
            p_param = all_potentials[partner]["parameterization"]
            if p_param != parameterization:
                if p_param not in outside:
                    outside[p_param] = []
                o_param = outside[p_param]
                if partner not in o_param:
                    o_param.append(partner)
            else:
                if partner not in inside:
                    inside.append(partner)
    return inside, outside


def create_datafile(directory="~/SEAMM/Parameters/slako"):
    """Parse the files and get the data needed for the metadata-file"""
    datasets = {
        "3ob": ["3ob-freq", "3ob-hhmod", "3ob-nhmod", "3ob-ophyd"],
        "matsci": ["magsil"],
        "mio": ["chalc", "hyb", "miomod-hh", "miomod-nh", "tiorg", "trans3d", "znorg"],
        "auorg": [],
        "borg": [],
        "halorg": [],
        "pbc": [],
        "siband": [],
        "rare": [],
    }
    # "ob2": [],

    if not isinstance(directory, Path):
        directory = Path(directory)
    directory = directory.expanduser().resolve()

    # The result dictionary
    result = {}

    # Read in all the potentials
    metadata, comments = analyze_directory(directory)
    print("\n".join(comments))
    print("")
    all_potentials = metadata["potentials"]

    # Make a list of the sets or elements covered by each combination
    result["datasets"] = {}
    for dataset, subsets in datasets.items():
        result["datasets"][dataset] = {
            "subsets": subsets,
            "parent": None,
        }
        for subset in subsets:
            result["datasets"][subset] = {
                "subsets": [],
                "parent": dataset,
            }

        # Create the element sets
        sets = find_sets(metadata, [dataset])
        result["datasets"][dataset]["element sets"] = sets
        for subset in subsets:
            sets = find_sets(metadata, [dataset, subset])
            result["datasets"][subset]["element sets"] = sets

    # Transfer desired information about each of the potentials
    result["potentials"] = {}
    result["pairs"] = {}
    for md5sum, data in all_potentials.items():
        result["potentials"][md5sum] = {
            "filename": data["filename"],
            "elements": data["elements"],
            "datasets": [f"{data['parameterization']}@{data['version']}"],
        }
        el1, el2 = data["elements"]
        key = f"{el1}-{el2}"
        if key not in result["pairs"]:
            result["pairs"][key] = [md5sum]
        else:
            result["pairs"][key].append(md5sum)

    # Get the maximum angular moment
    for dataset in result["datasets"]:
        pdata = metadata[dataset]
        version = [*pdata.keys()][0]
        vdata = pdata[version]
        potentials = vdata["potentials"]
        elements = {}

        pairs = result["datasets"][dataset]["potential pairs"] = {}
        for potential, md5sum in potentials.items():
            data = all_potentials[md5sum]
            el1, el2 = data["elements"]
            pairs[f"{el1}-{el2}"] = {"md5sum": md5sum}

            # Check that this dataset/version is in the list
            dv = f"{data['parameterization']}@{data['version']}"
            if dv not in result["potentials"][md5sum]["datasets"]:
                result["potentials"][md5sum]["datasets"].append(dv)

            shell_order = ("s", "p", "d", "f", "g", "h")
            if el1 == el2:
                sk_table = data["SK_table"]
                basis = sk_table["Basis"]
                shells = basis["Shells"]
                highest = -1
                for shell in shells.split():
                    highest = max(highest, shell_order.index(shell[1]))
                highest = shell_order[highest]
                if "HubbDerivative" in basis:
                    hder = basis["HubbDerivative"]
                    elements[el1] = {
                        "maximum angular momentum": highest,
                        "Hubbard derivative": hder,
                    }
                else:
                    elements[el1] = {"maximum angular momentum": highest}
        result["datasets"][dataset]["element data"] = elements

    # Print and save the results
    data = json.dumps(result, indent=4, sort_keys=True)
    # print(data)
    with open(directory / "metadata.json", "w") as fd:
        fd.write(data)


if __name__ == "__main__":
    # test_one('data/slako/3ob/3ob-3-1/Br-Br.skf')

    create_datafile()
    exit()

    # metadata, comments = analyze_directory('data/slako')
    # print('\n'.join(comments))
    # print('')

    # if False:
    #     for parameterization in metadata['parameterizations']:
    #         print('')
    #         print(parameterization)
    #         sets = find_sets(metadata, [parameterization])
    #         for group in sets:
    #             print(f'    {group}')

    # if False:
    #     partners(metadata)

    # if False:
    #     for parameterization in metadata['parameterizations']:
    #         print('')
    #         print(parameterization)
    #         partners2(metadata, parameterization)

    # if False:
    #     # Print the md5 sums for all potentials
    #     print('')
    #     print('Potentials')
    #     print('----------')
    #     for md5sum, data in metadata['potentials'].items():
    #         if 'elements' in data:
    #             el1, el2 = data['elements']
    #         else:
    #             el1 = 'xx'
    #             el2 = 'xx'
    #         print(f"{md5sum}  {el1}-{el2}  {data['filename']}")

    # if False:
    #     # List partners outside the current parameterization
    #     all_potentials = metadata['potentials']
    #     for parameterization in metadata['parameterizations']:
    #         pdata = metadata[parameterization]
    #         version = [*pdata.keys()][0]
    #         vdata = pdata[version]
    #         potentials = vdata['potentials']
    #         print('')
    #         print(parameterization)
    #         for group in vdata['sets']:
    #             print(f'    {group}')
    #         inside, outside = list_partners(metadata, parameterization)
    #         print('    inside:')
    #         for partner in inside:
    #             data = all_potentials[partner]
    #             print(f"        {data['filename']}")
    #         for param, partners in outside.items():
    #             print(f"    {param}:")
    #             for partner in partners:
    #                 data = all_potentials[partner]
    #                 print(f"        {data['filename']}")

    # if False:
    #     # Check if partners think we are a partner
    #     potentials = metadata['potentials']
    #     missing_partners = {}
    #     for md5sum, data in potentials.items():
    #         first = True
    #         for partner in data['partners']:
    #             pdata = potentials[partner]
    #             if md5sum not in pdata['partners']:
    #                 if partner not in missing_partners:
    #                     missing_partners[partner] = []
    #                 if md5sum not in missing_partners[partner]:
    #                     missing_partners[partner].append(md5sum)

    #     for md5sum, missing in missing_partners.items():
    #         print(potentials[md5sum]['filename'])
    #         for missed in missing:
    #             print(f"    {potentials[missed]['filename']}")

    # if False:
    #     # Find the sets of elements given multiple parameterizations
    #     for parameterizations in [
    #             ['mio'],
    #             ['mio', 'chalc'],
    #             ['mio', 'hyb'],
    #             ['mio', 'tiorg'],
    #             ['mio', 'znorg'],
    #             ['mio', 'tiorg', 'znorg']
    #     ]:
    #         print('')
    #         print(parameterizations)
    #         sets = find_sets(metadata, parameterizations)
    #         for group in sets:
    #             print(f'    {group}')

    # if True:
    #     # Get the maximum angular momentum from potentials
    #     all_potentials = metadata['potentials']
    #     for parameterization in metadata['parameterizations']:
    #         pdata = metadata[parameterization]
    #         version = [*pdata.keys()][0]
    #         vdata = pdata[version]
    #         potentials = vdata['potentials']
    #         print(parameterization)
    #         for potential, md5sum in potentials.items():
    #             data = all_potentials[md5sum]
    #             el1, el2 = data['elements']
    #             if el1 == el2:
    #                 sk_table = data['SK_table']
    #                 basis = sk_table['Basis']
    #                 shells = basis['Shells']
    #                 highest = shells.split()[-1][1]
    #                 if 'HubbDerivative' in basis:
    #                     hder = basis['HubbDerivative']
    #                     print(f"    {el1:2} {highest} {hder}")
    #                 else:
    #                     print(f"    {el1:2} {highest}")
