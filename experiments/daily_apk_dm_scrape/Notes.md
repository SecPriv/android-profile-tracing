# Notes

run with make and parallel to use multiple devices and log fails there


1. enter serial numbers
2. dump pre-installed apps per phone

each day, for each app:
    1. install or update app -> method to be implemented without update_all
    2. grab apk+dm
        - put on storage server
    3. uninstall if possible else uninstalls the updates



- install or update


## env

### crontab entry:

`0 4 * * * /home/seclab/code/heartoftheandroid/experiments/daily_apk_dm_scrape/cronwrapper.sh > /home/seclab/cron.log 2>&1`

every morning at 04:00
