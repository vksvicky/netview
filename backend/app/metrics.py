from prometheus_client import CollectorRegistry, Counter, Gauge


# Shared Prometheus registry
registry = CollectorRegistry()


# HTTP metrics
http_requests_total = Counter(
    "netview_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)


# Discovery metrics
discovered_devices_gauge = Gauge(
    "netview_discovered_devices_total",
    "Number of discovered devices",
    registry=registry,
)


# Interface metrics (labels: device_id, if_index)
if_in_octets = Gauge(
    "netview_if_in_octets",
    "Interface inbound octets",
    ["device_id", "if_index"],
    registry=registry,
)
if_out_octets = Gauge(
    "netview_if_out_octets",
    "Interface outbound octets",
    ["device_id", "if_index"],
    registry=registry,
)
if_in_errors = Gauge(
    "netview_if_in_errors",
    "Interface inbound errors",
    ["device_id", "if_index"],
    registry=registry,
)
if_out_errors = Gauge(
    "netview_if_out_errors",
    "Interface outbound errors",
    ["device_id", "if_index"],
    registry=registry,
)
if_in_discards = Gauge(
    "netview_if_in_discards",
    "Interface inbound discards",
    ["device_id", "if_index"],
    registry=registry,
)
if_out_discards = Gauge(
    "netview_if_out_discards",
    "Interface outbound discards",
    ["device_id", "if_index"],
    registry=registry,
)


# System metrics (labels: device_id)
cpu_utilization = Gauge(
    "netview_device_cpu_utilization_percent",
    "Device CPU utilization percentage",
    ["device_id"],
    registry=registry,
)
mem_utilization = Gauge(
    "netview_device_mem_utilization_percent",
    "Device memory utilization percentage",
    ["device_id"],
    registry=registry,
)


