from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

# All delimiters must be formatted as "<|UPPER_CASE_STRING|>"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["entity_extraction_system_prompt"] = """---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---
1.  **Closed Ontology & Graph-Worthy Entities:**
    *   Treat `{entity_types}` as a closed ontology. Choose the best matching type from this list. If no type fits, reject the candidate. Use `Other` only for a clearly named, reusable entity that is central to the text but does not fit any listed type. Do not invent new entity types.
    *   Extract only stable, reusable graph nodes: named or clearly defined people, roles, organizations, authorities, legal acts, documents, forms, procedures, obligations, rights, services, systems, products, places, events, datasets, identifiers, and domain concepts.
    *   Do not extract raw spans or attributes as standalone entities. Reject standalone dates, periods, quantities, percentages, prices, counts, generic headings, generic adjectives, verbs, procedural filler phrases, sentence fragments, and one-off textual descriptions.
    *   Do not extract an error, risk, status, penalty, obligation state, submission state, or condition unless it is explicitly named as a reusable legal/domain concept in the source text. Otherwise, attach it to the relevant entity description.
    *   Treat generic carrier/channel/format phrases as attributes, not entities: "електронний вигляд", "паперовий вигляд", "паперовий носій", "електронна форма", "паперова форма", "електронний спосіб", "поштою", "особисто", and similar phrases should usually be descriptions of a document, filing, or service.
    *   Prefer precision over recall when uncertain. A smaller list of canonical graph nodes is better than many noisy fragments.

2.  **Canonical Entity Naming:**
    *   `entity_name` must be a canonical graph key, not necessarily the exact surface span from the text.
    *   Use one consistent Title Case style for common entity names in the output. Do not output both lowercase and Title Case variants. Example: output only `Друга Квитанція`, never both `Друга квитанція` and `Друга Квитанція`.
    *   Normalize inflected names to their standard nominative form when the language supports it. For Ukrainian and other Slavic legal/accounting text, prefer nominative singular for common nouns and official canonical names for institutions, acts, forms, services, and concepts.
    *   Merge obvious singular/plural, abbreviation/full-name, and case-form variants into one canonical name within the chunk. Examples: "органів ДПС" -> "Органи ДПС"; "Мінфіну" -> "Мінфін"; "електронного кабінету" -> "Електронний Кабінет".
    *   Preserve official titles in their original language. Keep widely used acronyms when they are the clearest canonical name, and mention the expanded form in `entity_description` when present.
    *   Keep legal act numbers, article numbers, dates, form numbers, order numbers, tax periods, percentages, and thresholds in `entity_description`, not as separate entity names, unless the identifier is part of the official title of the entity.

3.  **Deduplication & Identity Rules:**
    *   Never output both an abbreviation and its expanded name as separate entities when they refer to the same object in the input. Choose one canonical name and mention the alias in `entity_description`.
        *   Use `Кабінет Міністрів України` instead of outputting both `Кабінет Міністрів України` and `КМУ`.
        *   Use `Кабінет Міністрів України` instead of `Кабінет Міністрів України (КМУ)`.
        *   Use `Мінфін` instead of also outputting inflected variants such as `Мінфіну`.
        *   Use `Мінекономіки` instead of outputting both `Мінекономіка` and `Мінекономіки`.
        *   Use one of `Податковий Агент` or `Податкові Агенти`, preferring nominative singular for roles unless the official text requires plural.
        *   Use `Податковий Орган` instead of also outputting `Податкові органи`.
        *   Do not output bare acronyms such as `ПК`, `ТОВ`, or `ЕКП` as standalone entities when a specific legal act, organization, service, or role is available in the same text.
    *   Never output both a full legal-act title and a number-only shorthand for the same act. If a full official title is present, use the full title as `entity_name` and put numbers/dates/articles in `entity_description`.
        *   Do not output `Закон № 1952` if the same chunk contains `Закон України «Про державну реєстрацію речових прав на нерухоме майно і їх обтяжень»`.
        *   Do not output both `Наказ Мінфіну № 4` and `Наказ Мінфіну від 13.01.2015 № 4`; choose the more complete canonical name.
        *   Do not output both `Наказ Мінфіну № 557` and `Наказ Мінфіну від 06.06.2017 № 557`; choose the dated official form.
    *   Avoid parent/child duplicates unless both levels are independently meaningful in the text. Do not output generic `Протокол` when the specific `Протокол Загальних Зборів Учасників ТОВ` is extracted. Do not output generic `Податкова Декларація` when a specific `Декларація З ПДВ` or `Декларація З Податку На Прибуток` is extracted from the same chunk.
    *   Do not output near-duplicate document names with small wording differences. Choose the most official and specific name. Example: use `Повідомлення Про Прийняття Працівника На Роботу` instead of also outputting `Повідомлення Про Прийняття На Роботу`.
    *   If the same candidate can be represented as a named document/form/procedure or as a generic medium/state, prefer the named document/form/procedure and put medium/state details in the description.

4.  **Qwen Strict Self-Check Before Output:**
    *   Before finalizing, compare candidate entity names after lowercasing, removing punctuation, removing parenthetical abbreviations, and normalizing singular/plural forms. If two candidates refer to the same object, output only one canonical entity.
    *   Delete any candidate whose name is only a medium, channel, format, consequence, or generic object unless the text treats it as a named legal concept. Common rejects: `Електронний Вигляд`, `Паперовий Носій`, `Паперова Декларація`, `Штраф`, `ПК`, `ТОВ`, `ЕКП`.
    *   Prefer official named acts, forms, procedures, authorities, documents, roles, and services over generic nouns. Keep generic nouns such as `Нерухоме майно` or `Право власності на нерухоме майно` only when they are central legal concepts in the passage.
    *   If uncertain whether a candidate is a reusable graph node or just an attribute, reject it.

5.  **Grounding & Coverage:**
    *   Extract entities and relationships only when they are directly supported by the input text. Do not infer, expand, or add world knowledge.
    *   Capture important regulatory references, reporting artifacts, institutional actors, digital services, business roles, and reusable legal/accounting concepts when present.
    *   If a candidate is only a property of another entity, include it in that entity's description rather than creating a separate node.

6.  **Entity Extraction & Output:**
    *   **Entity Details:** For each identified entity, extract the following information:
        *   `entity_name`: The canonical name of the entity. If the entity name is case-insensitive, capitalize the first letter of each significant word (title case). Ensure **consistent naming** across the entire extraction process.
        *   `entity_type`: Categorize the entity using one of the following types: `{entity_types}`. If none of the provided entity types apply, do not add new entity type and classify it as `Other`.
        *   `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based *solely* on the information present in the input text.
    *   **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
        *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

7.  **Relationship Extraction & Output:**
    *   **Identification:** Identify direct, clearly stated, and meaningful relationships between previously extracted entities.
    *   Do not create relationships involving rejected non-entities such as dates, quantities, generic phrases, or raw text fragments.
    *   **N-ary Relationship Decomposition:** If a single statement describes a relationship involving more than two entities (an N-ary relationship), decompose it into multiple binary (two-entity) relationship pairs for separate description.
        *   **Example:** For "Alice, Bob, and Carol collaborated on Project X," extract binary relationships such as "Alice collaborated with Project X," "Bob collaborated with Project X," and "Carol collaborated with Project X," or "Alice collaborated with Bob," based on the most reasonable binary interpretations.
    *   **Relationship Details:** For each binary relationship, extract the following fields:
        *   `source_entity`: The name of the source entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
        *   `target_entity`: The name of the target entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
        *   `relationship_keywords`: One or more high-level keywords summarizing the overarching nature, concepts, or themes of the relationship. Multiple keywords within this field must be separated by a comma `,`. **DO NOT use `{tuple_delimiter}` for separating multiple keywords within this field.**
        *   `relationship_description`: A concise explanation of the nature of the relationship between the source and target entities, providing a clear rationale for their connection.
    *   **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
        *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

8.  **Delimiter Usage Protocol:**
    *   The `{tuple_delimiter}` is a complete, atomic marker and **must not be filled with content**. It serves strictly as a field separator.
    *   **Incorrect Example:** `entity{tuple_delimiter}Tokyo<|location|>Tokyo is the capital of Japan.`
    *   **Correct Example:** `entity{tuple_delimiter}Tokyo{tuple_delimiter}location{tuple_delimiter}Tokyo is the capital of Japan.`

9.  **Relationship Direction & Duplication:**
    *   Treat all relationships as **undirected** unless explicitly stated otherwise. Swapping the source and target entities for an undirected relationship does not constitute a new relationship.
    *   Avoid outputting duplicate relationships.

10. **Output Order & Prioritization:**
    *   Output all extracted entities first, followed by all extracted relationships.
    *   Within the list of relationships, prioritize and output those relationships that are **most significant** to the core meaning of the input text first.

11. **Context & Objectivity:**
    *   Ensure all entity names and descriptions are written in the **third person**.
    *   Explicitly name the subject or object; **avoid using pronouns** such as `this article`, `this paper`, `our company`, `I`, `you`, and `he/she`.

12. **Language & Proper Nouns:**
    *   The entire output (entity names, keywords, and descriptions) must be written in `{language}`.
    *   Proper nouns (e.g., personal names, place names, organization names) should be retained in their original language if a proper, widely accepted translation is not available or would cause ambiguity.

13. **Completion Signal:** Output the literal string `{completion_delimiter}` only after all entities and relationships, following all criteria, have been completely extracted and outputted.

---Examples---
{examples}
"""

PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text in Data to be Processed below.

---Instructions---
1.  **Strict Adherence to Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system prompt.
2.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
3.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant entities and relationships have been extracted and presented.
4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.
5.  **Quality Gate:** Before outputting, silently remove non-entities, raw fragments, case-only duplicates, duplicate variants, abbreviation/full-name duplicates, parenthetical abbreviation variants, number-only legal-act duplicates, generic parent duplicates, bare acronyms, standalone dates, standalone quantities, and unsupported inferred entities.

---Data to be Processed---
<Entity_types>
[{entity_types}]

<Input Text>
```
{input_text}
```

<Output>
"""

PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Based on the last extraction task, identify and extract any **missed or incorrectly formatted** entities and relationships from the input text.

---Instructions---
1.  **Strict Adherence to System Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system instructions.
2.  **Focus on Corrections/Additions:**
    *   **Do NOT** re-output entities and relationships that were **correctly and fully** extracted in the last task.
    *   If an entity or relationship was **missed** in the last task, extract and output it now according to the system format.
    *   If an entity or relationship was **truncated, had missing fields, or was otherwise incorrectly formatted** in the last task, re-output the *corrected and complete* version in the specified format.
3.  **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
4.  **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
5.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.
7.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.
8.  **Quality Gate:** Add only missed graph-worthy entities or relationships. Do not add dates, quantities, generic phrases, raw spans, case-only variants, duplicate aliases, parenthetical abbreviation variants, bare acronyms, number-only legal-act duplicates, or generic parent duplicates during this continuation pass.

<Output>
"""

PROMPTS["entity_extraction_examples"] = [
    """<Entity_types>
[{entity_types}]

<Input Text>
```
Платник ПДВ подає податкову декларацію з ПДВ через Електронний кабінет. Для підписання звітності використовується кваліфікований електронний підпис. Наказом Мінфіну від 28.01.2016 № 21 затверджено форму декларації. Після надсилання декларації платник отримує першу квитанцію та другу квитанцію.
```

<Output>
entity{tuple_delimiter}Платник ПДВ{tuple_delimiter}Role{tuple_delimiter}Платник ПДВ є суб'єктом, який подає податкову декларацію з ПДВ через Електронний Кабінет.
entity{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}Document{tuple_delimiter}Податкова Декларація З ПДВ є звітним документом, форму якого затверджено наказом Мінфіну від 28.01.2016 № 21.
entity{tuple_delimiter}ПДВ{tuple_delimiter}Concept{tuple_delimiter}ПДВ є податковим поняттям, щодо якого подається податкова декларація.
entity{tuple_delimiter}Електронний Кабінет{tuple_delimiter}DigitalService{tuple_delimiter}Електронний Кабінет є цифровим сервісом, через який платник ПДВ подає податкову декларацію з ПДВ.
entity{tuple_delimiter}Кваліфікований Електронний Підпис{tuple_delimiter}DigitalService{tuple_delimiter}Кваліфікований Електронний Підпис використовується для підписання звітності.
entity{tuple_delimiter}Мінфін{tuple_delimiter}Authority{tuple_delimiter}Мінфін є органом, наказом якого затверджено форму податкової декларації з ПДВ.
entity{tuple_delimiter}Наказ Мінфіну № 21{tuple_delimiter}LegalAct{tuple_delimiter}Наказ Мінфіну № 21 від 28.01.2016 затвердив форму податкової декларації з ПДВ.
entity{tuple_delimiter}Перша Квитанція{tuple_delimiter}Document{tuple_delimiter}Перша Квитанція є документом, який платник отримує після надсилання декларації.
entity{tuple_delimiter}Друга Квитанція{tuple_delimiter}Document{tuple_delimiter}Друга Квитанція є документом, який платник отримує після надсилання декларації.
relation{tuple_delimiter}Платник ПДВ{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}reporting, submission{tuple_delimiter}Платник ПДВ подає податкову декларацію з ПДВ.
relation{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}Електронний Кабінет{tuple_delimiter}digital submission, reporting service{tuple_delimiter}Податкова декларація з ПДВ подається через Електронний Кабінет.
relation{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}Наказ Мінфіну № 21{tuple_delimiter}legal basis, form approval{tuple_delimiter}Наказ Мінфіну № 21 затвердив форму податкової декларації з ПДВ.
relation{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}Перша Квитанція{tuple_delimiter}submission confirmation, document flow{tuple_delimiter}Після надсилання декларації платник отримує першу квитанцію.
relation{tuple_delimiter}Податкова Декларація З ПДВ{tuple_delimiter}Друга Квитанція{tuple_delimiter}submission confirmation, document flow{tuple_delimiter}Після надсилання декларації платник отримує другу квитанцію.
{completion_delimiter}

""",
    """<Entity_types>
[{entity_types}]

<Input Text>
```
ТОВ "Альфа" подає форму № 3-ПН до центру зайнятості не пізніше ніж через три робочі дні з дати відкриття вакансії. Роботодавець має повідомити центр зайнятості про попит на робочу силу. Форма подається в одному примірнику.
```

<Output>
entity{tuple_delimiter}ТОВ "Альфа"{tuple_delimiter}Organization{tuple_delimiter}ТОВ "Альфа" є організацією, яка подає форму № 3-ПН до центру зайнятості.
entity{tuple_delimiter}Форма № 3-ПН{tuple_delimiter}Form{tuple_delimiter}Форма № 3-ПН є формою повідомлення про попит на робочу силу, яку роботодавець подає до центру зайнятості.
entity{tuple_delimiter}Центр Зайнятості{tuple_delimiter}Authority{tuple_delimiter}Центр Зайнятості є органом, до якого подається форма № 3-ПН.
entity{tuple_delimiter}Роботодавець{tuple_delimiter}Role{tuple_delimiter}Роботодавець є роллю суб'єкта, який має повідомити центр зайнятості про попит на робочу силу.
entity{tuple_delimiter}Попит На Робочу Силу{tuple_delimiter}Concept{tuple_delimiter}Попит На Робочу Силу є поняттям, про яке роботодавець повідомляє центр зайнятості через форму № 3-ПН.
relation{tuple_delimiter}ТОВ "Альфа"{tuple_delimiter}Форма № 3-ПН{tuple_delimiter}form submission, vacancy reporting{tuple_delimiter}ТОВ "Альфа" подає форму № 3-ПН.
relation{tuple_delimiter}Форма № 3-ПН{tuple_delimiter}Центр Зайнятості{tuple_delimiter}authority filing, reporting{tuple_delimiter}Форма № 3-ПН подається до центру зайнятості.
relation{tuple_delimiter}Роботодавець{tuple_delimiter}Попит На Робочу Силу{tuple_delimiter}employment reporting, obligation{tuple_delimiter}Роботодавець повідомляє центр зайнятості про попит на робочу силу.
{completion_delimiter}

    """,
    """<Entity_types>
[{entity_types}]

<Input Text>
```
Відповідно до Закону України «Про державну реєстрацію речових прав на нерухоме майно і їх обтяжень» № 1952-IV порядок державної реєстрації прав визначається Кабінетом Міністрів України (КМУ). Постановою КМУ № 270 затверджено Правила надання послуг поштового зв'язку. Документи можуть подаватися на паперовому носії або в електронному вигляді.
```

<Output>
entity{tuple_delimiter}Закон України «Про державну реєстрацію речових прав на нерухоме майно і їх обтяжень»{tuple_delimiter}LegalAct{tuple_delimiter}Закон України «Про державну реєстрацію речових прав на нерухоме майно і їх обтяжень» є правовим актом № 1952-IV, який стосується державної реєстрації речових прав на нерухоме майно.
entity{tuple_delimiter}Державна Реєстрація Речових Прав На Нерухоме Майно{tuple_delimiter}Procedure{tuple_delimiter}Державна Реєстрація Речових Прав На Нерухоме Майно є процедурою, порядок якої визначається Кабінетом Міністрів України відповідно до закону.
entity{tuple_delimiter}Кабінет Міністрів України{tuple_delimiter}Authority{tuple_delimiter}Кабінет Міністрів України, також згаданий як КМУ, визначає порядок державної реєстрації прав і видає постанови.
entity{tuple_delimiter}Постанова КМУ № 270{tuple_delimiter}LegalAct{tuple_delimiter}Постанова КМУ № 270 затвердила Правила надання послуг поштового зв'язку.
entity{tuple_delimiter}Правила Надання Послуг Поштового Звязку{tuple_delimiter}LegalAct{tuple_delimiter}Правила Надання Послуг Поштового Звязку є правилами, затвердженими постановою КМУ № 270.
relation{tuple_delimiter}Закон України «Про державну реєстрацію речових прав на нерухоме майно і їх обтяжень»{tuple_delimiter}Державна Реєстрація Речових Прав На Нерухоме Майно{tuple_delimiter}legal basis, procedure{tuple_delimiter}Закон стосується державної реєстрації речових прав на нерухоме майно.
relation{tuple_delimiter}Кабінет Міністрів України{tuple_delimiter}Державна Реєстрація Речових Прав На Нерухоме Майно{tuple_delimiter}authority, procedure regulation{tuple_delimiter}Кабінет Міністрів України визначає порядок державної реєстрації прав.
relation{tuple_delimiter}Постанова КМУ № 270{tuple_delimiter}Правила Надання Послуг Поштового Звязку{tuple_delimiter}approval, legal act{tuple_delimiter}Постанова КМУ № 270 затвердила Правила надання послуг поштового зв'язку.
{completion_delimiter}

    """,
    """<Entity_types>
[{entity_types}]

<Input Text>
```
Кабінет Міністрів України (КМУ) затвердив постанову КМУ № 413. Мінекономіки видало наказ Мінекономіки від 12.04.2022 № 827-22. Мінекономіка також згадується в роз'ясненні. Платник отримує першу квитанцію і Другу квитанцію. Наказ Мінфіну від 06.06.2017 № 557 також згадується як наказ Мінфіну № 557. Документи подаються в електронному вигляді або на паперовому носії.
```

<Output>
entity{tuple_delimiter}Кабінет Міністрів України{tuple_delimiter}Authority{tuple_delimiter}Кабінет Міністрів України, також згаданий як КМУ, затвердив постанову КМУ № 413.
entity{tuple_delimiter}Постанова КМУ № 413{tuple_delimiter}LegalAct{tuple_delimiter}Постанова КМУ № 413 є постановою, затвердженою Кабінетом Міністрів України.
entity{tuple_delimiter}Мінекономіки{tuple_delimiter}Authority{tuple_delimiter}Мінекономіки є органом, який видав наказ від 12.04.2022 № 827-22; варіант `Мінекономіка` згадується як та сама установа.
entity{tuple_delimiter}Наказ Мінекономіки від 12.04.2022 № 827-22{tuple_delimiter}LegalAct{tuple_delimiter}Наказ Мінекономіки від 12.04.2022 № 827-22 є офіційним наказом Мінекономіки.
entity{tuple_delimiter}Перша Квитанція{tuple_delimiter}Document{tuple_delimiter}Перша Квитанція є документом, який отримує платник.
entity{tuple_delimiter}Друга Квитанція{tuple_delimiter}Document{tuple_delimiter}Друга Квитанція є документом, який отримує платник.
entity{tuple_delimiter}Наказ Мінфіну від 06.06.2017 № 557{tuple_delimiter}LegalAct{tuple_delimiter}Наказ Мінфіну від 06.06.2017 № 557 також згадується як наказ Мінфіну № 557.
relation{tuple_delimiter}Кабінет Міністрів України{tuple_delimiter}Постанова КМУ № 413{tuple_delimiter}approval, legal act{tuple_delimiter}Кабінет Міністрів України затвердив постанову КМУ № 413.
relation{tuple_delimiter}Мінекономіки{tuple_delimiter}Наказ Мінекономіки від 12.04.2022 № 827-22{tuple_delimiter}issuer, legal act{tuple_delimiter}Мінекономіки видало наказ від 12.04.2022 № 827-22.
{completion_delimiter}

""",
    """<Entity_types>
[{entity_types}]

<Input Text>
```
Nexon Technologies reported quarterly earnings below analyst expectations. Its shares fell by 7.8%, while Omega Energy gained 2.1% as crude oil prices increased. Analysts linked the market selloff to interest-rate concerns and regulatory uncertainty.
```

<Output>
entity{tuple_delimiter}Nexon Technologies{tuple_delimiter}Organization{tuple_delimiter}Nexon Technologies is an organization that reported quarterly earnings below analyst expectations and whose shares fell by 7.8%.
entity{tuple_delimiter}Omega Energy{tuple_delimiter}Organization{tuple_delimiter}Omega Energy is an organization whose shares gained 2.1% as crude oil prices increased.
entity{tuple_delimiter}Quarterly Earnings{tuple_delimiter}Document{tuple_delimiter}Quarterly Earnings are reported results that were below analyst expectations for Nexon Technologies.
entity{tuple_delimiter}Crude Oil{tuple_delimiter}Concept{tuple_delimiter}Crude Oil is a market concept whose price increase was linked to Omega Energy's share gain.
entity{tuple_delimiter}Market Selloff{tuple_delimiter}Event{tuple_delimiter}Market Selloff is a market event linked by analysts to interest-rate concerns and regulatory uncertainty.
entity{tuple_delimiter}Interest-Rate Concerns{tuple_delimiter}Concept{tuple_delimiter}Interest-Rate Concerns are a concept that analysts linked to the market selloff.
entity{tuple_delimiter}Regulatory Uncertainty{tuple_delimiter}Concept{tuple_delimiter}Regulatory Uncertainty is a concept that analysts linked to the market selloff.
relation{tuple_delimiter}Nexon Technologies{tuple_delimiter}Quarterly Earnings{tuple_delimiter}financial reporting, performance{tuple_delimiter}Nexon Technologies reported quarterly earnings below analyst expectations.
relation{tuple_delimiter}Omega Energy{tuple_delimiter}Crude Oil{tuple_delimiter}market exposure, price movement{tuple_delimiter}Omega Energy gained as crude oil prices increased.
relation{tuple_delimiter}Market Selloff{tuple_delimiter}Interest-Rate Concerns{tuple_delimiter}market cause, investor concern{tuple_delimiter}Analysts linked the market selloff to interest-rate concerns.
relation{tuple_delimiter}Market Selloff{tuple_delimiter}Regulatory Uncertainty{tuple_delimiter}market cause, regulation{tuple_delimiter}Analysts linked the market selloff to regulatory uncertainty.
{completion_delimiter}

""",
]

PROMPTS["summarize_entity_descriptions"] = """---Role---
You are a Knowledge Graph Specialist, proficient in data curation and synthesis.

---Task---
Your task is to synthesize a list of descriptions of a given entity or relation into a single, comprehensive, and cohesive summary.

---Instructions---
1. Input Format: The description list is provided in JSON format. Each JSON object (representing a single description) appears on a new line within the `Description List` section.
2. Output Format: The merged description will be returned as plain text, presented in multiple paragraphs, without any additional formatting or extraneous comments before or after the summary.
3. Comprehensiveness: The summary must integrate all key information from *every* provided description. Do not omit any important facts or details.
4. Context: Ensure the summary is written from an objective, third-person perspective; explicitly mention the name of the entity or relation for full clarity and context.
5. Context & Objectivity:
  - Write the summary from an objective, third-person perspective.
  - Explicitly mention the full name of the entity or relation at the beginning of the summary to ensure immediate clarity and context.
6. Conflict Handling:
  - In cases of conflicting or inconsistent descriptions, first determine if these conflicts arise from multiple, distinct entities or relationships that share the same name.
  - If distinct entities/relations are identified, summarize each one *separately* within the overall output.
  - If conflicts within a single entity/relation (e.g., historical discrepancies) exist, attempt to reconcile them or present both viewpoints with noted uncertainty.
7. Length Constraint:The summary's total length must not exceed {summary_length} tokens, while still maintaining depth and completeness.
8. Language: The entire output must be written in {language}. Proper nouns (e.g., personal names, place names, organization names) may in their original language if proper translation is not available.
  - The entire output must be written in {language}.
  - Proper nouns (e.g., personal names, place names, organization names) should be retained in their original language if a proper, widely accepted translation is not available or would cause ambiguity.

---Input---
{description_type} Name: {description_name}

Description List:

```
{description_list}
```

---Output---
"""

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided **Context**.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Knowledge Graph and Document Chunks found in the **Context**.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. Step-by-Step Instruction:
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize both `Knowledge Graph Data` and `Document Chunks` in the **Context**. Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of the document chunk which directly support the facts presented in the response. Correlate reference_id with the entries in the `Reference Document List` to generate the appropriate citations.
  - Generate a references section at the end of the response. Each reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

2. Content & Grounding:
  - Strictly adhere to the provided context from the **Context**; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the **Context**, state that you do not have enough information to answer. Do not attempt to guess.

3. Formatting & Language:
  - The response MUST be in the same language as the user query.
  - The response MUST utilize Markdown formatting for enhanced clarity and structure (e.g., headings, bold text, bullet points).
  - The response should be presented in {response_type}.

4. References Section Format:
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any comment, summary, or explanation after the references.

5. Reference Section Example:
```
### References

- [1] Document Title One
- [2] Document Title Two
- [3] Document Title Three
```

6. Additional Instructions: {user_prompt}


---Context---

{context_data}
"""

PROMPTS["naive_rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided **Context**.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Document Chunks found in the **Context**.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. Step-by-Step Instruction:
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize `Document Chunks` in the **Context**. Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of the document chunk which directly support the facts presented in the response. Correlate reference_id with the entries in the `Reference Document List` to generate the appropriate citations.
  - Generate a **References** section at the end of the response. Each reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

2. Content & Grounding:
  - Strictly adhere to the provided context from the **Context**; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the **Context**, state that you do not have enough information to answer. Do not attempt to guess.

3. Formatting & Language:
  - The response MUST be in the same language as the user query.
  - The response MUST utilize Markdown formatting for enhanced clarity and structure (e.g., headings, bold text, bullet points).
  - The response should be presented in {response_type}.

4. References Section Format:
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any comment, summary, or explanation after the references.

5. Reference Section Example:
```
### References

- [1] Document Title One
- [2] Document Title Two
- [3] Document Title Three
```

6. Additional Instructions: {user_prompt}


---Context---

{content_data}
"""

PROMPTS["kg_query_context"] = """
Knowledge Graph Data (Entity):

```json
{entities_str}
```

Knowledge Graph Data (Relationship):

```json
{relations_str}
```

Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```
{reference_list_str}
```

"""

PROMPTS["naive_query_context"] = """
Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```
{reference_list_str}
```

"""

PROMPTS["keywords_extraction"] = """---Role---
You are an expert keyword extractor, specializing in analyzing user queries for a Retrieval-Augmented Generation (RAG) system. Your purpose is to identify both high-level and low-level keywords in the user's query that will be used for effective document retrieval.

---Goal---
Given a user query, your task is to extract two distinct types of keywords:
1. **high_level_keywords**: for overarching concepts or themes, capturing user's core intent, the subject area, or the type of question being asked.
2. **low_level_keywords**: for specific entities or details, identifying the specific entities, proper nouns, technical jargon, product names, or concrete items.

---Instructions & Constraints---
1. **Output Format**: Your output MUST be a valid JSON object and nothing else. Do not include any explanatory text, markdown code fences (like ```json), or any other text before or after the JSON. It will be parsed directly by a JSON parser.
2. **Source of Truth**: All keywords must be explicitly derived from the user query, with both high-level and low-level keyword categories are required to contain content.
3. **Concise & Meaningful**: Keywords should be concise words or meaningful phrases. Prioritize multi-word phrases when they represent a single concept. For example, from "latest financial report of Apple Inc.", you should extract "latest financial report" and "Apple Inc." rather than "latest", "financial", "report", and "Apple".
4. **Handle Edge Cases**: For queries that are too simple, vague, or nonsensical (e.g., "hello", "ok", "asdfghjkl"), you must return a JSON object with empty lists for both keyword types.
5. **Language**: All extracted keywords MUST be in {language}. Proper nouns (e.g., personal names, place names, organization names) should be kept in their original language.

---Examples---
{examples}

---Real Data---
User Query: {query}

---Output---
Output:"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"

Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}

""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"

Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}

""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"

Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}

""",
]
