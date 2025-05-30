#!/usr/bin/env python3

import click
import glob
import pickle
import tqdm
from pathlib import Path
import pandas as pd

COVTOOLS = ["profcov", "acvtool"]
TOOLS = ["time", "monkey", "droidbot", "fastbot"]
SKIPNUM=50 # skip every x probe hits to make plots manageable


# prepare directories
for covtool in COVTOOLS:
    p = Path("_cache") / covtool 
    p.mkdir(parents=True, exist_ok=True)


class CacheNotFoundError(Exception):
    pass


# profile coverage cache names
def cachename_for_profcov(tool: str):
    return Path("_cache/") / "profcov" / f"{tool}.pickle"

def cachename_for_acvtool(tool: str):
    return Path("_cache/") / "acvtool" / f"{tool}.pickle"


def _uprobes_to_total_and_cumulative(hit_uprobes):
    toplot_unique = []
    toplot_total = []
    _known_offs = set()
    _total_probes = 0

    for _, ts, offs in hit_uprobes:
        _total_probes+=1
        if _total_probes % SKIPNUM == 1:
            # total number is a lot, so we batch it in 50s steps
            toplot_total.append((ts, _total_probes))
        if offs not in _known_offs:
            _known_offs.add(offs)
            toplot_unique.append((ts, len(_known_offs)))
    
    tsses_total, total = zip(*toplot_total)
    tsses_cumulative, cumulative = zip(*toplot_unique)
    return tsses_total, total, tsses_cumulative, cumulative

def read_all_results_profcov(tool):
    resglob = f"../../dynamic/profcov/{tool}/results_{tool}-*/**/result.pickle"
    all_tsses = []
    all_cumulative_total = []
    all_cumulative_relative = []
    all_total = []
    all_appids = []
    all_runids = []
    for resfile in tqdm.tqdm(glob.glob(resglob)):
        try:
            apkid = str(resfile).split('/')[-2]
            runid = int(str(resfile).split('/')[-3].split('-')[1])
            with open(resfile, 'rb') as f:
                profile_info, offsets_info, trace_info, traced_activities, hit_uprobes = pickle.load(f)
            if len(hit_uprobes) == 0:
                continue
            tsses_total, total, tsses_cumulative, cumulative = _uprobes_to_total_and_cumulative(hit_uprobes)
            num_tracepoints_set = len(trace_info)

            # add cumulative data
            all_tsses.extend(tsses_cumulative)
            all_cumulative_total.extend(cumulative)
            all_cumulative_relative.extend([float(c)/num_tracepoints_set for c in cumulative])
            all_appids.extend([apkid for _ in range(len(cumulative))])
            all_runids.extend([runid for _ in range(len(cumulative))])
            all_total.extend([pd.NA for _ in range(len(cumulative))])
            
            # add total data
            all_tsses.extend(tsses_total)
            all_total.extend(total)
            all_appids.extend([apkid for _ in range(len(total))])
            all_runids.extend([runid for _ in range(len(total))])
            all_cumulative_total.extend([pd.NA for _ in range(len(total))])
            all_cumulative_relative.extend([pd.NA for _ in range(len(total))])
        except Exception as e:
            print(f"ERR on {resfile}")
            raise e
    
    df = pd.DataFrame({
            'seconds since first probe hit': all_tsses,
            'cumulative number of unique probes hit': all_cumulative_total,
            'profile coverage': all_cumulative_relative,
            'cumulative number of non-unique probes hit': all_total,
            'app id': all_appids,
            'run id': all_runids
        })
    return df

def _read_from_cache(tool, cachepath):
    print(f"loading '{tool}' from cache!")
    results = pd.read_pickle(cachepath)
    print(f" loaded '{tool}' results for {results['app id'].nunique()} apps and {results['run id'].nunique()} runs from cache!")
    return results

def read_from_cache_or_generate_profcov(tool):
    cachepath = cachename_for_profcov(tool)
    if not cachepath.exists():
        print(f"no cache found, loading '{tool}' from raw data")
        results = read_all_results_profcov(tool)
        if results['app id'].nunique() != 0:
            results.to_pickle(cachepath)
        else:
            print("error: raw data contained 0 results")
    else:
        results = _read_from_cache(tool, cachepath)
    return results

def read_from_cache_profcov(tool):
    cachepath = cachename_for_profcov(tool)
    if not cachepath.exists():
        print(f"ERROR: no cache found for {tool}")
        raise CacheNotFoundError()
    else:
        results = _read_from_cache(tool, cachepath)
    return results

def read_all_results_acvtool(tool):
    appids = []
    runids = []
    hits = []
    totals = []
    coverages = []
    tools = []
    for resfile in tqdm.tqdm(glob.glob(f"../../dynamic/acvtool/{tool}/wd_{tool}-*/**/report/main_index.html")):
        appid = str(resfile).split('/')[-3]
        resid = int(str(resfile).split('/')[-4].split('-')[1])
        with open(resfile, encoding='utf-8', errors='backslashreplace') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if '<td>Total' in line:
                    resline = lines[i+1]
        linehit, linetotal = resline.split('>')[1].split('<')[0].split(' of ')
        appids.append(appid)
        runids.append(resid)
        hits.append(int(linehit))
        totals.append(int(linetotal))
        coverages.append(float(int(linehit))/int(linetotal))
        tools.append(tool)

    df = pd.DataFrame({
            'app id': appids,
            'run id': runids,
            'code coverage': coverages,
            'total methods': totals,
            'hit methods': hits,
            'tool': tools,
        })
    return df

def read_from_cache_or_generate_acvtool(tool):
    cachepath = cachename_for_acvtool(tool)
    if not cachepath.exists():
        print(f"no cache found, loading '{tool}' from raw data")
        results = read_all_results_acvtool(tool)
        if results['app id'].nunique() != 0:
            results.to_pickle(cachepath)
        else:
            print("error: raw data contained 0 results")
    else:
        results = _read_from_cache(tool, cachepath)
    return results

def read_from_cache_acvtool(tool):
    cachepath = cachename_for_acvtool(tool)
    if not cachepath.exists():
        print(f"ERROR: no cache found for {tool}")
        raise CacheNotFoundError()
    else:
        results = _read_from_cache(tool, cachepath)
    return results


@click.command()
@click.option("--covtool", type=click.Choice(["all"] + COVTOOLS), default="all")
@click.option("--tool", type=click.Choice(["all"] + TOOLS), default="all")
def main(covtool, tool):
    """
    computing profile coverage caches takes ~15GB and 5m per tool,
        fastbot more like ~30GB and 30min and takes longer
    """
    if covtool == "all":
        covtools = COVTOOLS
    else:
        covtools = [covtool]
    
    if tool == "all":
        tools = TOOLS
    else:
        tools = [tool]
    
    if "profcov" in covtools:
        print('reading profcov')
        results_profcov = {}
        for tool in tools:
            results_profcov[tool] = read_from_cache_or_generate_profcov(tool)
        print("reading done")


        print('no profile coverage should be above 1.0:')
        for tool in tools:
            r = results_profcov[tool]
            s = r[r['profile coverage'] > 1.0]['app id'].unique()
            print(tool, s)
            if len(s) > 0:
                print(r[r['profile coverage'] > 1.0][['app id', 'run id', 'profile coverage']])
        print('')
    
    if "acvtool" in covtools:
        print('reading acvtool')
        results_acvtool = {}
        for tool in tools:
            results_acvtool[tool] = read_from_cache_or_generate_acvtool(tool)
        print("reading done")

        print('no code coverage should be above 1.0:')
        for tool in tools:
            r = results_acvtool[tool]
            print(tool, r[r['code coverage'] > 1.0]['app id'].unique())
        print('')



if __name__ == "__main__":
    main()
