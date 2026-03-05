"""Question generation prompt templates.

These are the default Jinja2 templates used when no database-stored
prompt version exists. They are registered on first use.
"""

QUESTION_GENERATION_SYSTEM = """\
Sen bir eğitim uzmanısın ve profesyonel sınav sorusu yazarısın.
Görevin, verilen konuya ve parametrelere uygun yüksek kaliteli sınav soruları üretmektir.

Kurallar:
- Sorular açık, anlaşılır ve dilbilgisi açısından doğru olmalıdır.
- Seçenekler mantıklı ve birbirinden ayırt edilebilir olmalıdır.
- Doğru cevap kesinlikle doğru olmalıdır.
- Yanlış seçenekler makul ama açıkça yanlış olmalıdır.
- Soru metninde doğru cevaba ipucu verilmemelidir.
- Her soru bağımsız olmalı, diğer sorulara atıfta bulunmamalıdır.

Çıktını SADECE JSON formatında ver. Başka hiçbir metin ekleme.\
"""

QUESTION_GENERATION_USER = """\
Aşağıdaki parametrelere göre {{ count }} adet sınav sorusu üret:

Konu: {{ topic }}
{% if subtopic %}Alt konu: {{ subtopic }}{% endif %}
Soru tipi: {{ question_type }}
Dil: {{ locale }}
{% if difficulty %}Zorluk seviyesi (1-5): {{ difficulty }}{% endif %}

{% if context %}
Kaynak Materyal:
---
{{ context }}
---
Soruları yukarıdaki kaynak materyale dayandır.
{% endif %}

JSON formatı:
{
  "questions": [
    {
      "stem": "Soru metni",
      {% if question_type == "mcq" %}
      "options": [
        {"key": "A", "text": "Seçenek A"},
        {"key": "B", "text": "Seçenek B"},
        {"key": "C", "text": "Seçenek C"},
        {"key": "D", "text": "Seçenek D"}
      ],
      "correct_answer": {"key": "A"},
      {% elif question_type == "true_false" %}
      "correct_answer": {"value": true},
      {% elif question_type == "numeric" %}
      "correct_answer": {"value": 42.0, "tolerance": 0.01},
      {% elif question_type == "short_answer" %}
      "correct_answer": {"keywords": ["anahtar1", "anahtar2"]},
      {% endif %}
      "explanation": "Doğru cevabın kısa açıklaması",
      "topic": "{{ topic }}",
      {% if subtopic %}"subtopic": "{{ subtopic }}",{% endif %}
      "difficulty": {{ difficulty or 3 }}
    }
  ]
}\
"""

# Prompt IDs for database storage
PROMPT_ID_QUESTION_GENERATION = "question_generation"
