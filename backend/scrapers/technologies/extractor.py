import re

TECH_PATTERNS: dict[str, re.Pattern[str]] = {
    "Python": re.compile(r"\bPython\b", re.I),
    "FastAPI": re.compile(r"\bFast\s*API\b", re.I),
    "Flask": re.compile(r"\bFlask\b", re.I),
    "Django": re.compile(r"\bDjango\b", re.I),
    "JavaScript": re.compile(r"\bJava\s*Script\b", re.I),
    "TypeScript": re.compile(r"\bType\s*Script\b", re.I),
    "Node.js": re.compile(r"\bNode\s*\.?\s*[Jj][Ss]\b"),
    "React": re.compile(r"\bReact\b(?!\s*Native)", re.I),
    "React Native": re.compile(r"\bReact\s+Native\b", re.I),
    "Next.js": re.compile(r"\bNext\s*\.?\s*[Jj][Ss]\b"),
    "Vue": re.compile(r"\bVue\s*\.?\s*[Jj][Ss]?\b", re.I),
    "Angular": re.compile(r"\bAngular\b(?!\s*JS)", re.I),
    "GraphQL": re.compile(r"\bGraph\s*QL\b", re.I),
    "REST": re.compile(r"\bREST\s*(?:ful\s*)?API\b", re.I),
    "Docker": re.compile(r"\bDocker\b", re.I),
    "Kubernetes": re.compile(r"\bKubernetes\b|\bK8s\b", re.I),
    "AWS": re.compile(r"\bAWS\b"),
    "Azure": re.compile(r"\bMicrosoft\s+Azure\b|\bAzure\b(?!\s+DevOps)", re.I),
    "GCP": re.compile(r"\bGCP\b|\bGoogle\s+Cloud\b", re.I),
    "Terraform": re.compile(r"\bTerraform\b", re.I),
    "CI/CD": re.compile(r"\bC[I]\s*/\s*C[D]\b"),
    "GitHub Actions": re.compile(r"\bGitHub\s+Actions\b", re.I),
    "Jenkins": re.compile(r"\bJenkins\b", re.I),
    "PostgreSQL": re.compile(r"\bPostgre\s*SQL\b", re.I),
    "MySQL": re.compile(r"\bMySQL\b", re.I),
    "MongoDB": re.compile(r"\bMongo\s*DB\b", re.I),
    "Redis": re.compile(r"\bRedis\b", re.I),
    "SQLAlchemy": re.compile(r"\bSQL\s*Alchemy\b", re.I),
    "Celery": re.compile(r"\bCelery\b", re.I),
    "RabbitMQ": re.compile(r"\bRabbit\s*MQ\b", re.I),
    "Kafka": re.compile(r"\bKafka\b", re.I),
    "Elasticsearch": re.compile(r"\bElastic\s*[Ss]earch\b", re.I),
    "Pandas": re.compile(r"\bPandas\b", re.I),
    "NumPy": re.compile(r"\bNumPy\b|\bNumpy\b", re.I),
    "PyTorch": re.compile(r"\bPyTorch\b", re.I),
    "TensorFlow": re.compile(r"\bTensor\s*[Ff]low\b", re.I),
    "scikit-learn": re.compile(r"\bscikit-?learn\b|Scikit-?[Ll]earn", re.I),
    "LangChain": re.compile(r"\bLang\s*Chain\b", re.I),
    "OpenAI": re.compile(r"\bOpen\s*AI\b|\bChatGPT\b", re.I),
    "Machine Learning": re.compile(r"\bMachine\s+Learning\b", re.I),
    "Rust": re.compile(r"\bRust\b", re.I),
    "Go": re.compile(r"\bGo\s*(?:lang)?\b"),
    "Java": re.compile(r"\bJava\b(?!\s*Script)", re.I),
    "C#": re.compile(r"\bC#\b"),
    "C++": re.compile(r"\bC\+\+\b"),
    "Ruby": re.compile(r"\bRuby\b(?!\s+on\s+Rails)", re.I),
    "Ruby on Rails": re.compile(r"\bRuby\s+on\s+Rails\b", re.I),
    "PHP": re.compile(r"\bPHP\b"),
    "Swift": re.compile(r"\bSwift\b", re.I),
    "Kotlin": re.compile(r"\bKotlin\b", re.I),
    "Flutter": re.compile(r"\bFlutter\b", re.I),
    "Android": re.compile(r"\bAndroid\b", re.I),
    "iOS": re.compile(r"\biOS\b|\bSwiftUI\b"),
    "gRPC": re.compile(r"\bgRPC\b"),
    "WebSocket": re.compile(r"\bWeb\s*Socket\b", re.I),
    "Linux": re.compile(r"\bLinux\b"),
    "Git": re.compile(r"\bGit\b(?!\s*Hub)", re.I),
    "Microservices": re.compile(r"\bMicro\s*services?\b", re.I),
    "Serverless": re.compile(r"\bServerless\b", re.I),
    "DevOps": re.compile(r"\bDev\s*Ops\b", re.I),
    "MLOps": re.compile(r"\bML\s*Ops\b", re.I),
    "Data Engineering": re.compile(r"\bData\s+Engineering\b", re.I),
    "ETL": re.compile(r"\bETL\b"),
    "Airflow": re.compile(r"\bAirflow\b", re.I),
    "Spark": re.compile(r"\bApache\s+Spark\b|\bSpark\b", re.I),
    "Hadoop": re.compile(r"\bHadoop\b", re.I),
    "Selenium": re.compile(r"\bSelenium\b", re.I),
    "Playwright": re.compile(r"\bPlaywright\b", re.I),
    "Cypress": re.compile(r"\bCypress\b", re.I),
    "Pytest": re.compile(r"\bPytest\b", re.I),
    "Jest": re.compile(r"\bJest\b", re.I),
    "Jira": re.compile(r"\bJira\b", re.I),
    "Agile": re.compile(r"\bAgile\b", re.I),
    "Scrum": re.compile(r"\bScrum\b", re.I),
    "Tailwind": re.compile(r"\bTailwind\b", re.I),
    "Bootstrap": re.compile(r"\bBootstrap\b", re.I),
    "Sass": re.compile(r"\bSass\b|\bSCSS\b", re.I),
    "Redux": re.compile(r"\bRedux\b", re.I),
    "MobX": re.compile(r"\bMobX\b", re.I),
    "Snowflake": re.compile(r"\bSnowflake\b", re.I),
    "Databricks": re.compile(r"\bDatabricks\b", re.I),
    "Power BI": re.compile(r"\bPower\s+BI\b", re.I),
    "Tableau": re.compile(r"\bTableau\b", re.I),
    "Figma": re.compile(r"\bFigma\b", re.I),
}


class TechnologyExtractor:
    """Extracts technology names from unstructured text.

    Uses precompiled regex patterns to identify technology keywords
    in job descriptions and plain text.  The approach is deterministic
    and fast — no AI involved.

    Usage::

        extractor = TechnologyExtractor()
        techs = extractor.extract(description)
        # → ["Python", "Docker", "AWS", "PostgreSQL"]
    """

    def __init__(self) -> None:
        self._patterns = TECH_PATTERNS

    def extract(self, text: str | None) -> list[str]:
        if not text:
            return []
        matched: set[str] = set()
        for name, pattern in self._patterns.items():
            if pattern.search(text):
                matched.add(name)
        return sorted(matched)


def extract_technologies(text: str | None) -> list[str]:
    """Convenience function that creates a throwaway extractor."""
    return TechnologyExtractor().extract(text)
