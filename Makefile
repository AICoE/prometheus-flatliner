oc_app_name=prometheus-flatliner-job
prometheus_endpoint_url=www.exampleUrl.com
prometheus_access_token=DUMMY_ACCESS_TOKEN
metrics_list=openshift_build_info,etcd_object_counts,alerts
metric_start_datetime=16 Oct 2018
metric_end_datetime=17 Oct 2018
metric_chunk_size=1h
oc_image_name=prometheus-flatliner-build-image
influx_db_url=example.com:8080

oc_build:
	oc new-app --file=./prometheus-flatliner-image-build-template.yaml \
			--param APPLICATION_NAME="${oc_image_name}"

oc_deploy:
	oc new-app --file=./prometheus-flatliner-job-template.yaml \
			--param APPLICATION_NAME="${oc_app_name}" \
			--param FLT_PROM_URL=${prometheus_endpoint_url} \
			--param FLT_PROM_ACCESS_TOKEN="${prometheus_access_token}" \
			--param FLT_METRICS_LIST="${metrics_list}" \
			--param FLT_METRIC_START_DATETIME="${metric_start_datetime}" \
			--param FLT_METRIC_END_DATETIME="${metric_end_datetime}" \
			--param FLT_METRIC_CHUNK_SIZE="${metric_chunk_size}" \
			--param BUILD_IMAGE="${oc_image_name}" \
			--param FLT_INFLUX_HOST="${influx_db_url}"

oc_delete_job:
	oc delete all -l app="${oc_app_name}"

oc_delete_image:
	oc delete all -l app="${oc_image_name}"
