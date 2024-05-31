"""Module used to compute metrics for a given datasets."""
import copy
from logging import Logger
from pathlib import Path
from typing import Any, List, Union

import click

import ig.cross_validation as exper
from ig import DATAPROC_DIRECTORY, MODELS_DIRECTORY
from ig.constants import EvalExpType
from ig.dataset.dataset import Dataset
from ig.src.logger import get_logger, init_logger
from ig.src.utils import (
    get_best_experiment,
    import_experiment,
    load_experiments,
    load_models,
    load_yml,
    log_summary_results,
)

log: Logger = get_logger("Eval")


@click.command()  # noqa
@click.option(
    "--test_data_paths",
    "-d",
    type=str,
    required=True,
    multiple=True,
    help="Path to the dataset used in  evaluation.",
)
@click.option(
    "--eval_id_name",
    "-eid",
    type=str,
    default=None,
    help="column name to eval per split.",
)
@click.option("--folder_name", "-n", type=str, required=True, help="Experiment name.")
@click.pass_context
def compute_metrics(  # noqa: CCR001
    ctx: Union[click.core.Context, Any],
    test_data_paths: List[str],
    folder_name: str,
    eval_id_name: str,
) -> None:
    """Evaluation  on a separate datasets."""
    experiment_path = MODELS_DIRECTORY / folder_name
    init_logger(logging_directory=experiment_path, file_name="InfoEval")
    general_configuration = load_yml(experiment_path / "configuration.yml")
    general_configuration["evaluation"]["eval_id_name"] = eval_id_name
    if not eval_id_name:
        general_configuration["evaluation"]["metric_selector"] = "topk"
        general_configuration["evaluation"]["monitoring_metrics"] = ["topk"]

    eval_configuration = general_configuration["evaluation"]
    log.info("****************************** Load YAML ****************************** ")
    experiment_names, experiment_params = load_experiments(general_configuration)
    log.info("****************************** Load EXP ****************************** ")
    model_types, model_params = load_models(general_configuration, experiment_path)
    log.info("****************************** Load Models ****************************** ")
    features_list_paths = copy.deepcopy(general_configuration["feature_paths"])
    log.info("****************************** Load Features lists *****************************")
    features_configuration_path = (
        experiment_path / DATAPROC_DIRECTORY / "features_configuration.yml"
    )
    for test_data_path in test_data_paths:

        test_data = Dataset(
            click_ctx=ctx,
            data_path=test_data_path,
            configuration=general_configuration,
            is_train=False,
            experiment_path=experiment_path,
            force_gcp=True,
            process_label=True,
            is_inference=True,
        ).load_data()
        file_name = Path(test_data_path).stem
        log.info(" %s \n", "#" * 20)
        log.info("Start evaluating %s\n", file_name)
        log.info("%s \n", "#" * 20)

        results: List[EvalExpType] = []
        for experiment_name, experiment_param in zip(experiment_names, experiment_params):
            log.info("%s :", experiment_name)
            experiment_class = import_experiment(exper, experiment_name)
            for model_type, _ in zip(model_types, model_params):
                log.info(" %s :", model_type)
                for features_list_path in features_list_paths:
                    features_list_name = features_list_path
                    run_path = experiment_path / experiment_name / features_list_name / model_type
                    configuration = load_yml(run_path / "configuration.yml")
                    configuration["evaluation"]["eval_id_name"] = eval_id_name
                    if not eval_id_name:
                        configuration["evaluation"]["metric_selector"] = "topk"

                    log.info("  %s :", features_list_name)
                    experiment = experiment_class(
                        train_data=None,
                        test_data=test_data,
                        configuration=configuration,
                        experiment_name=experiment_name,
                        folder_name=folder_name,
                        sub_folder_name=features_list_name,
                        features_configuration_path=features_configuration_path,
                        **experiment_param,
                    )

                    scores = experiment.eval_test()
                    results.append(scores)
        _, eval_message = get_best_experiment(
            results, eval_configuration, path=MODELS_DIRECTORY / folder_name, file_name="results"
        )
        log_summary_results(eval_message)

        log.info("Eval best experiment")
        best_exp_path = MODELS_DIRECTORY / folder_name / "best_experiment"
        best_exp_configuration = load_yml(best_exp_path / "configuration.yml")
        best_exp_configuration["evaluation"]["eval_id_name"] = eval_id_name
        if not eval_id_name:
            best_exp_configuration["evaluation"]["metric_selector"] = "topk"
        best_experiment_name = list(best_exp_configuration["experiments"])[0]
        best_experiment_param = best_exp_configuration["experiments"][best_experiment_name]
        best_experiment_features_file_path = best_exp_path / "features.txt"
        best_experiment_class = import_experiment(exper, best_experiment_name)

        experiment = best_experiment_class(
            train_data=None,
            test_data=test_data,
            configuration=best_exp_configuration,
            experiment_name=best_experiment_name,
            folder_name=folder_name,
            sub_folder_name=best_exp_configuration["features"],
            experiment_directory=best_exp_path,
            features_file_path=best_experiment_features_file_path,
            features_configuration_path=features_configuration_path,
            **best_experiment_param,
        )
        log.info("Experiment : %s", best_experiment_name)
        log.info("model : %s", best_exp_configuration["model_type"])
        log.info("features : %s", best_exp_configuration["features"])

        scores = experiment.eval_test()