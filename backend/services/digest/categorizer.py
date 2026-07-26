from backend.services.digest.config import DigestConfig
from backend.services.digest.models import ScoredJob, CategoryGroup
from backend.services.digest.sorter import sort_jobs


def assign_categories(jobs: list[ScoredJob], config: DigestConfig) -> list[CategoryGroup]:
    grouped: dict[str, list[ScoredJob]] = {}

    for sj in jobs:
        cat = sj.category
        if cat is None:
            continue
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(sj)

    result: list[CategoryGroup] = []
    for cat_key in config.category_keys():
        cat_jobs = grouped.get(cat_key, [])

        if not cat_jobs:
            continue

        cat_jobs = sort_jobs(cat_jobs)

        max_per = config.max_per_category
        cat_jobs = cat_jobs[:max_per]

        group = CategoryGroup(
            category_key=cat_key,
            category_label=config.category_label(cat_key),
            jobs=cat_jobs,
        )
        result.append(group)

    return result
