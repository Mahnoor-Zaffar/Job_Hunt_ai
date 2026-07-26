from pathlib import Path
from backend.services.digest.config import DigestConfig


def test_config_loads_all_files(config: DigestConfig):
    assert len(config.accepted_explicit) > 0
    assert len(config.accepted_related) > 0
    assert len(config.rejected_patterns) > 0
    assert len(config.tech_domains) > 0
    assert len(config.cat_configs) > 0
    assert config.confidence_config is not None
    assert config.preferences is not None


def test_accepted_titles(config: DigestConfig):
    explicit = config.accepted_explicit
    assert "backend engineer" in explicit
    assert "frontend developer" in explicit
    assert "full stack developer" in explicit
    assert "ai engineer" in explicit
    assert "devops engineer" in explicit
    assert "llm engineer" in explicit
    assert "ai developer" in explicit
    assert "ai platform engineer" in explicit

    related = config.accepted_related
    assert "software engineer" in related
    assert "software developer" in related


def test_rejected_patterns(config: DigestConfig):
    patterns = config.rejected_patterns
    assert "sales" in patterns
    assert "marketing" in patterns
    assert "recruiter" in patterns
    assert "blockchain" in patterns
    assert "intern" in patterns
    assert config.reject_internships is True


def test_categories(config: DigestConfig):
    keys = config.category_keys()
    assert "backend" in keys
    assert "frontend" in keys
    assert "fullstack" in keys
    assert "devops" in keys
    assert "ai" in keys
    assert "ml" in keys
    assert "llm" in keys

    assert config.category_label("backend") == "Backend Engineering"
    assert config.category_label("frontend") == "Frontend Engineering"
    assert config.category_label("llm") == "LLM Engineer"

    assert config.category_title_patterns("llm") is not None
    llm_domains = config.category_tech_domains("llm")
    assert "llm" in llm_domains


def test_scoring_config(config: DigestConfig):
    conf = config.confidence_config
    assert "high" in conf
    assert "medium" in conf
    assert "low" in conf
    assert conf["high"].get("score_value") == 100
    assert conf["medium"].get("score_value") == 70
    assert conf["low"].get("score_value") == 0

    thresholds = config.scoring_thresholds
    assert thresholds.get("technology_minimum", 0) > 0


def test_preferences(config: DigestConfig):
    assert config.max_per_category > 0
    assert config.max_total > 0
    assert config.min_confidence in ("high", "medium", "low")
    assert config.max_days_old > 0


def test_config_custom_dir(tmp_path: Path):
    custom_file = tmp_path / "scoring.yaml"
    custom_file.write_text("confidence:\n  high:\n    score_value: 100\nthresholds:\n  technology_minimum: 2")
    cfg = DigestConfig(tmp_path)
    assert cfg.confidence_config["high"]["score_value"] == 100
    assert cfg.scoring_thresholds.get("technology_minimum") == 2
