import argparse,json
from src.agent import run_deterministic,build_graph
p=argparse.ArgumentParser();p.add_argument('--graph',action='store_true');p.add_argument('--input',default='data/golden_cases.jsonl');a=p.parse_args()
with open(a.input,encoding='utf8') as f:
    for line in f:
        case=json.loads(line)
        if a.graph: result=build_graph().invoke({'request':case['input']})['result']
        else: result=run_deterministic(case['input'])
        print(json.dumps({'id':case['id'],'result':result}))
