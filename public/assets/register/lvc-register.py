#!/usr/bin/env python3
"""Illustrative annual postcode Location Rental Value Register (stdlib only)."""
from __future__ import annotations

import argparse, csv, hashlib, math, random, statistics
from collections import defaultdict
from pathlib import Path

RES_TYPES = ("flat", "terraced", "semi", "detached")
BED_BANDS = ("1", "2", "3", "4+")
SCHEDULE_TYPES = {
    "residential": RES_TYPES,
    "commercial": ("retail", "office", "industrial", "other"),
    "agriculture": ("arable", "pasture", "mixed", "horticulture", "other"),
    "forestry": ("commercial_woodland", "amenity_conservation", "other"),
}

def normalise_postcode(s): return " ".join(str(s).upper().split())
def fnum(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default

def quantile(values, q):
    v = sorted(values)
    if not v: return 0.0
    x = (len(v)-1)*q; lo = int(math.floor(x)); hi = int(math.ceil(x))
    return v[lo] if lo == hi else v[lo]*(hi-x)+v[hi]*(x-lo)

def weighted_median(rows):
    rows = sorted(rows, key=lambda x:x[0]); total=sum(w for _,w in rows); acc=0
    for value, weight in rows:
        acc += weight
        if acc >= total/2: return value
    return rows[-1][0]

def distance_km(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,(a[0],a[1],b[0],b[1]))
    h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 12742*math.asin(min(1,math.sqrt(h)))

def read_csv(path):
    with open(path,newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def class_key(r):
    schedule=r.get("use_class","residential").lower()
    typ=r.get("property_type","other").lower()
    bed=r.get("bedroom_band","") if schedule=="residential" else ""
    return schedule,typ,bed

def svg_outputs(rows,outdir,year):
    vals=[fnum(r["index_level"]) for r in rows if r["use_class"]=="residential" and r["property_type"]=="semi" and r["bedroom_band"]=="3"]
    bins=[100+i*25 for i in range(12)]; counts=[0]*len(bins)
    for v in vals: counts[min(len(bins)-1,max(0,int((v-100)//25)))] += 1
    mx=max(counts or [1]); bars=[]
    for i,c in enumerate(counts):
        x=55+i*48; h=220*c/max(mx,1); bars.append(f'<rect x="{x}" y="{280-h:.1f}" width="34" height="{h:.1f}" fill="#237a57"/><text x="{x+17}" y="300" text-anchor="middle" font-size="10">{bins[i]}</text>')
    chart=f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="340"><rect width="100%" height="100%" fill="white"/><text x="30" y="28" font-family="sans-serif" font-size="18">Residential location index distribution — {year}</text><line x1="45" y1="280" x2="650" y2="280" stroke="#333"/>{''.join(bars)}<text x="350" y="326" text-anchor="middle" font-family="sans-serif" font-size="12">Index (floor location = 100)</text></svg>'''
    (outdir/f"distribution_{year}.svg").write_text(chart,encoding="utf-8")
    pts=[]
    for r in rows:
        if r["use_class"]!="residential" or r["property_type"]!="semi" or r["bedroom_band"]!="3": continue
        lon,lat=fnum(r["longitude"]),fnum(r["latitude"]); x=60+(lon+8.7)/10.6*430; y=40+(60.9-lat)/11.1*650
        v=fnum(r["index_level"]); colour="#1b5e20" if v<150 else "#f9a825" if v<225 else "#b71c1c"
        pts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{colour}" opacity=".75"><title>{r["postcode"]}: {v:.1f}</title></circle>')
    map_svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="740"><rect width="100%" height="100%" fill="#f7faf8"/><text x="25" y="25" font-family="sans-serif" font-size="18">Illustrative UK postcode index map — {year}</text><path d="M245 55 L300 85 285 150 325 205 300 270 350 325 315 390 355 450 300 535 260 610 205 680 150 625 175 545 135 475 175 405 140 335 190 270 175 190 215 135 Z" fill="#dfe9e3" stroke="#789083"/>{''.join(pts)}<text x="25" y="720" font-family="sans-serif" font-size="11">Green &lt;150 · amber 150–224 · red 225+ · points are postcode centroids</text></svg>'''
    (outdir/f"map_{year}.svg").write_text(map_svg,encoding="utf-8")

def build(args):
    pcs=read_csv(args.postcodes); ev=read_csv(args.evidence)
    pcmap={normalise_postcode(r["postcode"]):r for r in pcs}
    observations=defaultdict(list)
    for r in ev:
        p=normalise_postcode(r.get("postcode","")); area=fnum(r.get("floor_area_sqm")); rent=fnum(r.get("annual_rent_gbp")); yr=int(fnum(r.get("year")))
        if p not in pcmap or area<=0 or rent<=0 or yr<args.year-1 or yr>args.year: continue
        schedule,typ,bed=class_key(r)
        if schedule not in SCHEDULE_TYPES or typ not in SCHEDULE_TYPES[schedule]: continue
        observations[(p,schedule,typ,bed)].append((rent/area,max(.05,fnum(r.get("quality_weight"),1))))
    direct={k:weighted_median(v) for k,v in observations.items()}
    classes=sorted(set((s,t,b) for _,s,t,b in direct))
    if not classes: raise SystemExit("No valid evidence rows for the requested year/window")
    coords={p:(fnum(r["latitude"]),fnum(r["longitude"])) for p,r in pcmap.items()}
    results=[]
    for s,t,b in classes:
        known={p:v for (p,ss,tt,bb),v in direct.items() if (ss,tt,bb)==(s,t,b)}
        known_values=list(known.values()); lo=quantile(known_values,args.floor_quantile); hi=quantile(known_values,args.ceiling_quantile)
        missing=sorted(set(pcmap)-set(known)); even={p: lo+(hi-lo)*(i+1)/(len(missing)+1) for i,p in enumerate(missing)}
        for p,meta in pcmap.items():
            n=len(observations.get((p,s,t,b),[])); donors=[]
            if p in known:
                raw=known[p]; grade="A" if n>=args.min_direct else "B"; method="direct" if grade=="A" else "direct_sparse"
            else:
                nearest=sorted(((distance_km(coords[p],coords[q]),q,v) for q,v in known.items() if q!=p),key=lambda x:x[0])[:args.neighbours]
                nearest=[x for x in nearest if x[0]<=args.max_distance_km]
                if nearest:
                    weights=[1/max(d,1)**args.distance_power for d,_,_ in nearest]; raw=sum(v*w for w,(_,_,v) in zip(weights,nearest))/sum(weights)
                    donors=[q for _,q,_ in nearest]; grade="C"; method="spatial"
                else: raw=even[p]; grade="D"; method="even_spread"
            bounded=min(max(raw,lo),hi); idx=100*bounded/lo if lo else 100
            results.append({"year":args.year,"postcode":p,"nation":meta.get("nation",""),"region":meta.get("region",""),"latitude":meta["latitude"],"longitude":meta["longitude"],"use_class":s,"property_type":t,"bedroom_band":b,"annual_rent_per_sqm":f"{raw:.4f}","floor_rent_per_sqm":f"{lo:.4f}","ceiling_rent_per_sqm":f"{hi:.4f}","bounded_rent_per_sqm":f"{bounded:.4f}","location_excess_over_floor_per_sqm":f"{bounded-lo:.4f}","index_level":f"{idx:.4f}","evidence_count":n,"confidence_grade":grade,"method":method,"donor_postcodes":"|".join(donors),"reassessment_factor":""})
    if args.previous_register:
        prev={(normalise_postcode(r["postcode"]),r["use_class"],r["property_type"],r.get("bedroom_band","")):fnum(r["index_level"]) for r in read_csv(args.previous_register)}
        for r in results:
            old=prev.get((r["postcode"],r["use_class"],r["property_type"],r["bedroom_band"]))
            r["reassessment_factor"]=f"{fnum(r['index_level'])/old:.6f}" if old else ""
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    fields=list(results[0]); write_csv(out/f"register_{args.year}.csv",results,fields)
    summary=[]
    for key in classes:
        rr=[r for r in results if (r["use_class"],r["property_type"],r["bedroom_band"])==key]
        summary.append({"year":args.year,"use_class":key[0],"property_type":key[1],"bedroom_band":key[2],"postcodes":len(rr),"direct_A":sum(r["confidence_grade"]=="A" for r in rr),"modelled_B":sum(r["confidence_grade"]=="B" for r in rr),"spatial_C":sum(r["confidence_grade"]=="C" for r in rr),"even_spread_D":sum(r["confidence_grade"]=="D" for r in rr),"floor":rr[0]["floor_rent_per_sqm"],"ceiling":rr[0]["ceiling_rent_per_sqm"]})
    write_csv(out/f"summary_{args.year}.csv",summary,list(summary[0])); svg_outputs(results,out,args.year)
    manifest={"register":f"register_{args.year}.csv","rows":len(results),"sha256":hashlib.sha256((out/f"register_{args.year}.csv").read_bytes()).hexdigest()}
    (out/f"manifest_{args.year}.txt").write_text("\n".join(f"{k}={v}" for k,v in manifest.items())+"\n",encoding="utf-8")
    print(f"Wrote {len(results):,} register rows to {out}")

def demo(args):
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); random.seed(args.seed)
    cities=[("AB10 1AB",57.15,-2.10,"Scotland","Aberdeen"),("BT1 5GS",54.60,-5.93,"Northern Ireland","Belfast"),("B1 1AA",52.48,-1.90,"England","Birmingham"),("CF10 1EP",51.48,-3.18,"Wales","Cardiff"),("EH1 1YZ",55.95,-3.19,"Scotland","Edinburgh"),("G1 1XW",55.86,-4.25,"Scotland","Glasgow"),("L1 8JQ",53.40,-2.98,"England","Liverpool"),("LS1 4DY",53.80,-1.55,"England","Leeds"),("M1 1AE",53.48,-2.24,"England","Manchester"),("NE1 4LP",54.97,-1.61,"England","Newcastle"),("NG1 2GB",52.95,-1.15,"England","Nottingham"),("NR1 1AA",52.63,1.30,"England","Norwich"),("OX1 1AA",51.75,-1.26,"England","Oxford"),("PL1 1AA",50.37,-4.14,"England","Plymouth"),("SA1 1AA",51.62,-3.94,"Wales","Swansea"),("SO14 7DW",50.90,-1.40,"England","Southampton"),("TR1 1AA",50.26,-5.05,"England","Truro"),("WC2N 5DU",51.51,-0.13,"England","London"),("YO1 7HH",53.96,-1.08,"England","York")]
    pcs=[{"postcode":p,"latitude":lat,"longitude":lon,"nation":n,"region":r} for p,lat,lon,n,r in cities]
    pf=out/"example_postcodes.csv"; write_csv(pf,pcs,list(pcs[0])); evidence=[]
    for ci,(p,lat,lon,n,r) in enumerate(cities):
        location=55+ci*5.5
        for typ_i,typ in enumerate(RES_TYPES):
            for bed_i,bed in enumerate(BED_BANDS):
                if (ci+typ_i+bed_i)%4==0: continue
                for j in range(6):
                    area=(45+bed_i*22)*(1+typ_i*.08); rate=location*(1+typ_i*.035)*(1+random.uniform(-.08,.08))
                    evidence.append({"postcode":p,"use_class":"residential","property_type":typ,"bedroom_band":bed,"floor_area_sqm":f"{area:.1f}","annual_rent_gbp":f"{area*rate:.2f}","year":args.year,"source":"synthetic_demo","quality_weight":"1"})
        for sched,typ,rate in (("commercial","office",location*.8),("agriculture","mixed",.025+ci*.001),("forestry","commercial_woodland",.012+ci*.0005)):
            if ci%3: evidence.append({"postcode":p,"use_class":sched,"property_type":typ,"bedroom_band":"","floor_area_sqm":"10000","annual_rent_gbp":f"{rate*10000:.2f}","year":args.year,"source":"synthetic_demo","quality_weight":"0.7"})
    ef=out/"example_evidence.csv"; write_csv(ef,evidence,list(evidence[0])); args.postcodes=str(pf); args.evidence=str(ef); args.previous_register=None; build(args)

def parser():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="command",required=True)
    for name in ("build","demo"):
        q=sub.add_parser(name); q.add_argument("--year",type=int,default=2026); q.add_argument("--output-dir",default="output")
        q.add_argument("--floor-quantile",type=float,default=.10); q.add_argument("--ceiling-quantile",type=float,default=.90); q.add_argument("--min-direct",type=int,default=5); q.add_argument("--neighbours",type=int,default=6); q.add_argument("--max-distance-km",type=float,default=120); q.add_argument("--distance-power",type=float,default=1.5)
    b=sub.choices["build"]; b.add_argument("--postcodes",required=True); b.add_argument("--evidence",required=True); b.add_argument("--previous-register")
    d=sub.choices["demo"]; d.add_argument("--seed",type=int,default=42)
    return p

def main():
    args=parser().parse_args()
    if not 0<=args.floor_quantile<args.ceiling_quantile<=1: raise SystemExit("Quantiles must satisfy 0 <= floor < ceiling <= 1")
    (demo if args.command=="demo" else build)(args)

if __name__=="__main__": main()
