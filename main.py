import pandas as pd

from tests import (
    dataset_to_factor_plan,
    do_factor_analysis,
    make_some_factor_plan_dataset,
)
from utils import config_debug

if __name__ == "__main__":
    config_debug()
    FILENAME = "./output/dataset.csv"

    # make_some_factor_plan_dataset(FILENAME)

    dataset = pd.read_csv(FILENAME)
    factor_plan = dataset_to_factor_plan(dataset)

    main_effects, interaction_effects = do_factor_analysis(factor_plan)
    print("Главные эффекты:", main_effects)
    print("Эффекты взаимодействия:", interaction_effects)
    pass
