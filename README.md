# CorePool Scraper
The script scrape CorePool pages for information, and export to prometheus metrics format.

This is used with the Node Exporter Textfile Collector. You have to setup your own stack.

## Installation

Create a virtual environment
```sh
python3 -m venv .venv
```


## Usage
Rename `config.py.example` to `config.py`
```sh
cp config.py.example config.py
```

Fill your Core Pool **username** and **password** in `config.py`

Run the script and output to a `*.prom` file.
```sh
python3 main.py > corepool_metrics.prom
```

### Add to Prometheus Textfile Collector
Add the `--collector.textfile.directory` parameter to the node export

```
/usr/local/bin/node_exporter --collector.textfile.directory /path/to/corepool_metrics.prom/
```

## Metrics

```
# HELP corepool_unpaid_balance CorePool metric for unpaid_balance
# TYPE corepool_unpaid_balance gauge
corepool_unpaid_balance 0.217829
# HELP corepool_plot_points CorePool metric for plot_points
# TYPE corepool_plot_points gauge
corepool_plot_points 570000
# HELP corepool_total_plots CorePool metric for total_plots
# TYPE corepool_total_plots gauge
corepool_total_plots 1000
# HELP corepool_blocks_found CorePool metric for blocks_found
# TYPE corepool_blocks_found gauge
corepool_blocks_found 18
# HELP corepool_active_farmers CorePool metric for active_farmers
# TYPE corepool_active_farmers gauge
corepool_active_farmers 10765
# HELP corepool_farmer_plots CorePool metric for farmer_plots
# TYPE corepool_farmer_plots gauge
corepool_farmer_plots 4297895
# HELP corepool_total_pool_size_pib CorePool metric for total_pool_size_pib
# TYPE corepool_total_pool_size_pib gauge
corepool_total_pool_size_pib 422.65
```

## To-Do

- [ ] Scrape farmer online status
- [ ] Scrape the plot point percentage in the pool
