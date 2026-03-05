"""Default rubrics for ISG long-form question types.

These are used when instructors create ISG exams with long_form questions.
Each rubric is structured for the LLM grader (Phase 4) to evaluate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RubricCriterion:
    id: str
    description: str
    max_points: float


@dataclass(frozen=True)
class DefaultRubric:
    rubric_id: str
    name: str
    description: str
    max_score: float
    criteria: tuple[RubricCriterion, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict format compatible with QuestionItem.rubric JSONB."""
        return {
            "max_score": self.max_score,
            "criteria": [
                {
                    "id": c.id,
                    "description": c.description,
                    "max_points": c.max_points,
                }
                for c in self.criteria
            ],
        }


# ---------------------------------------------------------------------------
# Default rubrics for ISG long-form question categories
# ---------------------------------------------------------------------------

RUBRIC_RISK_ASSESSMENT = DefaultRubric(
    rubric_id="isg_risk_assessment",
    name="Risk Değerlendirme Sorusu",
    description=(
        "İşyeri risk değerlendirme senaryolarını analiz eden açık uçlu sorular için rubrik."
    ),
    max_score=20.0,
    criteria=(
        RubricCriterion(
            id="tehlike_tanimlama",
            description="Tehlikelerin doğru ve eksiksiz tanımlanması",
            max_points=5.0,
        ),
        RubricCriterion(
            id="risk_analizi",
            description="Risk seviyesinin doğru analiz edilmesi (olasılık × şiddet)",
            max_points=5.0,
        ),
        RubricCriterion(
            id="kontrol_tedbirleri",
            description="Uygun kontrol tedbirlerinin önerilmesi (hiyerarşiye uygun)",
            max_points=5.0,
        ),
        RubricCriterion(
            id="mevzuat_referans",
            description="İlgili mevzuat ve standartlara doğru atıf yapılması",
            max_points=3.0,
        ),
        RubricCriterion(
            id="anlatim_kalitesi",
            description="Açık, sistematik ve profesyonel anlatım",
            max_points=2.0,
        ),
    ),
)

RUBRIC_WORKPLACE_INSPECTION = DefaultRubric(
    rubric_id="isg_workplace_inspection",
    name="İşyeri Denetim Sorusu",
    description="İşyeri denetim senaryolarını değerlendiren açık uçlu sorular için rubrik.",
    max_score=20.0,
    criteria=(
        RubricCriterion(
            id="uygunsuzluk_tespiti",
            description="Uygunsuzlukların doğru tespit edilmesi",
            max_points=6.0,
        ),
        RubricCriterion(
            id="yasal_dayanak",
            description="Yasal dayanakların belirtilmesi (yönetmelik, tebliğ, standart)",
            max_points=5.0,
        ),
        RubricCriterion(
            id="duzeltici_faaliyet",
            description="Düzeltici ve önleyici faaliyetlerin önerilmesi",
            max_points=5.0,
        ),
        RubricCriterion(
            id="raporlama",
            description="Denetim bulgularının düzgün raporlanması",
            max_points=4.0,
        ),
    ),
)

RUBRIC_ACCIDENT_ANALYSIS = DefaultRubric(
    rubric_id="isg_accident_analysis",
    name="İş Kazası Analiz Sorusu",
    description="İş kazası senaryolarını analiz eden açık uçlu sorular için rubrik.",
    max_score=20.0,
    criteria=(
        RubricCriterion(
            id="kaza_nedenleri",
            description="Kaza nedenlerinin (güvensiz davranış ve koşul) doğru belirlenmesi",
            max_points=6.0,
        ),
        RubricCriterion(
            id="kok_neden",
            description="Kök neden analizinin yapılması",
            max_points=5.0,
        ),
        RubricCriterion(
            id="onleme_onerileri",
            description="Tekrarını önlemeye yönelik tedbirlerin önerilmesi",
            max_points=5.0,
        ),
        RubricCriterion(
            id="bildirim_surec",
            description="Kaza bildirim sürecinin doğru açıklanması (SGK, işveren bildirimi)",
            max_points=4.0,
        ),
    ),
)

RUBRIC_EMERGENCY_PLAN = DefaultRubric(
    rubric_id="isg_emergency_plan",
    name="Acil Durum Planı Sorusu",
    description="Acil durum planlaması ve uygulaması hakkında açık uçlu sorular için rubrik.",
    max_score=20.0,
    criteria=(
        RubricCriterion(
            id="senaryo_tanimlama",
            description="Acil durum senaryolarının doğru tanımlanması",
            max_points=4.0,
        ),
        RubricCriterion(
            id="organizasyon",
            description="Acil durum organizasyonu ve görev dağılımı",
            max_points=5.0,
        ),
        RubricCriterion(
            id="tahliye_proseduru",
            description="Tahliye prosedürünün eksiksiz açıklanması",
            max_points=4.0,
        ),
        RubricCriterion(
            id="iletisim_koordinasyon",
            description="İletişim ve koordinasyon planının açıklanması",
            max_points=4.0,
        ),
        RubricCriterion(
            id="tatbikat_egitim",
            description="Tatbikat ve eğitim gereksinimlerinin belirtilmesi",
            max_points=3.0,
        ),
    ),
)

RUBRIC_LEGISLATION = DefaultRubric(
    rubric_id="isg_legislation",
    name="Mevzuat Yorumlama Sorusu",
    description="İSG mevzuatı yorumlama ve uygulama soruları için rubrik.",
    max_score=15.0,
    criteria=(
        RubricCriterion(
            id="mevzuat_bilgisi",
            description="İlgili mevzuatın doğru belirlenmesi ve aktarılması",
            max_points=5.0,
        ),
        RubricCriterion(
            id="yorum_uygulama",
            description="Mevzuatın senaryoya doğru uygulanması",
            max_points=5.0,
        ),
        RubricCriterion(
            id="sonuc_degerlendirme",
            description="Hukuki sonuçların doğru değerlendirilmesi",
            max_points=5.0,
        ),
    ),
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DEFAULT_RUBRICS: dict[str, DefaultRubric] = {
    r.rubric_id: r
    for r in (
        RUBRIC_RISK_ASSESSMENT,
        RUBRIC_WORKPLACE_INSPECTION,
        RUBRIC_ACCIDENT_ANALYSIS,
        RUBRIC_EMERGENCY_PLAN,
        RUBRIC_LEGISLATION,
    )
}


def get_rubric(rubric_id: str) -> DefaultRubric | None:
    """Return a default rubric by ID."""
    return DEFAULT_RUBRICS.get(rubric_id)


def list_rubrics() -> list[DefaultRubric]:
    """Return all available default rubrics."""
    return list(DEFAULT_RUBRICS.values())


# Map topic IDs to suggested rubric IDs
TOPIC_RUBRIC_MAP: dict[str, str] = {
    "risk_degerlendirme": "isg_risk_assessment",
    "isg_yonetim": "isg_workplace_inspection",
    "is_kazalari": "isg_accident_analysis",
    "mevzuat": "isg_legislation",
}


def get_rubric_for_topic(topic_id: str) -> DefaultRubric | None:
    """Return the suggested default rubric for a given topic."""
    rubric_id = TOPIC_RUBRIC_MAP.get(topic_id)
    if rubric_id is None:
        return None
    return DEFAULT_RUBRICS.get(rubric_id)
