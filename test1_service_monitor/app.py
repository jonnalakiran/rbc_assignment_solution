import os
from datetime import datetime
from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch

app = Flask(__name__)

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "service-health")

SERVICE_MAP = {
    "httpd": "httpd",
    "rabbitmq": "rabbitmq-server",
    "rabbitmq-server": "rabbitmq-server",
    "postgresql": "postgresql",
}

REQUIRED_FIELDS = {"service_name", "service_status", "host_name"}

es = Elasticsearch(ELASTICSEARCH_HOST)


def normalize_service_name(name: str) -> str:
    return SERVICE_MAP.get(name.lower(), name.lower())


def latest_documents():
    query = {
        "size": 100,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {"match_all": {}},
    }
    response = es.search(index=ELASTICSEARCH_INDEX, body=query)
    return response.get("hits", {}).get("hits", [])


def latest_status_by_service():
    docs = latest_documents()
    latest = {}
    for hit in docs:
        source = hit.get("_source", {})
        service = normalize_service_name(source.get("service_name", ""))
        if service and service not in latest:
            latest[service] = source
    return latest


@app.route("/add", methods=["POST"])
def add_document():
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        return jsonify({"error": f"Missing required fields: {sorted(missing)}"}), 400

    if payload["service_status"] not in {"UP", "DOWN"}:
        return jsonify({"error": "service_status must be UP or DOWN"}), 400

    payload.setdefault("@timestamp", datetime.utcnow().isoformat(timespec="seconds") + "Z")

    try:
        result = es.index(index=ELASTICSEARCH_INDEX, document=payload)
        return jsonify({
            "message": "Document inserted successfully",
            "index": ELASTICSEARCH_INDEX,
            "document_id": result.get("_id"),
        }), 201
    except Exception as exc:
        return jsonify({"error": f"Failed to write to Elasticsearch: {str(exc)}"}), 500


@app.route("/healthcheck", methods=["GET"])
def application_health():
    try:
        latest = latest_status_by_service()
        expected_services = ["httpd", "rabbitmq-server", "postgresql"]

        service_statuses = {
            svc: latest.get(svc, {}).get("service_status", "DOWN")
            for svc in expected_services
        }
        app_status = "UP" if all(status == "UP" for status in service_statuses.values()) else "DOWN"

        return jsonify({
            "application_name": "rbcapp1",
            "application_status": app_status,
            "services": service_statuses,
        })
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve health status: {str(exc)}"}), 500


@app.route("/healthcheck/<service_name>", methods=["GET"])
def service_health(service_name):
    try:
        normalized = normalize_service_name(service_name)
        latest = latest_status_by_service()
        source = latest.get(normalized)

        if not source:
            return jsonify({
                "service_name": normalized,
                "service_status": "DOWN",
                "message": "No status found in Elasticsearch; treated as DOWN",
            }), 404

        return jsonify({
            "service_name": normalized,
            "service_status": source.get("service_status", "DOWN"),
            "host_name": source.get("host_name"),
            "@timestamp": source.get("@timestamp"),
        })
    except Exception as exc:
        return jsonify({"error": f"Failed to retrieve service status: {str(exc)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
