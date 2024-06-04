#!/bin/bash

source /home/seclab/.profile
source /home/seclab/.bashrc

pyenv activate aot-profiles

pwd

cd /home/seclab/code/heartoftheandroid/experiments/daily_apk_dm_scrape && make full-daily-run
