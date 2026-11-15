"""This module is used to parse external data and add them to the DB for the app.
This is a standalone script that should not be imported"""

from __future__ import annotations

import os
import time
from collections.abc import Generator

import ijson
from connect import ExternalFoodsDB, FoodData


def parse_foods_foundation(filename: str, heading: str) -> Generator[FoodData]:
    data = ijson.items(open(filename, errors="ignore"), f"{heading}.item")
    for i, food in enumerate(data):
        description = food["description"]
        if "servingSize" in food:
            unit = food["servingSizeUnit"]
            if unit in ("mg", "ml"):
                food["servingSize"] /= 1000
            elif unit in ("g", "l"):
                pass
            else:
                assert False, "Unknown serving" + unit
            portions = {"Serving": food["servingSize"]}
        elif "foodPortions" in food:
            portions = food["foodPortions"]
            portions = {p["measureUnit"]["name"]: p["gramWeight"] for p in portions}
        else:
            continue
        nut_dict = dict.fromkeys(("protein", "fats", "carbs", "sodium", "sugar", "water"), 0.0)
        for nut in food["foodNutrients"]:
            name = nut["nutrient"]["name"]
            for s in nut_dict:
                if s.rstrip("s") in name.lower():
                    nut_dict[s] = float(nut["amount"])
                    # unit_name = nut['nutrient']['unitName']
                    # if unit_name == 'mg':
                    #     nut_dict[s] /= 1000

        portions = ",".join(f"{k}:{v}" for k, v in portions.items())
        yield FoodData(description=description, portions=portions, **nut_dict)


if __name__ == "__main__":
    db_dict = {
        "FoodData_Central_foundation_food_json_2021-10-28.json": "FoundationFoods",
        "FoodData_Central_sr_legacy_food_json_2021-10-28.json": "SRLegacyFoods",
        "FoodData_Central_branded_food_json_2021-10-28.json": "BrandedFoods",
    }
    db_dict = {os.path.abspath(k): v for k, v in db_dict.items()}
    with ExternalFoodsDB(locally=True) as fdb:
        start = time.perf_counter()
        for path, header in db_dict.items():
            for f in parse_foods_foundation(path, header):
                fdb.add_food(f)
        print(" ..Done.. Took", time.perf_counter() - start)
