import csv
from collections import defaultdict

def format_info(predicate, dictionary, output_file):
    """Format the information for a *single entry* before printing it out."""

    roles = {'belong-91': 'ACT [ARG1], PAT [ARG2]',
             'exist-91': 'ACT [ARG2]',
             'have-mod-91': 'ACT [ARG1], PAT [ARG2]',
             'have-place-91': 'ACT [ARG1], LOC [ARG2]',
             'have-role-91': 'ACT [ARG1], APP [ARG2], PAT [ARG3]',
             'have-source-91': 'ACT [ARG1], ORIG [ARG2]',
             'identity-91': 'ACT [ARG1], PAT [ARG2]'
             }

    formatted_info = (
        f"\n: id: {predicate}\n"
        f" + {roles[predicate]}\n"
        f" \t-POS: VERB\n"
        f" \t-Vallex1_id: {'; '.join(dictionary[ap])}\n"
        # f" \t-example: {'; '.join(ids)}\n"
        # f" \t-LDT_ids: {'; '.join(info.get('LDT_id', []))}\n"
    )
    print('* SUM', formatted_info, file=output_file)


frames = {}
predicates = defaultdict(list)

with open('valid_sum-frames_for_conversion.csv', mode='r') as infile:
    csv_file = csv.reader(infile)
    for line in csv_file:
        if line[5]:
            frames[line[0]] = line[5]
    for k, v in frames.items():
        predicates[v].append(k)

with open('Vallex4UMR.txt', mode='a') as outfile:
    for ap in predicates:
        format_info(ap, predicates, outfile)

