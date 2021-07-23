# CorePool Exporter
The script scrape CorePool pages for information, and export to prometheus metrics format.

This is used with the Node Exporter Textfile Collector. You have to setup your own stack.

## Installation

Create a virtual environment
```sh
python3 -m venv .venv
```

Install dependencies
```sh
source .venv/bin/activate
pip3 install -r requirements.txt
```

## Usage
Rename `config.py.example` to `config.py`
```sh
cp config.py.example config.py
```

Fill your Core Pool **username** and **password** in `config.py`

Just run the script, it will output a `corepool.prom` file.
```sh
python3 corepool.py
```

### Add to Prometheus Textfile Collector
Add the `--collector.textfile.directory` parameter to the node export

```
/usr/local/bin/node_exporter --collector.textfile.directory /path/to/corepool.prom/
```

## Metrics

```py
# HELP corepool_unpaid_balance unpaid XCH balance
# TYPE corepool_unpaid_balance gauge
corepool_unpaid_balance 0.270885
# HELP corepool_plot_points current accumulate plot points
# TYPE corepool_plot_points gauge
corepool_plot_points 405000.0
# HELP corepool_plot_points_percent plot points share percentage
# TYPE corepool_plot_points_percent gauge
corepool_plot_points_percent 0.020282
# HELP corepool_total_plots account total plots
# TYPE corepool_total_plots gauge
corepool_total_plots 1000.0
# HELP corepool_blocks_found current accumulate blocks found
# TYPE corepool_blocks_found gauge
corepool_blocks_found 25.0
# HELP corepool_farmer_status 1 if the farmer is online
# TYPE corepool_farmer_status gauge
corepool_farmer_status{farmer="MyCorePoolFarmer1"} 1.0
corepool_farmer_status{farmer="MyCorePoolFarmer2"} 0.0
# HELP corepool_active_farmers pool total active farmers
# TYPE corepool_active_farmers gauge
corepool_active_farmers 11048.0
# HELP corepool_farmer_plots pool total plot count
# TYPE corepool_farmer_plots gauge
corepool_farmer_plots 4.453431e+06
# HELP corepool_total_pool_size_pib pool total plot size in PiB
# TYPE corepool_total_pool_size_pib gauge
corepool_total_pool_size_pib 441.07
```

## To-Do

- [x] Scrape farmer online status
- [x] Scrape the plot point percentage in the pool
- [x] Use **Prometheus Python Client** to export metrics
