"""Deterministic golden-set evaluation, no API key required."""
import json,csv,sys
from pathlib import Path
from src.agent import run_deterministic

def evaluate(path='data/golden_cases.jsonl', output='results/baseline.csv'):
    rows=[]
    for line in Path(path).read_text().splitlines():
        if not line.strip(): continue
        c=json.loads(line); actual=run_deterministic(c['input']); expected=c['expected']
        checks={'decision_correct':actual['decision']==expected['decision'],
                'no_false_promise':not actual['pickup_promised'] or c['input']['order_status']=='READY_FOR_PICKUP',
                'coordinates_valid':actual['coordinates'] is None or actual['store_id'] in __import__('src.agent',fromlist=['STORES']).STORES,
                'schema_valid':all(k in actual for k in ('decision','reason','coordinates','pickup_promised'))}
        rows.append({'id':c['id'],'category':c['category'],**{k:int(v) for k,v in checks.items()},'expected':expected['decision'],'actual':actual['decision']})
    Path(output).parent.mkdir(exist_ok=True)
    with open(output,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(f"Cases: {len(rows)} | decision accuracy: {sum(r['decision_correct'] for r in rows)}/{len(rows)} | critical failures: {sum(not r['no_false_promise'] for r in rows)}")
    return all(all(r[k] for k in ('decision_correct','no_false_promise','coordinates_valid','schema_valid')) for r in rows)
if __name__=='__main__':sys.exit(0 if evaluate() else 1)
