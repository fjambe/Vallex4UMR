#!/usr/bin/env python3
# Copyright © 2024 Federica Gamba <gamba@ufal.mff.cuni.cz>

import csv
import warnings
import re


def split_key(key):
    alpha_part, num_part = key.rsplit('-', 1)
    return alpha_part, int(num_part)


if __name__ == "__main__":
    input_files = [
        'files_7.8.24/frames_Sallust_1-10.csv',
        'files_7.8.24/frames_Sallust_11-20.csv',
        'files_7.8.24/frames_Sallust_21-30.csv',
        'files_7.8.24/frames_Sallust_31-40.csv',
        'files_7.8.24/frames_Sallust_41-51.csv',
        'files_7.8.24/frames_Sallust_52-61.csv'
    ]

    # create a dict of dicts for mapping: main keys are UMR entries + each of them is a dictionary with keys v1_id, example, roles, lemma, ...
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
                        # we ignore entries annotated as UMR abstract predicates
                        if lines['UMR'].endswith('-91'):
                            continue
                        # we ignore not well-formed entries
                        if not re.match(r"^[a-zA-Z]+-\d{2}$", lines['UMR']):
                            continue
                        else:
                            # we proceed to create the entry for Vallex
                            mapped_entry = lines['UMR']  # extract the UMR key
                            if mapped_entry not in after_mapping:
                                after_mapping[mapped_entry] = {
                                    'LDT_id': [lines['id'] + f' (par.{par})'],  # list in case we need to add more than one id
                                    'v1_frame': [lines['V1 frame']],
                                    'example': [lines['example']],
                                    'roles': lines['roles'],
                                    'lemma': lines['lemma'],
                                    'synset_id': lines['synset id'],
                                    'URI_lemma': lines['URI lemma'],
                                    'definition': lines['definition'],
                                    'notes': lines['notes'],  # da valutare se tenere
                                    'gramm_info': lines['gramm_info']  # checked, no conflicts. no need to update it for duplicated entries.
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

                # sorting the mapped dictionary alphanumerically
                sorted_keys = sorted(after_mapping.keys(), key=split_key)
                after_mapping = {key: after_mapping[key] for key in sorted_keys}

                # printing out Vallex4UMR, after the mapping has been resolved (for now partially)
                # premature for now, to be printed later on
                for entry, info in after_mapping.items():
                    print(f"\n* {entry.split('-')[0].upper()}\n"
                          f" : id: {entry}\n"
                          f" : synset id: {info['synset_id']}\n"
                          # f" : lemma URI: {TODO}\n"  # extract from gui/some file, when I populate the synset_definition (otherwise there are some mismatches from the annotation).
                          f" + {info['roles']}\n"  # transform to PropBank-like (checking the annotated data)
                          f" \t-POS: {'NOUN' if info['synset_id'].split('#')[0] == 'n' else 'VERB' if info['synset_id'].split('#')[0] == 'v' else info['synset_id'].split('#')[0]}\n"
                          f" \t-Vallex1_id: {'; '.join(info['v1_frame'])}\n"
                          f" \t-example: {'; '.join(info['example'])}\n"
                          f" \t-LDT_ids: {'; '.join(info['LDT_id'])}\n", file=outfile)



# I think I also want to add the synset definition. I can populate it with some extra code exploiting gui/wn file.
# later on I will have to implement a sanity check (just saw opus with no roles)

# take care of newly defined entries, the ones having a 'definition'.

# transform to PropBank-like (checking the annotated data)