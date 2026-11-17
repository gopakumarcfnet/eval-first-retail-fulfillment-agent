"""Synthetic retail fulfillment decision graph. No proprietary rules or APIs."""
from typing import TypedDict

STORES = {
    'UAE-DXB-01': {'country':'AE','city':'Dubai','district':'Downtown','lat':25.1972,'lon':55.2744,'active':True},
    'UAE-AUH-01': {'country':'AE','city':'Abu Dhabi','district':'Al Zahiyah','lat':24.4945,'lon':54.3723,'active':True},
    'TR-IST-01': {'country':'TR','city':'Istanbul','district':'Kadikoy','lat':40.9909,'lon':29.0293,'active':True},
    'TR-ANK-01': {'country':'TR','city':'Ankara','district':'Cankaya','lat':39.9179,'lon':32.8627,'active':True},
    'US-SFO-01': {'country':'US','city':'San Francisco','district':'SoMa','lat':37.7749,'lon':-122.4194,'active':True},
    'US-SJC-01': {'country':'US','city':'San Jose','district':'Downtown','lat':37.3382,'lon':-121.8863,'active':True},
}
# Project-specific fictional business rules; not official country requirements.
POSTAL_POLICY = {'AE':'optional', 'TR':'optional', 'US':'required'}
READY = {'READY_FOR_PICKUP'}

class State(TypedDict, total=False):
    request: dict
    address_ok: bool
    address_reason: str
    location_ok: bool
    location_reason: str
    pickup_ok: bool
    pickup_reason: str
    decision: str
    reason: str
    store: dict
    result: dict

def validate_address(state: State) -> dict:
    r = state['request']; country=r.get('country'); policy=POSTAL_POLICY.get(country)
    if not policy: return {'address_ok':False,'address_reason':'Unsupported country'}
    if not r.get('city'): return {'address_ok':False,'address_reason':'City missing'}
    if policy=='required' and not str(r.get('postal_code') or '').strip():
        return {'address_ok':False,'address_reason':'Postal code required by simulated US policy'}
    return {'address_ok':True,'address_reason':'Address meets simulated country policy'}

def resolve_location(state: State) -> dict:
    r=state['request']; s=STORES.get(r.get('store_id'))
    if not s: return {'location_ok':False,'location_reason':'Unknown store; no coordinates inferred','store':{}}
    if not s['active']: return {'location_ok':False,'location_reason':'Store inactive','store':s}
    if (s['country'],s['city'].casefold(),s['district'].casefold()) != (r.get('country'),str(r.get('city','')).casefold(),str(r.get('district','')).casefold()):
        return {'location_ok':False,'location_reason':'Store and address location mismatch','store':{}}
    return {'location_ok':True,'location_reason':'Matched a seeded synthetic store','store':s}

def check_pickup(state: State) -> dict:
    ok=state['request'].get('order_status') in READY
    return {'pickup_ok':ok,'pickup_reason':'Order marked ready' if ok else 'Order not confirmed ready for pickup'}

def decide(state: State) -> dict:
    if not state['address_ok']: d='NEEDS_REVIEW'; reason=state['address_reason']
    elif not state['location_ok']: d='NEEDS_REVIEW'; reason=state['location_reason']
    elif not state['pickup_ok']: d='NOT_READY'; reason=state['pickup_reason']
    else: d='ELIGIBLE'; reason='Validated location and confirmed pickup-ready order'
    r=state['request']
    return {'decision':d,'reason':reason,'to':r.get('customer_id','anonymous'),'store_id':r.get('store_id'),'country':r.get('country'),'coordinates':({'lat':state['store']['lat'],'lon':state['store']['lon']} if state['location_ok'] else None),'pickup_promised':d=='ELIGIBLE'}

def run_deterministic(request: dict) -> dict:
    state={'request':request}
    for fn in (validate_address,resolve_location,check_pickup): state.update(fn(state))
    return decide(state)

def build_graph():
    """Optional LangGraph integration. The exact same decision functions run in tests."""
    from langgraph.graph import StateGraph, START, END
    graph=StateGraph(State)
    for name,fn in [('validate_address',validate_address),('resolve_location',resolve_location),('check_pickup',check_pickup)]: graph.add_node(name,fn)
    graph.add_node('decide', lambda state: {'result':decide(state)})
    graph.add_edge(START,'validate_address'); graph.add_edge('validate_address','resolve_location')
    graph.add_edge('resolve_location','check_pickup'); graph.add_edge('check_pickup','decide'); graph.add_edge('decide',END)
    return graph.compile()

if __name__=='__main__':
    import json
    example={'country':'AE','city':'Dubai','district':'Downtown','store_id':'UAE-DXB-01','order_status':'READY_FOR_PICKUP'}
    print(json.dumps(run_deterministic(example),indent=2))
