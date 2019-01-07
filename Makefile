ENV_FILE := .env
include ${ENV_FILE}
export $(shell sed 's/=.*//' ${ENV_FILE})
export PIPENV_DOTENV_LOCATION=${ENV_FILE}

oc_get_token:
	oc sa get-token "prometheus" -n "${NAMESPACE}"

oc_create_build:
	oc process --filename=openshift/prometheus-flatliner-image-build-template.yaml \
		--param NAMESPACE=${NAMESPACE} \
		| oc apply -f -

oc_build_head:
	$(eval ARCHIVE=$(shell mktemp))
	git archive --format=tar.gz HEAD > ${ARCHIVE}
	oc start-build prometheus-flatliner --from-archive ${ARCHIVE} --follow

oc_trigger_build:
	oc start-build prometheus-flatliner -F

oc_historic_job:
	oc process --filename=openshift/prometheus-flatliner-job-template.yaml \
		--param APPLICATION_NAME="prometheus-flatliner-historic-job" \
		--param NAMESPACE=${NAMESPACE} \
		--param FLT_PROM_URL=${FLT_PROM_URL} \
		--param FLT_PROM_ACCESS_TOKEN="${FLT_PROM_ACCESS_TOKEN}" \
		--param FLT_METRICS_LIST="${FLT_METRICS_LIST}" \
		--param FLT_METRIC_START_DATETIME="${FLT_METRIC_START_DATETIME}" \
		--param FLT_METRIC_END_DATETIME="${FLT_METRIC_END_DATETIME}" \
		--param FLT_METRIC_CHUNK_SIZE="${FLT_METRIC_CHUNK_SIZE}" \
		--param FLT_LIVE_METRIC_COLLECT="False" \
		| oc apply -f -

oc_delete_historic_job:
	oc delete all -l app=prometheus-flatliner-historic-job

oc_live_job:
	oc process --filename=openshift/prometheus-flatliner-job-template.yaml \
		--param APPLICATION_NAME="prometheus-flatliner-live-job"
		--param NAMESPACE=${NAMESPACE} \
		--param FLT_PROM_URL=${FLT_PROM_URL} \
		--param FLT_PROM_ACCESS_TOKEN="${FLT_PROM_ACCESS_TOKEN}" \
		--param FLT_METRICS_LIST="${FLT_METRICS_LIST}" \
		--param FLT_METRIC_START_DATETIME="${FLT_METRIC_START_DATETIME}" \
		--param FLT_METRIC_END_DATETIME="${FLT_METRIC_END_DATETIME}" \
		--param FLT_METRIC_CHUNK_SIZE="${FLT_METRIC_CHUNK_SIZE}" \
		--param FLT_INFLUX_DB_DSN="${FTL_INFLUX_DB_DSN}" \
		--param FLT_LIVE_METRIC_COLLECT="True" \
		| oc apply -f -

oc_delete_live_job:
	oc delete all -l app=prometheus-flatliner-live-job

run_app:
	PIPENV_DOTENV_LOCATION=.env pipenv run python app.py

historic_job:
	PIPENV_DOTENV_LOCATION=.env.historic pipenv run pytest

test:
	PIPENV_DOTENV_LOCATION=.env.test pipenv run pytest
