#!/usr/bin/env python3
# Copyright © 2024 Federica Gamba <gamba@ufal.mff.cuni.cz>

import csv
import warnings
import re
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--wordnet", default=False, help="Path to WordNet file.")
parser.add_argument("--mapping", default=False, help="Path to file mapping UMR and Vallex2 entries.")
parser.add_argument("--vallex", default=False, help="Path to Vallex2 file.")


pos = {
    'a': 'ADJ',
    'n': 'NOUN',
    'v': 'VERB',
    'r': 'ADV',
}

def split_key(key):
    alpha_part, num_part = key.rsplit('-', 1)
    return alpha_part, int(num_part)


def control(umr_entry):
    # TODO: verify that entries are well-formed.
    pass


def store_wordnet(filename):
    """Storing WordNet synsets given the WordNet file path."""
    defs = {}
    with open(filename, mode='r') as wordnet:
        for row in csv.DictReader(wordnet):
            syn_id = row['id_synset'].split('/')[-1].split('-')
            syn_id = syn_id[1] + '#' + syn_id[0]
            defs[syn_id] = row['definition']
        return defs


def retrieve_synset_def(syn_id, defs):
    """Function to retrieve the synset definition given the synset id,
    or the brand-new definition created when a WN synset was not available."""
    return " + ".join([defs.get(s, 'Unknown') for s in syn_id.split('/')])


def store_uris_from_mapping(mapping_file):
    with open(mapping_file, mode='r') as mapping:
        return {row['UMR_id']: row['uri'] for row in csv.DictReader(mapping, delimiter='\t')}


def retrieve_uri(umr_entry, stored_uris):
    """Function to retrieve the URI given the UMR id."""
    # Handle merged entries: get the first part before the first '/'
    base_entry = umr_entry.split('/')[0]
    if 'NEW' in base_entry:
        base_entry = base_entry.split('-')[0] + "-01"  # the URI is shared for the same lemma, so any word sense is fine
    return stored_uris.get(base_entry)


def create_entries(infos, row):
    mpd_entry = row['UMR']
    roles = list(role.strip() for role in row['roles'].split(','))
    if mpd_entry not in infos:
        # Create the entry for Vallex4UMR, by first extracting the UMR key
        synset_def = retrieve_synset_def(row['synset_id'], definitions)
        uri = retrieve_uri(mpd_entry, uris)
        infos[mpd_entry] = {
            # Lists/sets are used in case it is necessary to add more than one id to a same entry
            'LDT_id': [row['id'] + f' (par.{par})'],
            'v1_frame': {row['V1 frame']},
            'example': {row['example']},
            'roles': roles_to_propbank([role.strip() for role in row['roles'].split(',')]),
            'lemma': row['lemma'],
            'synset_id': row['synset_id'].replace('#', '-') if row['synset_id'] else 'NA',
            'URI_lemma': uri if uri else 'http://lila-erc.eu/data/id/lemma/'+row['URI lemma'],
            'definition': synset_def if synset_def != 'Unknown' else row['definition'],
            'POS': pos.get(row['synset_id'].split('#')[0], row['synset_id'].split('#')[0]),
            'gramm_info': row['gramm_info']  # conflicts are checked by the warning, so no need of list
        }
    else:
        infos[mpd_entry]['LDT_id'].append(lines['id'] + f' (par.{par})')
        infos[mpd_entry]['v1_frame'].add(lines['V1 frame'])
        infos[mpd_entry]['example'].add(lines['example'])
        # lemma, synset_id, URI_lemma, definition will be the same.
        if roles_to_propbank([role.strip() for role in lines['roles'].split(',')]) != infos[mpd_entry]['roles']:
            warnings.warn(f"Mismatch in roles:{lines['roles']} VS. {infos[mpd_entry]['roles']}."
                          f"Check the entry with LDT id {lines['id']} and {infos[mpd_entry]['LDT_id']}.")
        if lines['gramm_info'] != infos[mpd_entry]['gramm_info']:
            warnings.warn(f"Mismatch in gramm_info:{lines['gramm_info']} VS. {infos[mpd_entry]['gramm_info']}."
                          f"Check the entry with LDT id {lines['id']} and {infos[mpd_entry]['LDT_id']}.")
    return infos


def format_info(info, full=True):
    """Format the information for a single entry before printing it out."""
    # Basic information that is always included
    gramm_info_line = f" \t-gramm_info: {info.get('gramm_info')}\n" if info.get('gramm_info') else ''
    formatted_info = (
        f": id: {info.get('entry', 'NA')}\n"
        f" + {info.get('roles', 'NA')}\n"
        f" \t-synset_id: {info.get('synset_id', 'NA')}\n"
        f" \t-synset_definition: {info.get('definition', 'NA')}\n"
        f" \t-lemma_URI: {info.get('URI_lemma', 'NA')}\n"
        f" \t-POS: {info.get('POS', 'NA')}\n"
        f"{gramm_info_line}"
    )

    # Additional information only included if full is True
    if full:
        formatted_info += (
            f" \t-Vallex1_id: {'; '.join(info.get('v1_frame', []))}\n"
            f" \t-example: {'; '.join(info.get('example', []))}\n"
            f" \t-LDT_ids: {'; '.join(info.get('LDT_id', []))}\n"
        )

    return formatted_info


def remove_duplicates(infos):
    """
    Remove single entries that are part of merged ones, to avoid repetition.
    E.g., cupiditas-01 and cupiditas-02, as they have been merged as cupiditas-01/cupiditas-02.
    """
    # Reorder infos so that merged entries occur first.
    infos = dict(sorted(infos.items(), key=lambda item: ('/' not in item[0], item[0])))

    processed = set()
    for entry, info in infos.items():
            if '/' in entry:
                for sub_entry in entry.split('/'):
                    processed.add(sub_entry)

    return {key: infos[key] for key in sorted(infos) if key not in processed}


def process_entries(infos, output_file):
    """Process and print all entries in filtered_infos."""
    for entry, info in infos.items():
        header = f"* {entry.split('-')[0].upper()}\n"
        entry_info = format_info({**info, 'entry': entry}, full='LDT_id' in info and bool(info.get('LDT_id')))
        print(header, entry_info, file=output_file)


def populate_other_entries(mapping_file, vallex, infos):
    """
    Function to create entries for which no occurrences in the text have been found.
    Based on the mapping between UMR and Vallex2.
    Roles (e.g. ACT, PAT) are taken from Vallex2.
    """
    with open(mapping_file, mode='r') as mapping, open(vallex, mode='r') as val:
        stored_vallex = {f"{row['uri']}+{row['id_synset']}": row['arguments_set'] for row in csv.DictReader(val, delimiter='\t')}
        storage = {
            row['UMR_id']: {
                'lemma': row['lemma'],
                'synset_id': row['id_synset'].replace('#', '-'),
                'URI_lemma': row['uri'],
                'definition': retrieve_synset_def(row['id_synset'], definitions),
                'POS': pos.get(row['id_synset'].split('#')[0], row['id_synset'].split('#')[0]),
                'roles': roles_to_propbank(stored_vallex.get(f"{row['uri']}+{row['id_synset']}").split(','))
            }
            for row in csv.DictReader(mapping, delimiter='\t')}

        # merge the 'non-observed' entries with the main ones from create_entries()
        for umr_id, data in storage.items():
            if umr_id not in infos:
                infos[umr_id] = data

        return infos


def roles_to_propbank(roles: list):
    """
    Function to convert ACT/PAT/... functors to ARG0/ARG1/... PropBank roles.
    Based on a custom hierarchy (cf. default mapping available at
    https://github.com/ufal/UMR/blob/main/tecto2umr/dafault-functors-to-umrlabels.txt).
    Only ACT and PAT are fixed (ARG0 and ARG1, respectively). Arguments follow, then adjuncts.
    """
    functor_hierarchy = [
        'ACT', 'PAT', 'ADDR', 'EFF', 'ORIG', 'BEN', 'DIFF', 'REG', 'MANN', 'DIR1', 'DIR3', 'DIR2', 'LOC',
        'TOWH', 'TFHL', 'TWHEN', 'MEANS', 'EXT', 'AIM', 'MAT', 'INTT', 'CAUS', 'CPR', 'APP', 'ACMP'
    ]

    sorted_functors = sorted(f for f in roles if f.strip() not in ['---', ''])
    pb_roles = []
    # Assign ARG0 to ACT and ARG1 to PAT if present, and track current_arg
    current_arg = 0
    for functor in ['ACT', 'PAT']:
        if functor in sorted_functors:
            pb_roles.append(f"{functor} [ARG{current_arg}]")
            current_arg += 1
            sorted_functors.remove(functor)

    # Assign remaining functors to ARG starting from current_arg
    pb_roles += [f"{functor} [ARG{current_arg + idx}]" for idx, functor in enumerate(sorted(sorted_functors, key=lambda f: functor_hierarchy.index(f)))]

    return ", ".join(pb_roles)


if __name__ == "__main__":

    args = parser.parse_args()
    definitions = store_wordnet(args.wordnet)
    uris = store_uris_from_mapping(args.mapping)

    input_files = [
        'files_26.8.24/frames_Sallust_1-10.csv',
        'files_26.8.24/frames_Sallust_11-20.csv',
        'files_26.8.24/frames_Sallust_21-30.csv',
        'files_26.8.24/frames_Sallust_31-40.csv',
        'files_26.8.24/frames_Sallust_41-51.csv',
        'files_26.8.24/frames_Sallust_52-61.csv'
    ]

    # Create a dictionary of dictionaries for mapping:
    # main keys are UMR entries + each of them is a dictionary with keys v1_id, example, roles, lemma, ...
    after_mapping = {}
    with open('Vallex4UMR.txt', 'w') as outfile:
        for file_path in input_files:
            with open(file_path, mode='r') as infile:
                csv_file = csv.DictReader(infile)
                for lines in csv_file:
                    if 'Par.' in lines['id']:
                        par = lines['id'].split(' ')[-1]
                        continue
                    else:
                        # Ignore entries annotated as UMR abstract predicates
                        if lines['UMR'].endswith('-91'):
                            continue
                        # Consider only well-formed entries
                        # 1. standard patterns (dico-01, dico2-01, dico-NEW-23)
                        # 2. merged entries (polliceor-01/polliceor-02)
                        if re.match(r"^[a-zA-Z]+(\d)?(-NEW)?-\d{2}(/[a-zA-Z]+(\d)?(-NEW)?-\d{2})*$", lines["UMR"]):
                            create_entries(after_mapping, lines)

        after_mapping = populate_other_entries(args.mapping, args.vallex, after_mapping)

        # Print out Vallex4UMR, after the mapping has been resolved
        filtered_after_mapping = remove_duplicates(after_mapping)
        process_entries(filtered_after_mapping, outfile)