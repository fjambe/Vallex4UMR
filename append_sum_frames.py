import pandas as pd
from collections import defaultdict

def format_info(dataframe, predicate, frame_dict, output_file):
    examples = dataframe.loc[df["frame"].isin(frame_dict[predicate]['frames']), "example"].tolist()
    pos_line = " \t-POS: VERB\n" if not predicate.endswith("-91") else ""

    # Handle roles: if multiple sets exist, issue a warning and join them; otherwise just take the single string
    roles = frame_dict[predicate].get('roles')
    if isinstance(roles, set):
        if len(roles) == 1:
            roles_str = next(iter(roles))  # extract the single element
        else:
            # Multiple roles: join them with semicolon
            roles_str = "; ".join(sorted(roles))
            roles_str = roles_str + ' - WARNING: different frames'
    else:
        roles_str = roles or ""  # if it's a string or None

    formatted_info = (
        f"\n: id: {predicate}\n"
        # f" + {frame_dict.get(predicate)['roles']}\n"
        f" + {roles_str}\n"
        f"{pos_line}"
        f" \t-Vallex1_id: {'; '.join(frame_dict[predicate]['frames'])}\n"
        f" \t-example: {'; '.join(examples)}\n"
        # f" \t-LDT_ids: {'; '.join(info.get('LDT_id', []))}\n"
    )
    print(f'* {row["lemma"].upper()}', formatted_info)#, file=output_file)


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
            elif line.startswith("-Vallex1_id:"):
                frames = line[len("-Vallex1_id:"):].strip().split("; ")
                existing_entries[current_id]['frames'] = frames
            elif line.startswith("-example:"):
                examples = line[len("-example:"):].strip().split("; ")
                existing_entries[current_id]['examples'] = examples

    # Step 2: Read CSV files with sum and habeo frames
    df = pd.read_csv('sum_habeo_frames.csv', header=0)
    df = df[df['status'] == 'reviewed'].drop(columns=['status', 'notes', 'conversion rules', 'frequency'])

    # Step 3: Process frames and print information
    for _, row in df.iterrows():
        predicate_id = row["UMR concept"]

        if row['UMR concept'].startswith('(') or row['UMR concept'].startswith('if'):
            # separate document
            pass

        else:
            # predicate_info[predicate_id]['roles'] = abstract_predicates.get(predicate_id, "")

            # --- Extract roles from functors and UMR roles ---
            functors_list = [f.strip().split("(")[0] for f in row["functors"].split(",")] # Remove parenthetical info from each functor
            umr_roles_list = [r.strip() for r in row["UMR roles"].split("|")]
            roles_string = ", ".join(f"{f} [{r}]" for f, r in zip(functors_list, umr_roles_list))

            predicate_info[predicate_id]['roles'].add(roles_string)
            predicate_info[predicate_id]['frames'].append(row['frame'])

            if predicate_id not in existing_entries:
                format_info(df, predicate_id, predicate_info, vallex)

            else:
                # Merge frames
                frames = existing_entries[predicate_id].setdefault("frames", [])
                if row['frame'] not in frames:
                    frames.append(row['frame'])

                # Merge examples
                examples_list = existing_entries[predicate_id].setdefault("examples", [])
                if row['example'] not in examples_list:
                    examples_list.append(row['example'])

                if "roles" not in existing_entries[predicate_id] or not existing_entries[predicate_id]["roles"]:
                    existing_entries[predicate_id]["roles"] = roles_string





