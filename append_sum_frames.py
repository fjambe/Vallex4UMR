import pandas as pd
from collections import defaultdict
import re

def custom_sort_key(pr_id):
    """
    Sort predicates alphabetically, with rules:
    - Base entries (like habeo-25) come first.
    - Their -NEW-xx variants come immediately after them.
    - Sub-bases (like habeo-in-incerto-NEW-01) follow later, sorted normally.
    """

    # Case 1: plain base like habeo-25
    m_base = re.match(r"^(.*?)-(\d+)$", pr_id)
    if m_base:
        lemma, num = m_base.groups()
        return lemma, int(num), 0  # 0 = base

    # Case 2: NEW variant of base like habeo-NEW-25
    m_new = re.match(r"^(.*?)-NEW-(\d+)$", pr_id)
    if m_new:
        lemma, num = m_new.groups()
        return lemma, int(num), 1  # 1 = NEW, comes after base

    # Case 3: sub-base (like habeo-in-incerto-NEW-01)
    return pr_id, float("inf"), 2  # keep them later, natural order


def format_info(dataframe, predicate, frame_dict, output):
    exs = dataframe.loc[df["frame"].isin(frame_dict[predicate]['frames']), "example"].tolist()
    pos_value = output[predicate].get("POS")  # try to fetch stored POS
    if not pos_value:
        pos_value = "VERB" if not predicate.endswith("-91") else ""  # default rule
    pos_line = f" \t-POS: {pos_value}\n" if pos_value else ""

    # Handle synset_id, synset_definition, lemma_URI
    syn_id = output[predicate].get("synset_id", "")
    syn_def = output[predicate].get("synset_definition", "")
    lemma_uri = output[predicate].get("lemma_URI", "")
    ldt = output[predicate].get("LDT_ids", [])

    syn_id_line = f" \t-synset_id: {syn_id}\n" if syn_id else ""
    syn_def_line = f" \t-synset_definition: {syn_def}\n" if syn_def else ""
    lemma_uri_line = f" \t-lemma_URI: {lemma_uri}\n" if lemma_uri else ""
    ldt_ids_line = f" \t-LDT_ids: {'; '.join(ldt)}\n" if ldt else ""

    # Handle roles: if multiple sets exist, issue a warning and join them; otherwise just take the single string
    roles = frame_dict[predicate].get('roles')
    if isinstance(roles, set):
        if len(roles) == 1:
            roles_str = next(iter(roles))  # extract the single element
        elif len(roles) == 0:
            roles_str = ""
        else:
            roles_str = "; ".join(sorted(roles))
            roles_str = roles_str + ' - WARNING: different frames'
    else:
        roles_str = roles or ""  # if it's a string or None

    vallex_ids = frame_dict[predicate]['frames']
    vallex_line = f" \t-Vallex1_id: {'; '.join(vallex_ids)}\n" if vallex_ids else ""
    example_line = f" \t-example: {'; '.join(exs)}\n" if exs else ""

    formatted_info = (
        f"\n: id: {predicate}\n"
        f" + {roles_str}\n"
        f"{syn_id_line}"
        f"{syn_def_line}"
        f"{lemma_uri_line}"
        f"{pos_line}"
        f"{vallex_line}"
        f"{example_line}"
        f"{ldt_ids_line}"
    )
    return formatted_info


predicate_info = defaultdict(lambda: {"roles": set(), "frames": []})

abstract_predicates = {
    'exist-91': 'ACT [ARG1]',
    'have-mod-91': 'ACT [ARG1], PAT [ARG2]',
    'have-place-91': 'ACT [ARG1], LOC [ARG2]',
    'have-role-91': 'ACT [ARG1], APP [ARG2], PAT [ARG3]',
    'have-source-91': 'ACT [ARG1], ORIG [ARG2]',
    'identity-91': 'ACT [ARG1], PAT [ARG2]',
    'thetic-possession-91': 'ACT [ARG1], PAT [ARG2]',
    'pred-possession-91': 'ACT [ARG1], PAT [ARG2]',
    'have-causer-91': 'ACT [ARG1], ORIG [ARG2]',
    'include-91': 'ACT [ARG1], LOC [ARG2]',
    'have-result-91': 'ACT [ARG1], PAT [ARG2]',
    'have-example-91': 'ACT [ARG1], PAT [ARG2]'
    }

if __name__ == "__main__":

    # Step 1: Read Vallex file and extract existing information
    existing_entries = {}

    current_pred = None  # lemma
    current_id = None  # actual predicate id, will be dictionary key

    with open("Vallex4UMR.txt", "r", encoding="utf-8") as vallex:
        for line in vallex:
            line = line.strip()
            if line.startswith("* "):
                current_pred = line[2:]  # store lemma for printing
            elif line.startswith(": id:"):
                current_id = line[len(": id:"):].strip()
                if current_id not in existing_entries:
                    existing_entries[current_id] = {"lemma": current_pred}
            elif line.startswith("+"):
                existing_entries[current_id]['roles'] = line[2:].strip()
            elif line.startswith("-synset_id:"):
                existing_entries[current_id]['synset_id'] = line[len("-synset_id:"):].strip()
            elif line.startswith("-synset_definition:"):
                existing_entries[current_id]['synset_definition'] = line[len("-synset_definition:"):].strip()
            elif line.startswith("-lemma_URI:"):
                existing_entries[current_id]['lemma_URI'] = line[len("-lemma_URI:"):].strip()
            elif line.startswith("-POS:"):
                pos_val = line[len("-POS:"):].strip()
                existing_entries[current_id]['POS'] = pos_val
            elif line.startswith("-Vallex1_id:"):
                frames = line[len("-Vallex1_id:"):].strip().split("; ")
                existing_entries[current_id]['frames'] = frames
            elif line.startswith("-example:"):
                examples = line[len("-example:"):].strip().split("; ")
                existing_entries[current_id]['examples'] = examples
            elif line.startswith("-LDT_ids:"):
                ldt_ids = line[len("-LDT_ids:"):].strip().split("; ")
                existing_entries[current_id]['LDT_ids'] = ldt_ids

    for pred_id, info in existing_entries.items():
        if "roles" in info and info["roles"]:
            predicate_info[pred_id]['roles'].add(info["roles"])
        if "frames" in info and info["frames"]:
            predicate_info[pred_id]['frames'].extend(info["frames"])

    # Step 2: Read CSV files with sum and habeo frames
    df = pd.read_csv('sum_habeo_frames.csv', header=0)
    df = df[df['status'] == 'reviewed'].drop(columns=['status', 'notes', 'conversion rules', 'frequency'])

    # Step 3: Process frames
    for _, row in df.iterrows():
        predicate_id = row["UMR concept"]

        if row['UMR concept'].startswith('(') or row['UMR concept'].startswith('if'):
            # separate document
            pass

        else:
            # --- Extract roles from functors and UMR roles ---
            functors_list = [f.strip().split("(")[0] for f in row["functors"].split(",")] # Remove parenthetical info from each functor
            umr_roles_list = [r.strip() for r in row["UMR roles"].split("|")]
            roles_string = ", ".join(f"{f} [{r}]" for f, r in zip(functors_list, umr_roles_list))

            predicate_info[predicate_id]['roles'].add(roles_string)
            predicate_info[predicate_id]['frames'].append(row['frame'])

            if predicate_id not in existing_entries:
                existing_entries[predicate_id] = {
                    "lemma": row["lemma"],
                    "frames": [row["frame"]],
                    "examples": [row["example"]],
                    "roles": roles_string,
                    "pos": None,
                    "synset_id": None,
                    "synset_definition": row["meaning"],
                    "lemma_URI": None,
                    "LDT_ids": []
                }

            else:
                # Merge information
                frames = existing_entries[predicate_id].setdefault("frames", [])
                if row['frame'] not in frames:
                    frames.append(row['frame'])

                examples_list = existing_entries[predicate_id].setdefault("examples", [])
                if row['example'] not in examples_list:
                    examples_list.append(row['example'])

                if "roles" not in existing_entries[predicate_id] or not existing_entries[predicate_id]["roles"]:
                    existing_entries[predicate_id]["roles"] = roles_string

                if "NEW" in predicate_id:
                    if not existing_entries[predicate_id].get("synset_definition"):
                        existing_entries[predicate_id]["synset_definition"] = row.get("meaning", "").strip()

    # Sort before printing everything at the end.
    with open("Vallex4UMR_updated.txt", "w", encoding="utf-8") as output_file:
        for predicate_id in sorted(existing_entries.keys(), key=custom_sort_key):
            entry_text = format_info(df, predicate_id, predicate_info, existing_entries)
            output_file.write(entry_text)

