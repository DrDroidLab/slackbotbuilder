# Grafana Dashboard Check

Go to the URL `<grafana-url>`

## Two queries we need to run:

### Query 1: Container CPU Usage

```
sum(rate(container_cpu_usage_seconds_total{pod=~"<pod-pattern>", instance=~"<instance-pattern>", namespace=~"<namespace>", container_name!="POD", name!=""}[5m])) by (pod)
```

### Query 2: API Success Rate

```
sum(rate(apisix_http_status{code=~"",service=~""}[2m])) / sum(rate(apisix_http_status{code=~"",service=~""}[2m])) * 100
```

## Instructions:

1. Check all the panels in this Grafana Dashboard (SLO Dashboard)
2. Check for any anomalies in the traffic from each window
3. See if there are dips or spikes for the past 24h window
4. Analyze the data and provide insights on:
   - CPU usage patterns
   - API success rates
   - Any unusual traffic patterns
   - Recommendations for optimization

## Placeholder Values:

- `<grafana-url>`: Replace with actual Grafana dashboard URL
- `<pod-pattern>`: Replace with actual pod name pattern
- `<instance-pattern>`: Replace with actual instance pattern
- `<namespace>`: Replace with actual namespace
- `<service-pattern>`: Replace with actual service pattern
