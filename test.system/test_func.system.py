import requests
import time

config = {
    "piids": ["pdspi-guidance-example", "pdspi-mapper-example", "pdspi-fhir-example"],
    "selectors": [
        {
            "id": "PDS:sars",
            "legalValues": {
                "enum": [
                    {"title": "Treatment", "value": "PDS:sars:treatment"},
                    {"title": "Resource", "value": "PDS:sars:resource"},
                ],
                "type": "string",
            },
            "title": "SARS",
        },
        {
            "title": "Drug",
            "id": "dosing.rxCUI",
            "legalValues": {
                "type": "string",
                "enum": [
                    {"value": "rxCUI:1596450", "title": "Gentamicin"},
                    {"value": "rxCUI:1114195"},
                    {"value": "rxCUI:1546356"},
                    {"value": "rxCUI:1364430"},
                    {"value": "rxCUI:1599538"},
                    {"value": "rxCUI:1927851"},
                ],
            },
        },
    ],
    "custom_units": [
        {"id": "LOINC:2160-0", "units": "mg/dL"},
        {"id": "LOINC:30525-0", "units": "year"},
        {"id": "LOINC:8302-2", "units": "m"},
        {"id": "LOINC:29463-7", "units": "kg"},
        {"id": "LOINC:39156-5", "units": "kg/m^2"},
    ],
}


time.sleep(60)


def test_get_custom_units():
    resp = requests.get("http://localhost:8080/v1/plugin/pdspi-config/customUnits")

    assert resp.status_code == 200
    assert resp.json() == config["custom_units"]


def test_get_selectors():
    resp = requests.get("http://localhost:8080/v1/plugin/pdspi-config/selectors")

    assert resp.status_code == 200
    assert resp.json() == config["selectors"]


def test_get_pds_selectors():
    resp = requests.get("http://localhost:8080/v1/plugin/pds/selectors")

    assert resp.status_code == 200
    assert resp.json() == config["selectors"]


def test_get_config():
    resp = requests.get("http://localhost:8080/v1/plugin/pdspi-config/config")

    assert resp.status_code == 200
    arr = resp.json()
    assert len(arr) == 5
    for a in arr:
        assert "pluginType" in a
        assert "pluginSelectors" in a
        assert "piid" in a
        # assert "pluginTypeTitle" in a
        # assert "title" in a


def test_get_pds_config():
    resp = requests.get("http://localhost:8080/v1/plugin/pds/config")

    assert resp.status_code == 200
    arr = resp.json()
    assert len(arr) == 5
    for a in arr:
        assert "pluginType" in a
        assert "pluginSelectors" in a
        assert "piid" in a
        # assert "pluginTypeTitle" in a
        # assert "title" in a


def test_get_config_piid():
    resp = requests.get(
        "http://localhost:8080/v1/plugin/pdspi-config/config/pdspi-guidance-example"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "pluginType" in a
    assert "pluginSelectors" in a
    assert "piid" in a
    # assert "pluginTypeTitle" in a
    # assert "title" in a

    resp = requests.get(
        "http://localhost:8080/v1/plugin/pdspi-config/config/pdspi-mapper-example"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "pluginType" in a
    assert "pluginSelectors" in a
    assert "piid" in a
    # assert "pluginTypeTitle" in a
    # assert "title" in a

    resp = requests.get(
        "http://localhost:8080/v1/plugin/pdspi-config/config/pdspi-fhir-example"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "pluginType" in a
    assert "pluginSelectors" in a
    assert "piid" in a
    # assert "pluginTypeTitle" in a
    # assert "title" in a


synthetic_ptid = "smart-7321938"


def test_get_Patient_ptid():
    resp = requests.get(
        f"http://localhost:8080/v1/plugin/pdspi-fhir-example/Patient/{synthetic_ptid}"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "id" in a
    assert a["id"] == synthetic_ptid


def test_get_Observation_ptid():
    resp = requests.get(
        f"http://localhost:8080/v1/plugin/pdspi-fhir-example/Observation?patient={synthetic_ptid}"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "resourceType" in a
    assert a["resourceType"] == "Bundle"
    for entry in a.get("entry", []):
        assert "resource" in entry
        resource = entry["resource"]
        assert resource["resourceType"] == "Observation"
        assert resource["subject"]["reference"] == f"Patient/{synthetic_ptid}"


def test_get_Condition_ptid():
    resp = requests.get(
        f"http://localhost:8080/v1/plugin/pdspi-fhir-example/Condition?patient={synthetic_ptid}"
    )

    assert resp.status_code == 200
    a = resp.json()

    assert "resourceType" in a
    assert a["resourceType"] == "Bundle"
    for entry in a.get("entry", []):
        assert "resource" in entry
        resource = entry["resource"]
        assert resource["resourceType"] == "Condition"
        assert resource["subject"]["reference"] == f"Patient/{synthetic_ptid}"


json_post_headers = {"Content-Type": "application/json", "Accept": "application/json"}


def test_get_pds_patient_variables():
    resp = requests.post(
        f"http://localhost:8080/v1/plugin/pds/patientVariables",
        json={
            "ptid": "smart-7321938",
            "guidance_piid": "pdspi-guidance-example",
            "timestamp": "2020-02-19T00:00:00Z",
        },
        headers=json_post_headers,
    )

    print(resp.content)
    assert resp.status_code == 200
    assert resp.json() == [
        {
            "certitude": 2,
            "how": "Current date '2020-02-19' minus patient's birthdate (FHIR resource 'Patient' field>'birthDate' = '2010-12-16')",
            "id": "LOINC:30525-0",
            "variableValue": {"units": "year", "value": 9},
        },
        {
            "certitude": 0,
            "how": "no record found code http://loinc.org 29463-7",
            "id": "LOINC:29463-7",
            "variableValue": {"value": None},
        },
        {
            "certitude": 0,
            "how": "no record found code http://loinc.org 39156-5",
            "id": "LOINC:39156-5",
            "variableValue": {"value": None},
        },
    ]


def test_get_pds_patient_variables_no_timestamp():
    resp = requests.post(
        f"http://localhost:8080/v1/plugin/pds/patientVariables",
        json={"ptid": "smart-7321938", "guidance_piid": "pdspi-guidance-example"},
        headers=json_post_headers,
    )

    print(resp.content)
    assert resp.status_code == 200
    rj = resp.json()
    assert len(rj) == 3


def test_post_pds_guidance():
    resp = requests.post(
        "http://localhost:8080/v1/plugin/pds/guidance",
        headers=json_post_headers,
        json={"piid": "pdspi-guidance-example", "ptid": synthetic_ptid},
    )

    print(resp.content)
    assert resp.status_code == 200

    rj = resp.json()
    assert "justification" in rj


def test_post_pds_guidance_user_supplied_patient_variables():
    resp = requests.post(
        "http://localhost:8080/v1/plugin/pds/guidance",
        headers=json_post_headers,
        json={
            "piid": "pdspi-guidance-example",
            "ptid": synthetic_ptid,
            "userSuppliedPatientVariables": [
                {
                    "certitude": 2,
                    "how": "Current date '2020-02-19' minus patient's birthdate (FHIR resource 'Patient' field>'birthDate' = '2010-12-16')",
                    "id": "LOINC:30525-0",
                    "variableValue": {"units": "year", "value": 9},
                },
                {
                    "certitude": 0,
                    "how": "no record found code http://loinc.org 39156-5",
                    "id": "LOINC:39156-5",
                    "variableValue": {"value": None},
                },
            ],
        },
    )

    print(resp.content)
    assert resp.status_code == 200

    rj = resp.json()
    assert "justification" in rj


def test_post_pds_guidance_plugin_parameter_values():
    resp = requests.post(
        "http://localhost:8080/v1/plugin/pds/guidance",
        headers=json_post_headers,
        json={
            "piid": "pdspi-guidance-example",
            "ptid": synthetic_ptid,
            "pluginParameterValues": [
                {
                    "id": "pdspi-guidance-example:1",
                    "parameterDescription": "This calculator uses one of four extended-interval nomograms. Please choose one nomogram.",
                    "parameterValue": {"value": "Hartford"},
                    "title": "Extended interval nomogram",
                }
            ],
        },
    )

    print(resp.content)
    assert resp.status_code == 200

    rj = resp.json()
    assert "justification" in rj