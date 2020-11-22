#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility program to scan the Slater-Koster potential files and extract
the metadata from them.
"""

import hashlib
import json  # noqa: F401
from pathlib import Path
import pprint  # noqa: F401

import xmltodict


def parse_file(filename):
    with open(filename, 'r') as fd:
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
    metadata = dict(**xmltodict.parse('\n'.join(xml)))

    data = ''.join(data)
    m = hashlib.md5(data.encode())
    md5sum = m.hexdigest()

    return md5sum, metadata


def test_one(filename='data/slako/3ob/3ob-3-1/Br-Br.skf'):
    md5sum, metadata = parse_file(filename)

    # print(f'md5sum = {md5sum}')
    # print(json.dumps(metadata, indent=4))

    general = metadata['Documentation']['General']
    if general['Md5sum'] != md5sum:
        print('md5 checksums differ!')

    compatibility = general['Compatibility']
    partners = compatibility['Partner']
    for partner in partners:
        print(f"{partner['@Identifier']:>9} {partner['Md5sum']}")

    SK_table = metadata['Documentation']['SK_table']
    print(f"Shells = {SK_table['Basis']['Shells']}")


def analyze_directory(root='data/slako'):
    """Find all the Slater-Koster files under a given directory
    and analyze their metadata.
    """
    if not isinstance(root, Path):
        root = Path(root)

    comments = []
    metadata = {
        'bad_md5s': {},
        'same': {},
        'parameterizations': [],
        'potentials': {},
    }
    bad = metadata['bad_md5s']
    same = metadata['same']
    parameterizations = metadata['parameterizations']
    all_potentials = metadata['potentials']

    sk_files = root.glob('**/*.skf')
    for path in sk_files:
        # Assume the parent directory is the parameterization + version
        # and grandparent is the parameterization.
        parent = path.parent
        grandparent = parent.parent
        parameterization = grandparent.name
        version = '.'.join(parent.name.split('-')[1:])
        if parameterization not in parameterizations:
            parameterizations.append(parameterization)

        md5sum, data = parse_file(path)

        data = data['Documentation']
        general = data['General']

        data['parameterization'] = parameterization
        data['version'] = version
        data['filename'] = str(path)

        if md5sum in all_potentials:
            if 'filename' not in all_potentials[md5sum]:
                comments.append(
                    f"{path} metadata already exists for {md5sum} "
                    "but there is no filename !?!"
                )
            else:
                same[str(path)] = all_potentials[md5sum]['filename']
        else:
            all_potentials[md5sum] = data

        if general['Md5sum'] != md5sum:
            md5 = general['Md5sum']

            data['md5 mismatch'] = True
            bad[md5sum] = md5
            # comments.append(f'{path} md5 checksums differ!')
        else:
            data['md5 mismatch'] = False
            
        if parameterization not in metadata:
            pdata = metadata[parameterization] = {}
        else:
            pdata = metadata[parameterization]
        if version not in pdata:
            vdata = pdata[version] = {
                'potentials': {},
                'sets': []
            }
        else:
            vdata = pdata[version]
        potentials = vdata['potentials']
        el1 = general['Element1']
        if 'Element2' in general:
            el2 = general['Element2']
        else:
            el2 = el1
        # Check the file name
        if '-' in path.stem:
            try:
                tmp1, tmp2 = path.stem.split('_')[0].split('-')
                if tmp1 != el1 or tmp2 != el2:
                    comments.append(
                        f'Element error in {path}: should be {el1}-{el2}'
                    )
                    data['elements'] = [tmp1, tmp2]
            except Exception:
                print(f'Odd filename: {path} -- elements {el1}-{el2}')
                comments.append(
                    f'Odd filename: {path} -- elements {el1}-{el2}'
                )
            # Believe the filename
            potentials[path.stem] = md5sum
        else:
            if path.stem != el1 + el2:
                print(f'Odd filename: {path} -- elements {el1}-{el2}')
                comments.append(
                    f'Odd filename: {path} -- elements {el1}-{el2}'
                )
            # Believe the elements
            potentials[f'{el1}-{el2}'] = md5sum
            data['elements'] = [el1, el2]

    # The files that have the same potential
    if len(same) > 0:
        comments.append('')
        comments.append('The following files have the same data:')
        for f1, f2 in same.items():
            if Path(f1).parent == Path(f2).parent:
                comments.append(f'    {f1} {Path(f2).name}')
            else:
                comments.append(f'    {f1} {f2}')

    # Check on the bad md5 sums from in the file
    comments.append('')
    for good, other in bad.items():
        good_file = Path(all_potentials[good]['filename']).relative_to(root)
        if other in metadata:
            other_file = Path(
                all_potentials[other]['filename']
            ).relative_to(root)
            comments.append(
                f'file {good_file} has the MD5 sum from {other_file}'
            )
        else:
            comments.append(
                f'file {good_file} has an MD5 sum internally that doesnt '
                'match anything'
            )

    return metadata, comments


def find_sets(metadata, parameterization):
    """Find the sets of atoms with complete parameterizations"""
    pdata = metadata[parameterization]
    version = [*pdata.keys()][0]
    vdata = pdata[version]
    potentials = vdata['potentials']
    elements = []
    for stem in potentials.keys():
        el1, el2 = stem.split('-')
        if el1 not in elements:
            elements.append(el1)
        if el2 not in elements:
            elements.append(el2)
    elements.sort()

    pairs = {el: [] for el in elements}
    for stem in potentials.keys():
        el1, el2 = stem.split('-')
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
            result.append([*n_set])

    vdata['sets'] = result
    return result


def partners2(metadata, parameterization):
    """Find the listed partners"""
    pdata = metadata[parameterization]
    all_potentials = metadata['potentials']
    version = [*pdata.keys()][0]
    vdata = pdata[version]
    potentials = vdata['potentials']

    for key, md5sum in potentials.items():
        print(f'\n{key}')
        data = all_potentials[md5sum]
        general = data['General']
        if 'Compatibility' not in general:
            print(f"{data['filename']} has no compatibility data")
            continue
        compatibility = general['Compatibility']
        for partner in compatibility['Partner']:
            md5 = partner['Md5sum']
            if md5 in all_potentials:
                tmp = all_potentials[md5]
                print(
                    f"     {tmp['parameterization']} {tmp['version']} "
                    f"{partner['@Identifier']}"
                )
            elif md5 in metadata['bad_md5s']:
                good_md5 = metadata['bad_md5s'][md5]
                tmp = all_potentials[good_md5]
                print(
                    f"     {tmp['parameterization']} {tmp['version']} "
                    f"{partner['@Identifier']}"
                )
            else:
                print(f"    {partner['@Identifier']} {partner['Md5sum']}")
                pprint.pprint(partner)


def partners(metadata):
    """Find the listed partners"""
    all_potentials = metadata['potentials']

    for md5sum, data in all_potentials.items():
        data = all_potentials[md5sum]
        general = data['General']
        if 'Compatibility' not in general:
            print(f"{data['filename']} has no compatibility data")
            continue
        compatibility = general['Compatibility']
        partners = []
        for partner in compatibility['Partner']:
            md5 = partner['Md5sum']
            if md5 in all_potentials:
                partners.append(md5)
            elif md5 in metadata['bad_md5s']:
                good_md5 = metadata['bad_md5s'][md5]
                partners.append(good_md5)
            else:
                print(f"    {partner['@Identifier']} {partner['Md5sum']}")
                pprint.pprint(partner)
        data['partners'] = partners


if __name__ == "__main__":
    # test_one('data/slako/3ob/3ob-3-1/Br-Br.skf')

    metadata, comments = analyze_directory('data/slako')
    print('\n'.join(comments))
    print('')

    if True:
        for parameterization in metadata['parameterizations']:
            print('')
            print(parameterization)
            sets = find_sets(metadata, parameterization)
            for group in sets:
                print(f'    {group}')

    if True:
        partners(metadata)

