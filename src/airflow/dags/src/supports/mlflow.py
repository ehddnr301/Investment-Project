import mlflow
from mlflow.tracking import MlflowClient
from mlflow.store.artifact.runs_artifact_repo import RunsArtifactRepository


def create_new_mlflow_model(model_name: str) -> int:
    client = MlflowClient()

    filter_string = f"name='{model_name}'"
    results = client.search_model_versions(filter_string)

    if not results:
        client.create_registered_model(model_name)

        return 200

    return 409


def create_model_version(model_name: str, run_id: str, model_uri: str) -> str:
    client = MlflowClient()

    model_source = RunsArtifactRepository.get_underlying_uri(model_uri)
    model_version = client.create_model_version(model_name, model_source, run_id)

    return model_version.version


def update_registered_model(
    model_name: str, version: str, eval_metric: str, optimize_method: str = "maximize"
) -> str:
    client = MlflowClient()
    production_model = None
    current_model = client.get_model_version(model_name, version)

    filter_string = f"name='{current_model.name}'"
    model_version_list = client.search_model_versions(filter_string)

    for mv in model_version_list:
        if mv.current_stage == "Production":
            production_model = mv

    if production_model is None:
        client.transition_model_version_stage(
            current_model.name, current_model.version, "Production"
        )
        production_model = current_model

        return "Production Model Registered"

    else:
        current_metric = client.get_run(current_model.run_id).data.metrics[eval_metric]
        production_metric = client.get_run(production_model.run_id).data.metrics[
            eval_metric
        ]

        if (current_metric > production_metric and optimize_method == "maximize") or (
            current_metric < production_metric and optimize_method == "minimize"
        ):
            client.transition_model_version_stage(
                current_model.name,
                current_model.version,
                "Production",
                archive_existing_versions=True,
            )
            production_model = current_model

            return "Production Model Updated"

    return "Nothing Changed"
