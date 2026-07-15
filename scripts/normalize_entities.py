#!/usr/bin/env python3
"""Normalize Superleads entity names and domains without final identity merging."""
from __future__ import annotations

import argparse, json, re
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse
from _superleads_common import ensure_list, load_json, write_json

LEGAL_SUFFIX_RE=re.compile(r"\b(inc|inc\.|ltd|ltd\.|limited|llc|gmbh|sarl|sas|spa|bv|ag|ab|as|oy|plc|co\.|company|corp\.|corporation)\b", re.I)
SPACE_RE=re.compile(r"\s+")

def normalize_name(name:str)->str:
    lowered=LEGAL_SUFFIX_RE.sub("", name.lower().strip())
    lowered=re.sub(r"[^a-z0-9]+"," ",lowered)
    return SPACE_RE.sub(" ",lowered).strip()

def domain_from_url(url:Any)->str|None:
    if not isinstance(url,str) or not url.strip(): return None
    parsed=urlparse(url if "://" in url else "https://"+url)
    host=(parsed.netloc or parsed.path.split("/")[0]).lower()
    if host.startswith("www."): host=host[4:]
    return host or None

def normalize_graph(graph:dict[str,Any])->dict[str,Any]:
    result=deepcopy(graph); buckets:dict[tuple[str|None,str|None],list[str]]={}
    for entity in ensure_list(result,"entities"):
        if not isinstance(entity,dict): continue
        name=entity.get("name") or entity.get("legal_name") or ""
        normalized=normalize_name(str(name)) if name else ""
        domain=domain_from_url(entity.get("website") or entity.get("domain"))
        entity["normalized_name"]=normalized
        if domain: entity["normalized_domain"]=domain
        buckets.setdefault((normalized or None, domain or None),[]).append(entity.get("entity_id"))
    flags=[]
    for (name,domain),entity_ids in sorted(buckets.items(),key=lambda item:str(item[0])):
        ids=[eid for eid in entity_ids if eid]
        if len(ids)>1:
            flags.append({"type":"possible_duplicate","normalized_name":name,"normalized_domain":domain,"entity_ids":ids,"note":"Normalization suggests possible duplicate only; final identity resolution requires evidence."})
    result.setdefault("identity_review_flags",[]).extend(flags)
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("graph"); p.add_argument("--output",required=True); p.add_argument("--format",choices=["text","json"],default="text"); a=p.parse_args()
    graph=load_json(a.graph)
    if not isinstance(graph,dict): raise SystemExit("Research graph must be a JSON object")
    result=normalize_graph(graph); write_json(a.output,result); flags=result.get("identity_review_flags",[])
    if a.format=="json": print(json.dumps({"ok":True,"identity_review_flag_count":len(flags),"output":a.output},ensure_ascii=False,indent=2))
    else: print(f"normalized graph written: {a.output}\nidentity_review_flags: {len(flags)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
