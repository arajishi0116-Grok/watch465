import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data/members.json', encoding='utf-8') as f:
    m = json.load(f)
print(f'合計: {len(m)}人')
weird = [x for x in m if len(x['name']) < 2 or not x['party']]
print(f'要除外候補: {len(weird)}件')
for x in weird[:5]:
    print(x)
print('\n正常サンプル5件:')
normal = [x for x in m if len(x['name']) >= 2 and x['party']]
for x in normal[:5]:
    print(f"{x['name']} / {x['party']} / {x['constituency']} / {x['term_count']}期")
