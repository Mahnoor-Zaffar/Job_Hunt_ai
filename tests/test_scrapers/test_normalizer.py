import pytest

from backend.scrapers.models.models import RawJob
from backend.scrapers.normalizer.normalizer import Normalizer


class TestNormalizerEnhanced:
    @pytest.fixture
    def normalizer(self) -> Normalizer:
        return Normalizer()

    def test_remote_type_from_flag(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com/j/1",
            source="test",
            source_id="1",
            is_remote=True,
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "remote"
        assert nj.is_remote is True

    def test_remote_type_from_location_keyword(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Work from home",
            url="https://x.com/j/2",
            source="test",
            source_id="2",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "remote"

    def test_hybrid_detection(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Hybrid - London, UK",
            url="https://x.com/j/3",
            source="test",
            source_id="3",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "hybrid"

    def test_hybrid_detection_flexible(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Flexible remote, Islamabad",
            url="https://x.com/j/4",
            source="test",
            source_id="4",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "hybrid"

    def test_onsite_default(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Islamabad, Pakistan",
            url="https://x.com/j/5",
            source="test",
            source_id="5",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "onsite"
        assert nj.is_remote is False

    def test_raw_remote_type_preserved(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Some Office",
            url="https://x.com/j/6",
            source="test",
            source_id="6",
            is_remote=False,
            remote_type="remote",
        )
        nj = normalizer.normalize(raw)
        assert nj.remote_type == "remote"

    def test_supported_location_islamabad(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Islamabad, Pakistan",
            url="https://x.com/j/7",
            source="test",
            source_id="7",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert normalizer.is_supported_location(nj) is True

    def test_supported_location_rawalpindi(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Rawalpindi",
            url="https://x.com/j/8",
            source="test",
            source_id="8",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert normalizer.is_supported_location(nj) is True

    def test_supported_location_lahore(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Lahore, Pakistan",
            url="https://x.com/j/9",
            source="test",
            source_id="9",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert normalizer.is_supported_location(nj) is True

    def test_karachi_not_supported(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Karachi, Pakistan",
            url="https://x.com/j/10",
            source="test",
            source_id="10",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.city == "Karachi"
        assert normalizer.is_supported_location(nj) is False

    def test_remote_job_is_supported(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com/j/11",
            source="test",
            source_id="11",
            is_remote=True,
        )
        nj = normalizer.normalize(raw)
        assert normalizer.is_supported_location(nj) is True

    def test_tech_skills_merged_from_description(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Python Engineer",
            company="Co",
            location="Remote",
            url="https://x.com/j/12",
            source="test",
            source_id="12",
            is_remote=True,
            skills=["Django"],
            description="We need Python, Docker, and AWS experience",
        )
        nj = normalizer.normalize(raw)
        assert nj.skills is not None
        assert "Python" in nj.skills
        assert "Docker" in nj.skills
        assert "AWS" in nj.skills
        assert "Django" in nj.skills

    def test_skills_sorted(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com/j/13",
            source="test",
            source_id="13",
            is_remote=True,
            skills=["Flask", "Python", "Docker"],
        )
        nj = normalizer.normalize(raw)
        assert nj.skills is not None
        assert nj.skills == sorted(nj.skills)

    def test_normalized_has_fingerprint(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Lahore",
            url="https://x.com/j/14",
            source="test",
            source_id="14",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.fingerprint
        assert len(nj.fingerprint) == 64  # SHA-256 hex
