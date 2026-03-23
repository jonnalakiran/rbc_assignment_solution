# RBC Assignment Solution



This repository contains a complete solution for all three assignment sections.





#### Project structure



```text
rbc\\\_assignment\\\_solution/
├── README.md
├── requirements.txt
├── docs/
│    └── assignment\\\_summary.md
├── test1\\\_service\\\_monitor/
│   ├── service\\\_monitor.py
│   ├── app.py
│   ├── sample\\\_payloads/
│   │   ├── httpd-status-sample.json
│   │   ├── rabbitmq-status-sample.json
│   │   └── postgresql-status-sample.json
│   └── output/
├── test2\\\_ansible/
│   ├── inventory.ini
│   └── assignment.yml
└── test3\\\_sales\\\_filter/
    ├── sales\\\_filter.py
    ├── assignment data (1).csv
    └── filtered\\\_properties\\\_below\\\_avg\\\_price\\\_per\\\_sqft.csv
```

#### Assumptions



##### Test 1



* `rbcapp1` depends on three Linux services:

  * `httpd`
  * `rabbitmq-server`
  * `postgresql`
* If all three services are up, application status is `UP`; otherwise it is `DOWN`.
* The monitoring script writes one JSON file per service using the required naming pattern:
`{serviceName}-status-{timestamp}.json`
* Elasticsearch index name used by the REST service: `service-health`
* The REST API is implemented with Flask for simplicity.



##### Test 2



* Hosts:

  * `host1` runs `httpd`
  * `host2` runs `rabbitmq-server`
  * `host3` runs `postgresql`
* The Ansible playbook supports:

  * `action=verify\\\_install`
  * `action=check-disk`
  * `action=check-status`
* For installation illustration, the playbook installs `httpd` only on `host1` if missing.
* Alert email in the playbook uses `ops.alerts@example.com` as the recipient.
* `check-status` uses the REST endpoint from Test 1.



##### Test 3



* Rows with `sq\\\_\\\_ft <= 0` are excluded from price-per-foot calculations to avoid invalid division.
* Average price per square foot is calculated over valid rows only.
* Output CSV contains only properties sold for **less than** the computed average price per square foot.



### Execution instructions



##### 1\) Install Python dependencies



```bash
pip install -r requirements.txt
```

##### Test 1: Monitor services and REST API



###### Generate JSON status files



```bash
cd test1\\\_service\\\_monitor
python service\\\_monitor.py
```

Generated files will be written to:

```text
test1\\\_service\\\_monitor/output/
```

##### Run the Flask API



```bash
cd test1\\\_service\\\_monitor
python app.py
```

API endpoints:

* `POST /add`
* `GET /healthcheck`
* `GET /healthcheck/<serviceName>`



##### Example requests



Insert a status document:

```bash
curl -X POST http://127.0.0.1:5000/add   -H "Content-Type: application/json"   -d @output/httpd-status-<timestamp>.json
```

Get application health:

```bash
curl http://127.0.0.1:5000/healthcheck
```

Get one service health:

```bash
curl http://127.0.0.1:5000/healthcheck/httpd
```

##### Environment variables for Elasticsearch



Optional environment variables:

```bash
export ELASTICSEARCH\\\_HOST=http://localhost:9200
export ELASTICSEARCH\\\_INDEX=service-health
```

##### Test 2: Ansible 

##### 

##### Verify install



```bash
cd test2\\\_ansible
ansible-playbook assignment.yml -i inventory.ini -e action=verify\\\_install
```

##### Check disk usage



```bash
ansible-playbook assignment.yml -i inventory.ini -e action=check-disk
```

##### Check application/service status



```bash
ansible-playbook assignment.yml -i inventory.ini -e action=check-status
```

##### Test 3: Sales filtering



```bash
cd test3\\\_sales\\\_filter
python sales\\\_filter.py
```

Output file:

```text
filtered\\\_properties\\\_below\\\_avg\\\_price\\\_per\\\_sqft.csv
```

##### Actual Test 3 result from the provided CSV



* Valid rows used for average price/ft calculation: 814
* Average price per square foot: 145.6733
* Output rows below average price per square foot: 470



##### Notes



* The monitoring and Flask service are production-friendly starter implementations with input validation and error handling.
* In a real environment, Ansible email settings may need SMTP server details or delegation to a mail relay host.
* If Elasticsearch is not available during local testing, the Flask API still validates payloads and will return a connection error message instead of silently failing.

