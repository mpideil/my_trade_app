This is a python trade app to be used with cron as a launch scheduler and influxdb as DB

# Installation

**Tools**
sudo aptitude install git man
sudo apt install python3-pip
ls /usr/bin/python*
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2
python -m pip install influxdb-client
python -m pip install pandas
python -m pip install yfinance
python -m pip install matplotlib
python -m pip install seaborn


** TA-LIB**
Mac OS X
```
$ brew install ta-lib
```
Linux
Download http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz and:
```
$ untar and cd
$ ./configure --prefix=/usr
$ make
$ sudo make install
```

```
python -m pip install ta-lib
```


```
sudo aptitude install docker influxdb-client
```

***Custom influxdb-client***
```
/Users/xxx/.pyenv/versions/3.8.2/lib/python3.8/site-packages/influxdb_client/client/write/point.py
8a9
> import numpy as np
161c162
<         elif isinstance(value, int ) and not isinstance(value, bool):
---
>         elif isinstance(value, np.integer) and not isinstance(value, bool):
```

**Docker**
sudo apt install apt-transport-https ca-certificates curl gnupg2 software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
sudo apt update
apt-cache policy docker-ce
sudo apt install docker-ce


**InfluxDB**
sudo mkdir /var/lib/influxdb2/

docker run --rm influxdb:2.0.4 influxd print-config > config.yml

## Modify the default configuration, which will now be available under $PWD.
### Start the InfluxDB container:
````
assets-path: ""
bolt-path: /var/lib/influxdb2/influxd.bolt
e2e-testing: false
engine-path: /var/lib/influxdb2/engine
feature-flags: {}
#http-bind-address: "127.0.0.1:8086"
http-bind-address: :8086
influxql-max-select-buckets: 0
influxql-max-select-point: 0
influxql-max-select-series: 0
key-name: ""
log-level: info
nats-max-payload-bytes: 1048576
nats-port: 4222
no-tasks: false
query-concurrency: 10
query-initial-memory-bytes: 0
query-max-memory-bytes: 0
query-memory-bytes: 9223372036854775807
query-queue-size: 10
reporting-disabled: false
secret-store: bolt
session-length: 60
session-renew-disabled: false
storage-cache-max-memory-size: 1073741824
storage-cache-snapshot-memory-size: 26214400
storage-cache-snapshot-write-cold-duration: 10m0s
storage-compact-full-write-cold-duration: 4h0m0s
storage-compact-throughput-burst: 50331648
storage-max-concurrent-compactions: 0
storage-max-index-log-file-size: 1048576
storage-retention-check-interval: 30m0s
storage-series-file-max-concurrent-snapshot-compactions: 0
storage-series-id-set-cache-size: 0
storage-shard-precreator-advance-period: 30m0s
storage-shard-precreator-check-interval: 10m0s
storage-tsm-use-madv-willneed: false
storage-validate-keys: false
storage-wal-fsync-delay: 0s
store: bolt
testing-always-allow-setup: false
tls-cert: ""
tls-key: ""
tls-min-version: "1.2"
tls-strict-ciphers: false
tracing-type: ""
vault-addr: ""
vault-cacert: ""
vault-capath: ""
vault-client-cert: ""
vault-client-key: ""
vault-client-timeout: 0s
vault-max-retries: 0
vault-skip-verify: false
vault-tls-server-name: ""
vault-token: ""
log-level: "info"
````

```
sudo docker run --name influxdb2 -p 127.0.0.1:8086:8086 -v /var/lib/influxdb2/config.yml:/etc/influxdb2/config.yml:ro --volume /var/lib/influxdb2/:/var/lib/influxdb2/ influxdb:2.0.4 --reporting-disabled

USERNAME=influx_user
PASSWORD=influx_password
ORGANIZATION=org1
BUCKET=bucket1
docker exec -it influxdb2 influx setup --username $USERNAME --password $PASSWORD --org $ORGANIZATION --bucket $BUCKET -r 0
```


### after tests to erase all data :
```
influx delete -o org1 --bucket bucket1 --start '1970-01-01T00:00:00Z' --stop $(date +"%Y-%m-%dT%H:%M:%SZ")
```
### after tests to check all data :
```
influx query 'from(bucket:"bucket1") |> range(start:-3y)'
```

### Cheatsheet
**query**
```
influx query 'from(bucket:"bucket1") |> range(start:-3y)|> drop(columns: ["_start", "_stop"]) |> filter(fn: (r) => r._measurement == "SBUX" and r.kind == "close")'
```
**query with filter**
```
influx query 'from(bucket:"bucket1") |> range(start:-3y)|> filter(fn: (r) => r._measurement == "SBUX" and r.freq == "1h" and r.kind == "close")'
```
**count**
```
influx query 'from(bucket:"bucket1") |> range(start:-3y)|> filter(fn: (r) => r._measurement == "SBUX" and r.freq == "1h")|>count()'
```
**last data in time**
```
influx query 'from(bucket:"bucket1")|> range(start:2021-02-12T18:00:00Z)|> drop(columns: ["_start", "_stop"]) |> filter(fn: (r) => r._measurement == "SBUX" and r.kind == "close" and r.freq == "1h")|>sort(columns: ["_time"])|>tail(n:5)'
```

**list measurements**
```
influx query 'from(bucket:"bucket1")|> range(start:-3y)|> group(columns:["_measurement"])|> distinct(column:"_measurement")'
```



**Git repo**
Create a new UNIX account for the git user.
```
sudo adduser --shell $(which git-shell) git
```

Create a new git repository called "foo".
```
sudo -u git mkdir ~git/foo.git
sudo -u git git -C ~git/foo.git init --bare
```

Clone the repo; you can also use git@example.com:foo.git
```
git clone git@example.com:foo
```

You'll also want to regularly backup your git repositories, in case Something Bad happens. To this end, I've written a small shell script that creates a tar archive for each git directory, and uploads it to a private Google cloud storage bucket if the SHA-1 of the archive has changed since the last time the script ran. I run this via a cron job, set to run once an hour. Here's what my backup script looks like:
```
#!/bin/bash
set -eux
GITDIR=/home/git
BUCKET=gs://my-google-cloud-bucket/git/

# Renice ourselves.
renice -n 10 $$

# Clean things up when we're done.
trap "rm -f /tmp/*.git.tar.xz" EXIT

cd /tmp

# Create tar archives of each git repo.
for proj in ${GITDIR}/*.git; do
    base=$(basename $proj)
    tar -C $GITDIR -cJf ${base}.tar.xz $base
done

upload() {
    if [ $# -gt 0 ]; then
        gsutil -q cp "$@" $BUCKET
    fi
}

# If hashes.txt exists, only upload files whose hashes have changed. Otherwise,
# upload everything.
if [ -f hashes.txt ]; then
    upload $(sha1sum -c hashes.txt 2>/dev/null | awk -F: '/FAILED/ {print $1}')
else
    upload *.git.tar.xz
fi

# Write out the new file hashes for the next run.
sha1sum *.git.tar.xz >hashes.txt
```

** SSH **
```
#influxDB tests
ssh -L 8086:localhost:8086
```

**python**
```
pip install influxdb-client
```

**CheatSheet python**

```
# Get alphavantage data
df = pd.read_csv(f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol=AAPL&interval=60min&slice=year1month2&apikey=1X5VS10ZQI93ROP8')
df = df.iloc[-1:]


# Get influx data
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
token = "xxx"
org = "org1"
bucket = "bucket1"
print("Connect to db")
client = InfluxDBClient(url="http://localhost:8086", token=token,debug=False)
write_api = client.write_api(write_options=SYNCHRONOUS)
query= f'''from(bucket:"bucket1") |> range(start:-2y) |> filter(fn: (r) => r._measurement == "AAPL")|> drop(columns: ["_start", "_stop","_field","_measurement","freq","kind"])|>sort(columns: ["_time"])|>tail(n:2)'''
df_from_influx = client.query_api().query_data_frame(org=org, query=query)
df_from_influx.drop(columns=['table', 'result'],inplace=True)
df_from_influx.rename(columns={"_time": "date", "_value": "close"},inplace=True)
df_from_influx.set_index("date",inplace=True)
df_from_influx = df_from_influx.iloc[-1:]

import pytz
current_timezone = pytz.timezone('US/Eastern')
pd.to_datetime(df_temp['time'])[0].replace(tzinfo=current_timezone)
```

### Put influx data
```
full_json = [{"time": XXXX,"measurement": "AAPL","tags": {"freq": "1h","kind": "close","flavour": "raw"},"fields": {"close": 11112}}]
write_api.write(bucket, org, record=full_json,time_precision='s')
```

### Cron exec
```
** Cron **
2 13-23 * * 1-5  /usr/bin/python /xxxxx/start.py 2>&1 >> /xxx/logs/log| logger -t mycmd
```
