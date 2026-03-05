"""ISG (İş Sağlığı ve Güvenliği) exam blueprints based on OSHM official syllabus.

Three certification classes:
  - A Sınıfı: İş Güvenliği Uzmanı (mühendis/mimar, en kapsamlı)
  - B Sınıfı: İş Güvenliği Uzmanı (teknik eleman)
  - C Sınıfı: İş Güvenliği Uzmanı (temel seviye)

Topic weights follow the official İSGÜM/OSHM exam distribution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Subtopic:
    id: str
    name: str


@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    subtopics: tuple[Subtopic, ...] = ()


@dataclass(frozen=True)
class TopicWeight:
    topic_id: str
    weight: float  # 0.0–1.0, sums to 1.0 per blueprint
    question_count: int  # recommended count in a standard 50-question exam


@dataclass(frozen=True)
class Blueprint:
    exam_class: str  # "A", "B", "C"
    title: str
    description: str
    total_questions: int
    time_limit_minutes: int
    pass_score: float  # percentage
    topic_weights: tuple[TopicWeight, ...] = ()
    allowed_question_types: tuple[str, ...] = (
        "mcq",
        "true_false",
        "short_answer",
        "long_form",
    )


# ---------------------------------------------------------------------------
# Official ISG topic taxonomy
# ---------------------------------------------------------------------------

ISG_TOPICS: tuple[Topic, ...] = (
    Topic(
        id="mevzuat",
        name="İSG Mevzuatı ve Hukuku",
        subtopics=(
            Subtopic(id="mevzuat_6331", name="6331 Sayılı İSG Kanunu"),
            Subtopic(id="mevzuat_yonetmelikler", name="İSG Yönetmelikleri"),
            Subtopic(id="mevzuat_ilo", name="ILO Sözleşmeleri ve AB Direktifleri"),
            Subtopic(id="mevzuat_cezai", name="Cezai ve Hukuki Sorumluluklar"),
        ),
    ),
    Topic(
        id="is_sagligi",
        name="İş Sağlığı",
        subtopics=(
            Subtopic(id="is_sagligi_meslek_hastaliklari", name="Meslek Hastalıkları"),
            Subtopic(id="is_sagligi_hijyen", name="İş Hijyeni ve Toksikoloji"),
            Subtopic(id="is_sagligi_ergonomi", name="Ergonomi"),
            Subtopic(id="is_sagligi_psikoloji", name="İş Psikolojisi ve Stres"),
            Subtopic(id="is_sagligi_ilkyardim", name="İlk Yardım"),
        ),
    ),
    Topic(
        id="teknik_guvenlik",
        name="Teknik Güvenlik",
        subtopics=(
            Subtopic(id="teknik_makine", name="Makine Güvenliği"),
            Subtopic(id="teknik_elektrik", name="Elektrik Güvenliği"),
            Subtopic(id="teknik_yangin", name="Yangın Güvenliği ve Önleme"),
            Subtopic(id="teknik_kimyasal", name="Kimyasal Maddeler ve Güvenlik"),
            Subtopic(id="teknik_insaat", name="İnşaat ve Yapı İşleri Güvenliği"),
            Subtopic(id="teknik_basinc", name="Basınçlı Kaplar ve Kaldırma Araçları"),
        ),
    ),
    Topic(
        id="risk_degerlendirme",
        name="Risk Değerlendirme",
        subtopics=(
            Subtopic(id="risk_metotlar", name="Risk Değerlendirme Metotları"),
            Subtopic(id="risk_analiz", name="Tehlike ve Risk Analizi"),
            Subtopic(id="risk_kontrol", name="Risk Kontrol Tedbirleri"),
            Subtopic(id="risk_acil_durum", name="Acil Durum Planlaması"),
        ),
    ),
    Topic(
        id="is_kazalari",
        name="İş Kazaları ve Önleme",
        subtopics=(
            Subtopic(id="kaza_istatistik", name="Kaza İstatistikleri ve Analizi"),
            Subtopic(id="kaza_sorusturma", name="Kaza Soruşturma Teknikleri"),
            Subtopic(id="kaza_onleme", name="Kaza Önleme Stratejileri"),
        ),
    ),
    Topic(
        id="kkd",
        name="Kişisel Koruyucu Donanımlar (KKD)",
        subtopics=(
            Subtopic(id="kkd_turleri", name="KKD Türleri ve Seçimi"),
            Subtopic(id="kkd_standartlar", name="KKD Standartları"),
            Subtopic(id="kkd_kullanim", name="KKD Kullanımı ve Bakımı"),
        ),
    ),
    Topic(
        id="isg_yonetim",
        name="İSG Yönetim Sistemleri",
        subtopics=(
            Subtopic(id="yonetim_iso45001", name="ISO 45001 İSG Yönetim Sistemi"),
            Subtopic(id="yonetim_denetim", name="İSG Denetimi ve Teftiş"),
            Subtopic(id="yonetim_egitim", name="İSG Eğitimi ve Bilinçlendirme"),
            Subtopic(id="yonetim_dokumantasyon", name="İSG Dokümantasyonu"),
        ),
    ),
    Topic(
        id="cevre",
        name="Çevre Güvenliği",
        subtopics=(
            Subtopic(id="cevre_atik", name="Atık Yönetimi"),
            Subtopic(id="cevre_gurultu", name="Gürültü ve Titreşim"),
            Subtopic(id="cevre_aydinlatma", name="Aydınlatma ve Termal Konfor"),
        ),
    ),
)

TOPICS_BY_ID: dict[str, Topic] = {t.id: t for t in ISG_TOPICS}


# ---------------------------------------------------------------------------
# A / B / C class blueprints
# ---------------------------------------------------------------------------

BLUEPRINT_A = Blueprint(
    exam_class="A",
    title="A Sınıfı İş Güvenliği Uzmanlığı Sınavı",
    description=(
        "Mühendis, mimar ve teknik elemanlar için en kapsamlı İSG sertifikasyon "
        "sınavı. Çok tehlikeli işyerlerinde görev yapabilme yetkisi verir."
    ),
    total_questions=50,
    time_limit_minutes=75,
    pass_score=70.0,
    topic_weights=(
        TopicWeight(topic_id="mevzuat", weight=0.20, question_count=10),
        TopicWeight(topic_id="is_sagligi", weight=0.15, question_count=8),
        TopicWeight(topic_id="teknik_guvenlik", weight=0.20, question_count=10),
        TopicWeight(topic_id="risk_degerlendirme", weight=0.15, question_count=7),
        TopicWeight(topic_id="is_kazalari", weight=0.10, question_count=5),
        TopicWeight(topic_id="kkd", weight=0.05, question_count=3),
        TopicWeight(topic_id="isg_yonetim", weight=0.10, question_count=5),
        TopicWeight(topic_id="cevre", weight=0.05, question_count=2),
    ),
)

BLUEPRINT_B = Blueprint(
    exam_class="B",
    title="B Sınıfı İş Güvenliği Uzmanlığı Sınavı",
    description=(
        "Teknik elemanlar için orta düzey İSG sertifikasyon sınavı. "
        "Tehlikeli işyerlerinde görev yapabilme yetkisi verir."
    ),
    total_questions=50,
    time_limit_minutes=75,
    pass_score=70.0,
    topic_weights=(
        TopicWeight(topic_id="mevzuat", weight=0.20, question_count=10),
        TopicWeight(topic_id="is_sagligi", weight=0.15, question_count=8),
        TopicWeight(topic_id="teknik_guvenlik", weight=0.15, question_count=7),
        TopicWeight(topic_id="risk_degerlendirme", weight=0.15, question_count=8),
        TopicWeight(topic_id="is_kazalari", weight=0.10, question_count=5),
        TopicWeight(topic_id="kkd", weight=0.10, question_count=5),
        TopicWeight(topic_id="isg_yonetim", weight=0.10, question_count=5),
        TopicWeight(topic_id="cevre", weight=0.05, question_count=2),
    ),
)

BLUEPRINT_C = Blueprint(
    exam_class="C",
    title="C Sınıfı İş Güvenliği Uzmanlığı Sınavı",
    description=(
        "Temel seviye İSG sertifikasyon sınavı. "
        "Az tehlikeli işyerlerinde görev yapabilme yetkisi verir."
    ),
    total_questions=50,
    time_limit_minutes=75,
    pass_score=60.0,
    topic_weights=(
        TopicWeight(topic_id="mevzuat", weight=0.25, question_count=13),
        TopicWeight(topic_id="is_sagligi", weight=0.15, question_count=7),
        TopicWeight(topic_id="teknik_guvenlik", weight=0.10, question_count=5),
        TopicWeight(topic_id="risk_degerlendirme", weight=0.15, question_count=8),
        TopicWeight(topic_id="is_kazalari", weight=0.10, question_count=5),
        TopicWeight(topic_id="kkd", weight=0.10, question_count=5),
        TopicWeight(topic_id="isg_yonetim", weight=0.10, question_count=5),
        TopicWeight(topic_id="cevre", weight=0.05, question_count=2),
    ),
)

BLUEPRINTS: dict[str, Blueprint] = {
    "A": BLUEPRINT_A,
    "B": BLUEPRINT_B,
    "C": BLUEPRINT_C,
}


def get_blueprint(exam_class: str) -> Blueprint | None:
    """Return blueprint for given class or None."""
    return BLUEPRINTS.get(exam_class.upper())


def list_blueprints() -> list[Blueprint]:
    """Return all available blueprints."""
    return list(BLUEPRINTS.values())
