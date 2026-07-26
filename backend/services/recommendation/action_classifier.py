from backend.models.career_profile import CareerProfile
from backend.services.ranking.models import RankedJob
from backend.services.ranking.weights import load_actions, load_labels


def classify_action(ranked: RankedJob, profile: CareerProfile | None = None) -> str:
    labels = load_labels()
    actions = load_actions()

    label = ranked.label
    for lbl, threshold in sorted(labels.items(), key=lambda x: x[1], reverse=True):
        if ranked.composite_score >= threshold:
            label = lbl
            break

    return actions.get(label, "Skip")
