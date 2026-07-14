from backend.scrapers.technologies import TechnologyExtractor, extract_technologies


class TestTechnologyExtractor:
    def test_extract_empty_input(self) -> None:
        assert extract_technologies(None) == []
        assert extract_technologies("") == []
        assert extract_technologies("   ") == []

    def test_extract_common_tech(self) -> None:
        result = extract_technologies("We need a Python developer with Docker experience")
        assert "Python" in result
        assert "Docker" in result

    def test_extract_case_insensitive(self) -> None:
        result = extract_technologies("PYTHON is great, and DOCKER too")
        assert "Python" in result
        assert "Docker" in result

    def test_extract_multiple_sorted(self) -> None:
        result = extract_technologies(
            "Looking for a Python and React developer with AWS experience"
        )
        assert result == sorted(result)
        assert "Python" in result
        assert "React" in result
        assert "AWS" in result

    def test_non_tech_not_extracted(self) -> None:
        result = extract_technologies("We are a friendly team looking for great people")
        assert result == []

    def test_extract_from_description(self) -> None:
        text = (
            "We need someone who knows FastAPI, PostgreSQL, Redis, "
            "and Kubernetes. Experience with CI/CD and Terraform is a plus."
        )
        result = extract_technologies(text)
        assert "FastAPI" in result
        assert "PostgreSQL" in result
        assert "Redis" in result
        assert "Kubernetes" in result
        assert "CI/CD" in result
        assert "Terraform" in result

    def test_class_instance_works(self) -> None:
        extractor = TechnologyExtractor()
        result = extractor.extract("We use TypeScript and React")
        assert "TypeScript" in result
        assert "React" in result

    def test_extract_react_native_not_confused_with_react(self) -> None:
        result = extract_technologies("We build React Native apps")
        assert "React Native" in result

    def test_extract_node_js(self) -> None:
        result = extract_technologies("Knowledge of Node.js and Next.js required")
        assert "Node.js" in result
        assert "Next.js" in result

    def test_extract_machine_learning(self) -> None:
        result = extract_technologies(
            "Looking for Machine Learning engineer with PyTorch and TensorFlow skills"
        )
        assert "Machine Learning" in result
        assert "PyTorch" in result
        assert "TensorFlow" in result

    def test_extract_java_not_javascript(self) -> None:
        # "Java" without "Script" should match
        result = extract_technologies("We are a Java shop")
        assert "Java" in result
