import os
import syslog
from functools import partial

import tx.logging.utils
from tx.fhir.utils import bundle, unbundle
from tx.functional.either import Left, Right, either_applicative
from tx.functional.list import list_traversable
from tx.logging.utils import tx_log
from tx.requests.utils import get, post

list_traversable_either_applicative = list_traversable(either_applicative)
post_headers = {"Content-Type": "application/json", "Accept": "application/json"}


# pds_host = os.environ["PDS_HOST"]
# pds_port = os.environ["PDS_PORT"]
# pds_config = os.environ["PDS_CONFIG"]
# pds_version = os.environ["PDS_VERSION"]
# pds_logging = os.environ["PDS_LOGGING"]
# pds_url_base = f"http://{pds_host}:{pds_port}/{pds_version}/plugin"


def log(level, event, source, *args, **kwargs):
    tx_log(f"{pds_url_base}/{pds_logging}", level, event, source, *args, **kwargs)


cfv_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "clinical_feature_variable": {"type": "string"},
            "description": {"type": "string"},
            "title": {"type": "string"},
            "why": {"type": "string"},
            "units": {"type": "string"},
        },
        "required": ["clinicalFeatureVariable", "description", "title", "why"],
    },
}


def _get_records(ptids, fhir_plugin_id, timestamp):
    pt_records = []
    for ptid in ptids:
        url_patient = f"{pds_url_base}/{fhir_plugin_id}/Patient/{ptid}"
        url_condition = f"{pds_url_base}/{fhir_plugin_id}/Condition?patient={ptid}"
        url_observation = f"{pds_url_base}/{fhir_plugin_id}/Observation?patient={ptid}"

        val = get(url_patient).bind(
            lambda patient: get(url_condition).bind(
                lambda condition: get(url_observation).bind(
                    lambda observation: unbundle(condition).bind(
                        lambda condition_unbundled: unbundle(observation).map(
                            lambda observation_unbundled: bundle(
                                [patient, *condition_unbundled, *observation_unbundled]
                            )
                        )
                    )
                )
            )
        )
        pt_records.append(val)
    return list_traversable_either_applicative.sequence(pt_records)


def default_mapper_plugin_id():
    return next(filter(lambda x: x["pluginType"] == "m", get_config()))["piid"]


def default_fhir_plugin_id():
    return next(filter(lambda x: x["pluginType"] == "f", get_config()))["piid"]


def _get_patient_variables(body):
    patient_ids = body["patientIds"]
    piid = body["guidancePiid"]
    mapper_plugin_id = body.get("mapperPiid")
    if mapper_plugin_id == None:
        mapper_plugin_id = default_mapper_plugin_id()
        log(syslog.LOG_ERR, f"no mapperPiid, using {mapper_plugin_id}", "pds")
    fhir_plugin_id = body.get("fhirPiid")
    if fhir_plugin_id == None:
        fhir_plugin_id = default_fhir_plugin_id()
        log(syslog.LOG_ERR, f"no fhirPiid, using {fhir_plugin_id}", "pds")
    timestamp = body.get("timestamp")
    if timestamp == None:
        timestamp = tx.logging.utils.timestamp()
        log(syslog.LOG_ERR, f"no timestamp, using {timestamp}", "pds")

    def handle_clinical_feature_variables(config):
        if len(config) > 0:
            if len(config) > 1:
                log(syslog.LOG_ERR, f"more than one configs for plugin {piid}", "pds")
            clinical_feature_variable_objects = config[0]["settingsDefaults"][
                "patientVariables"
            ]

            def cfvo_to_cfvo2(cfvo):
                cfvo2 = {**cfvo}
                return Right(cfvo2)

            return list_traversable_either_applicative.sequence(
                list(map(cfvo_to_cfvo2, clinical_feature_variable_objects))
            )
        else:
            return Left(f"no configs for plugin {piid}")

    def handle_mapper(cfvos2, data):
        url = f"{pds_url_base}/{mapper_plugin_id}/mapping"
        return post(
            url,
            json={
                "patientIds": patient_ids,
                "timestamp": timestamp,
                "settingsRequested": {"patientVariables": cfvos2},
                "data": data,
            },
        )

    return (
        _get_config(piid)
        .bind(handle_clinical_feature_variables)
        .bind(
            lambda cfvo2: (
                _get_records(patient_ids, fhir_plugin_id, timestamp).bind(
                    partial(handle_mapper, cfvo2)
                )
            )
        )
    )


def get_patient_variables(body):
    return _get_patient_variables(body).value


def _get_guidance(body):
    for body_item in body:
        piid = body_item["piid"]
        mapperPiid = body_item.get("mapperPiid")
        fhirPiid = body_item.get("fhirPiid")
        if (
            "settingsRequested" not in body_item
            or "patientVariables" not in body_item["settingsRequested"]
        ):
            pvs = _get_patient_variables(
                {
                    "patientIds": [body_item["patientId"]],
                    "guidancePiid": piid,
                    **({} if mapperPiid is None else {"mapperPiid": mapperPiid}),
                    **({} if fhirPiid is None else {"fhirPiid": fhirPiid}),
                }
            )
            if isinstance(pvs, Left):
                return pvs
            else:
                pat_vars = {
                    "patientVariables": val["values"]
                    for val in pvs.value
                    if val["patientId"] == body_item["patientId"]
                }
                body_item["settingsRequested"] = pat_vars

    url = f"{pds_url_base}/{piid}/guidance"
    resp2 = post(url, json=body)
    return resp2


def get_guidance(body):
    return _get_guidance(body).value


def get_config(piid=None):
    return _get_config(piid).value


def error_code(result):
    return result.rec(
        lambda err: Left(("not found", 404) if err[0]["status_code"] == 404 else err),
        lambda config: Right(config),
    )


def _get_config(piid=None):
    url = f"{pds_url_base}/{pds_config}/config"
    if piid is not None:
        url += f"/{piid}"

    return error_code(get(url)).map(lambda config: config if piid is None else [config])


def get_selector_config():
    return _get_selector_config().value


def _get_selector_config():
    url = f"{pds_url_base}/{pds_config}/selectorConfig"

    return error_code(get(url))


def get_selectors(piid=None):
    url = f"{pds_url_base}/{pds_config}/selectors"
    resp = get(url)
    return resp.value
