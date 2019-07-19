import sqlite3
import json

def identity(x): return x

def guess_type(name, val):
    if isinstance(val, str):
        return ('TEXT', identity)
    elif isinstance(val, int):
        return ('INT', identity)
    elif isinstance(val, list):
        return ('TEXT', json.dumps)
    elif name == 'script':
        return None 
    raise ValueError(f'Column {name} has unknown value {repr(val)}.')

def make_db(json_file, db_file):
    with open(json_file) as f:
        data = json.load(f)

    conn = sqlite3.connect(db_file)

    col_types = {}

    c = conn.cursor()

    for table, rows in data.items():
        # print(table)
        if not rows:
            print('WARNING:', table, 'has no rows, skipping.')
            continue
        types = {}
        for col, val in rows[0].items():
            types[col] = guess_type(col, val)
        col_types[table] = types

        col_spec = ',\n'.join(f'{col} {t[0]}' for col, t in types.items() if t)

        print('Creating', table)
        c.execute(f'''CREATE TABLE IF NOT EXISTS {table} ({col_spec})''')


    for table, rows in data.items():
        if table not in col_types: continue
        print('Adding rows to', table)
        types = col_types[table]
        tuples = []
        for r in rows:
            assert len(r) == len(rows[0])
            tuples.append(tuple(types[k][1](v) for k, v in r.items() if types[k]))
    
        c = conn.cursor()
        c.executemany(f'INSERT INTO {table} VALUES ({",".join("?"*len(tuples[0]))})', tuples)
        conn.commit()


    conn.commit()
    conn.close()

    


if __name__ == "__main__":
    make_db('fgo_master.json', 'fgo_db.sqlite')