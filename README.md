# Ping service
ping-service is a simple python service that starts up subproccesses to continously ping servers of your choosing and report the results as prometheus metrics.

## Usage
```
pip install config/requirements.prod.txt
python app/server.py google.com facebook.com bing.com
```

You can access the server on port 5000 at `localhost:5000/metrics`.

This is a sample output:

```
# HELP ping_latency latency in milliseconds
# TYPE ping_latency summary
ping_latency_count{host="google.com"} 3.0
ping_latency_sum{host="google.com"} 56.2
ping_latency_count{host="bing.com"} 3.0
ping_latency_sum{host="bing.com"} 59.2
ping_latency_count{host="facebook.com"} 3.0
ping_latency_sum{host="facebook.com"} 114.29999999999998
# HELP ping_sent_total total number of pings sent
# TYPE ping_sent_total counter
ping_sent_total{host="google.com"} 3.0
ping_sent_total{host="bing.com"} 3.0
ping_sent_total{host="facebook.com"} 3.0
# HELP ping_dropped_total total number of pings dropped
# TYPE ping_dropped_total counter
ping_dropped_total{host="google.com"} 0.0
ping_dropped_total{host="bing.com"} 0.0
ping_dropped_total{host="facebook.com"} 0.0
```

## Docker and kubernetes
Of course the main purpose of this service is to monitor your network inside some container environment. For that reason this repo includes a Dockerfile and a sample k8s manifest that sets up appropriate pod, deployment, service and servicemonitor using [the built images from docker hub](https://hub.docker.com/repository/docker/mkolman/ping-service/).