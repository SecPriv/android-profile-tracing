#!/usr/bin/env python3

import glob
from datetime import datetime


profcov_time = None

for startend in glob.glob("profcov/**/_parallel_meta/*.startend"):
    # print(startend)
    with open(startend) as f:
        lines = f.readlines()
        if len(lines) % 2 == 0:
            i = 0
            total_delta = None
            while i < len(lines):
                start = lines[i][7:].strip()
                end = lines[i+1][5:].strip()
            
                # Mon 26 May 2025 17:52:38 CEST
                t_start = datetime.strptime(start, "%a %d %b %Y %H:%M:%S %Z")
                t_end   = datetime.strptime(end,   "%a %d %b %Y %H:%M:%S %Z")

                t_delta = t_end - t_start
                if not total_delta:
                    total_delta = t_delta
                else:
                    total_delta += t_delta
                i+=2
            if profcov_time:
                profcov_time += total_delta
            else:
                profcov_time = total_delta
        else:
            print(f"{startend} has not multiple of 2 lines!")

print(f"provcov total time: {profcov_time}")

acv_time = None

for startend in glob.glob("acvtool/**/_parallel_meta/*.startend"):
    # print(startend)
    with open(startend) as f:
        lines = f.readlines()
        if len(lines) % 2 == 0:
            i = 0
            total_delta = None
            while i < len(lines):
                start = lines[i][7:].strip()
                end = lines[i+1][5:].strip()
            
                # Mon 26 May 2025 17:52:38 CEST
                t_start = datetime.strptime(start, "%a %d %b %Y %H:%M:%S %Z")
                t_end   = datetime.strptime(end,   "%a %d %b %Y %H:%M:%S %Z")

                t_delta = t_end - t_start
                if not total_delta:
                    total_delta = t_delta
                else:
                    total_delta += t_delta
                i+=2
            if acv_time:
                acv_time += total_delta
            else:
                acv_time = total_delta
        else:
            print(f"{startend} has not multiple of 2 lines!")

print(f"acv total time: {acv_time}")
