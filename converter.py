#!/usr/bin/env python3
# Copyright © 2024 Federica Gamba <gamba@ufal.mff.cuni.cz>

import csv
import warnings
import re
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--wordnet", default=False, help="Path to WordNet file.")
parser.add_argument("--mapping", default=False, help="Path to file mapping UMR and Vallex2 entries.")


def split_key(key):
    alpha_part, num_part = key.rsplit('-', 1)
    return alpha_part, int(num_part)


def sanity_check(umr_entry):
    # TODO: implement a sanity check (saw opus with no roles)
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


def retrieve_synset_def(umr_entry, entries_dict, defs):
    """Function to retrieve the synset definition given the synset id."""
    synset_id = entries_dict[umr_entry]['synset_id']
    return defs.get(synset_id)


def store_uris_from_mapping(mapping_file):
    with open(mapping_file, mode='r') as mapping:
        return {row['UMR_id']: row['uri'] for row in csv.DictReader(mapping, delimiter='\t')}


def retrieve_uri(umr_entry, stored_uris):
    """Function to retrieve the URI given the UMR id."""
    return stored_uris.get(umr_entry)


if __name__ == "__main__":

    args = parser.parse_args()
    definitions = store_wordnet(args.wordnet)
    uris = store_uris_from_mapping(args.mapping)

    input_files = [
        'files_7.8.24/frames_Sallust_1-10.csv',
        'files_7.8.24/frames_Sallust_11-20.csv',
        'files_7.8.24/frames_Sallust_21-30.csv',
        'files_7.8.24/frames_Sallust_31-40.csv',
        'files_7.8.24/frames_Sallust_41-51.csv',
        'files_7.8.24/frames_Sallust_52-61.csv'
    ]

    # Create a dictionary of dictionaries for mapping:
    # main keys are UMR entries + each of them is a dictionary with keys v1_id, example, roles, lemma, ...
    after_mapping = {}
    for file_path in input_files:
        with open(file_path, mode='r') as infile:
            csv_file = csv.DictReader(infile)
            with open('Vallex4UMR.txt', 'w') as outfile:
                for lines in csv_file:
                    if 'Par.' in lines['id']:
                        par = lines['id'].split(' ')[-1]
                        continue
                    else:
                        # Ignore entries annotated as UMR abstract predicates
                        if lines['UMR'].endswith('-91'):
                            continue
                        # Ignore not well-formed entries
                        if not re.match(r"^[a-zA-Z]+-\d{2}$", lines['UMR']):
                            continue
                        else:
                            # Create the entry for Vallex4UMR, by first extracting the UMR key
                            mapped_entry = lines['UMR']
                            if mapped_entry not in after_mapping:
                                # Lists are used in case it is necessary to add more than one id to a same entry
                                after_mapping[mapped_entry] = {
                                    'LDT_id': [lines['id'] + f' (par.{par})'],
                                    'v1_frame': [lines['V1 frame']],
                                    'example': [lines['example']],
                                    'roles': lines['roles'],
                                    'lemma': lines['lemma'],
                                    'synset_id': lines['synset id'],
                                    'URI_lemma': lines['URI lemma'],
                                    'definition': lines['definition'],
                                    'notes': lines['notes'],  # da valutare se tenere
                                    'gramm_info': lines['gramm_info']  # No conflicts, so no need to update it for duplicate entries.
                                }

                            else:
                                after_mapping[mapped_entry]['LDT_id'].append(lines['id'] + f' (par.{par})')
                                after_mapping[mapped_entry]['v1_frame'].append(lines['V1 frame'])
                                after_mapping[mapped_entry]['example'].append(lines['example'])
                                # TODO: lemma, synset_id, URI_lemma, definition will be the same.
                                # TODO: decide what to do with notes.
                                # if lines['roles'] != after_mapping[mapped_entry]['roles']:
                                #     warnings.warn(f"Mismatch in roles:{lines['roles']} VS. {after_mapping[mapped_entry]['roles']}."
                                #                   f"Check the entry with LDT id {lines['id']}.")
                                # if lines['notes'] != after_mapping[mapped_entry]['notes']:
                                #     warnings.warn(f"Mismatch in notes:{lines['notes']} VS. {after_mapping[mapped_entry]['notes']}."
                                #                   f"Check the entry with LDT id {lines['id']}.")

                # Sort the mapped dictionary alphanumerically
                sorted_keys = sorted(after_mapping.keys(), key=split_key)
                after_mapping = {key: after_mapping[key] for key in sorted_keys}

                # Print out Vallex4UMR, after the mapping has been resolved
                for entry, info in after_mapping.items():
                    print(f"\n* {entry.split('-')[0].upper()}\n"
                          f" : id: {entry}\n"
                          f" : synset id: {info['synset_id']}\n"
                          f" : synset definition: {retrieve_synset_def(entry, after_mapping, definitions)}\n"
                          f" : lemma URI: {retrieve_uri(entry, uris)}\n"
                          f" + {info['roles']}\n"
                          f" \t-POS: {'NOUN' if info['synset_id'].split('#')[0] == 'n' else 'VERB' if info['synset_id'].split('#')[0] == 'v' else info['synset_id'].split('#')[0]}\n"
                          f" \t-Vallex1_id: {'; '.join(info['v1_frame'])}\n"
                          f" \t-example: {'; '.join(info['example'])}\n"
                          f" \t-LDT_ids: {'; '.join(info['LDT_id'])}\n", file=outfile)

# TODOs:
# take care of newly defined entries, the ones having a 'definition'.
# transform to PropBank-like (checking the annotated data)

# I probably want to populate also the rest of entries (althought not observed in the text) based on the mapping.
# they will contain less information, but for now it is somehow weird to see missing numbers
# (e.g.: reperio-07 ... reperio-10)