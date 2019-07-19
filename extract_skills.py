import sqlite3
import json

from pprint import pprint
from collections import defaultdict

def main(db_file):
    with open('skills.json', encoding='utf-8') as f:
        skills = json.load(f)
    skills['四夜の終末 EX'] = 'The End of Four Nights EX'
    skills['被虐体質 A+'] = 'Masochistic Nature A+'
    skills['軍師の忠言 A'] = 'Tactician\'s Advice A'
    skills['宣帝の指揮 A'] = "Emperor's Command A"
    skills['至上礼装・月霊髄液 B'] = 'Supreme Mystic Code: Volumen Hydrargyrum B'
    skills['天秤の護り A+'] = 'Protection of the Scales A+'
    skills['魔力放出（星） A+'] = 'Mana Burst (Stars) A+'
    skills['星の裁き A'] = 'Judgment of the Stars A'
    skills['対霊戦闘 B'] = 'Anti-Spirit Combat B'
    skills['封印礼装解除 C'] = 'Sealed Mystic Code Deployment C'
    skills['最果ての加護 B'] = 'Protection of World\'s End B'
    
    replaces = {
        '耐':'対',
        '／': '/',
    }
    fixers = [
        lambda n: n.split()[0],
        lambda n: n.replace('（', '(').replace('）', ')'),
        lambda n: n.replace('(', '（').replace(')', '）'),
        lambda n: n.replace('(', '（').replace(') ', '）'),
        lambda n: n.replace('！', '!'),
        lambda n: n.replace('！ ', '！'),
        {' ': ''},
        {'  ': ' '}
    ]
    failed = []
    def get_skill_name(jp_name):
        o_name = jp_name
        if jp_name in skills:
            return skills[jp_name]
        for old, new in replaces.items():
            jp_name = jp_name.replace(old, new)

        if jp_name in skills:
            return skills[jp_name]

        for fixer in fixers:
            if isinstance(fixer, dict):
                _name = jp_name
                for old, new in fixer.items():
                    _name = _name.replace(old, new)
                fixer = lambda x: _name
            if fixer(jp_name) in skills:
                return skills[fixer(jp_name)]
        failed.append(o_name)
        return o_name
        # raise ValueError(f'jp_name: {o_name}, changed to {jp_name}')

    conn = sqlite3.connect(db_file)

    col_types = {}

    c = conn.cursor()
    
    skill_query = '''SELECT collectionNo, mstSvt.id, num, mstSkill.name, iconId FROM mstSvtSkill, mstSkill, mstSvt
WHERE mstSvtSkill.skillId = mstSkill.id AND mstSvtSkill.svtId = mstSvt.id
	AND mstSvtSkill.flag = 0 AND collectionNo > 0 AND battleName != '-'
ORDER BY collectionNo, num, skillId'''
    servant_skills = defaultdict(lambda: {'kaz_id': None, 'skills': [[], [], []], 'passives': []})
    for svt_id, kaz_id, num, name, icon in c.execute(skill_query):
        servant_skills[svt_id]['kaz_id'] = str(kaz_id)
        servant_skills[svt_id]['skills'][num-1].append((get_skill_name(name), icon))

    passive_query = '''SELECT collectionNo, classPassive FROM mstSvt
WHERE collectionNo > 0 AND battleName != '-'
ORDER BY collectionNo'''
    svt_passive_query = '''SELECT name, iconId FROM mstSkill
WHERE id IN ({})'''
    for svt_id, passives_str in c.execute(passive_query):
        passives = json.loads(passives_str)
        passives = [str(x) for x in passives]
        fmt_query = svt_passive_query.format(','.join('?'*len(passives)))
        c2 = conn.cursor()
        for name, icon in c2.execute(fmt_query, passives):
            servant_skills[svt_id]['passives'].append((get_skill_name(name), icon))
    conn.close()

    print(failed)
    with open('servant_skills.json', 'w') as f:
        json.dump(servant_skills, f)

    with open('servants.json') as f:
        servants = json.load(f)
    
    for svt in servants:
        servants[svt].update(servant_skills[int(svt)])
    
    with open('servant_details_and_skills.json', 'w') as f:
        json.dump(servants, f)

    


if __name__ == "__main__":
    main('fgo_master.sqlite')