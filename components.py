"""Component registry for Loginom .lgp MCP builder."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentInfo:
    key: str
    title: str
    category: str
    vendor: str
    engine: str
    # logical ports for linking (name -> guid)
    inputs: dict[str, str]
    outputs: dict[str, str]
    # extra kwargs accepted by add_node
    options: tuple[str, ...] = ()


# Shared port GUIDs
P_DS_IN = "9dc72a3f-56bf-3bfc-84ec-f979daf4da6b"
P_DS_OUT = "4ba0e2c2-69ad-3a32-bbdc-75714efe7a51"
P_DS_ELSE = "99559aff-aff4-3e08-8f1e-a290790bba03"
P_DATASET = "58f7e6c3-511e-39d7-8853-036e0a1a7612"
P_MAIN = "e028600d-9dca-3604-89ce-cd2fdadb4c1c"
P_JOINED = "54ae772d-7bcb-36bb-88ac-976dcae031bc"
P_VARS = "d252e390-f72d-36c4-97fc-60d86186c3c6"
P_VARS_OUT = "b671426b-642b-3e7c-b9a9-9653573f3199"
P_JOINED_VARS = "0054b2b7-4a88-3344-9b91-53d2cf60adfe"
P_COLUNION_JOINED = "5a7adf70-52aa-4223-b40b-6b7837d98359"
P_SUPPORT = "7957ead3-e5a4-3fdc-a6f6-257da214aec9"
P_UNGROUP_OUT = "b1b9a7d7-acab-3f13-a8cc-e93ad801d966"
P_UNGROUP_STATS = "c1517ce9-666e-3c4d-b6dc-de107adf927a"
P_RANGES_IN = "8ae3195f-164d-3b58-8868-6b02979f28d1"
P_RANGES_OUT = "26d376d8-9a60-3baa-b210-be00b095e5aa"
P_OUT_DATA = "87ef0491-b8e1-3fe2-aad7-3d3f6ca39174"
P_OUT_OUTLIERS = "d4871709-2ee7-3c6a-bd72-d65885a82746"
P_OUT_EXTR = "b635a828-1df5-35c7-a5bd-e27f652fcc4a"
P_PART_COMMON = "289668ce-a35b-36f7-a4c7-7e9819fb3fc8"
P_PART_TEACH = "51c20538-def7-374c-851c-a318298b9c80"
P_PART_TEST = "0b3d620f-18d5-38da-8d37-7159844f74d8"
P_XSD = "fd34ec8d-296a-3c2c-8eb3-efab884ae3cd"
P_CLASS_PARAMS = "114f9a7f-dfa1-3fdd-ac79-86d7e23d8310"
P_BINNING_PARAMS = "6ae2fc3e-b405-386e-9c97-7f04bc23d3ee"
P_CONNECTION = "78ce58f4-e818-3754-bc2e-6af868677420"
P_RESULT_STATUS = "078588da-9edb-35aa-9cff-3f8a5b66b073"

TRANSFORM_IO = (
    {"data": P_DS_IN},
    {"data": P_DS_OUT},
)
TWO_TABLE_IO = (
    {"main": P_MAIN, "joined": P_JOINED},
    {"data": P_DS_OUT},
)
IMPORT_IO = (
    {},
    {"data": P_DATASET},
)

COMPONENTS: dict[str, ComponentInfo] = {
    "import_native": ComponentInfo(
        "import_native",
        "Импорт Loginom Data",
        "import",
        "35a6e054-ee0c-42f6-bda6-af10b57a36aa",
        "TBGImportNative",
        *IMPORT_IO,
        options=("file_name",),
    ),
    "import_text": ComponentInfo(
        "import_text",
        "Текстовый файл",
        "import",
        "dd767700-1321-4c70-ab92-2acfc4db4492",
        "TBGImportTextFile",
        *IMPORT_IO,
        options=("file_name",),
    ),
    "import_excel": ComponentInfo(
        "import_excel",
        "Excel файл",
        "import",
        "b391583d-e11b-4ee3-96ce-1438f9d3df5d",
        "TBGImportExcelFileEngine",
        *IMPORT_IO,
        options=("file_name",),
    ),
    "sorting": ComponentInfo(
        "sorting", "Сортировка", "transform",
        "62a25d53-677f-45ef-abe7-537dfdc2ea4b", "TBGSortingEngine", *TRANSFORM_IO,
    ),
    "reform_columns": ComponentInfo(
        "reform_columns", "Параметры полей", "transform",
        "dc279f34-55cf-4fee-8bb4-e10de32c88f2", "TBGReformColumnsEngine", *TRANSFORM_IO,
    ),
    "calculator": ComponentInfo(
        "calculator", "Калькулятор", "transform",
        "c7b69712-557f-4e51-bba5-db9cc2659e7a", "TBGCalcData",
        {"data": P_DS_IN, "variables": P_VARS},
        {"data": P_DS_OUT},
    ),
    "datetime": ComponentInfo(
        "datetime", "Дата и время", "transform",
        "d21f2169-20c2-4ca3-85e3-5279e52aeebc", "TBGDateReformEngine", *TRANSFORM_IO,
    ),
    "grouping": ComponentInfo(
        "grouping", "Группировка", "transform",
        "4d4f2852-8a7d-4993-84f0-5b488029b1a7", "TBGGroupDataEngine", *TRANSFORM_IO,
    ),
    "replace": ComponentInfo(
        "replace", "Замена", "transform",
        "5346793b-a4f9-40f2-ae49-b14c731bd0f2", "TBGCustomModelComponentEngine", *TRANSFORM_IO,
    ),
    "filter": ComponentInfo(
        "filter", "Фильтр строк", "transform",
        "a0e49d86-6fe3-43fc-8046-29d1ce92c03d", "TBGFilterDataEngine",
        {"data": P_DS_IN},
        {"data": P_DS_OUT, "else": P_DS_ELSE},
    ),
    "union": ComponentInfo(
        "union", "Объединение", "multi",
        "f5aa91d2-9fe5-439d-9f7f-1e17996da272", "TBGUnionDataEngine", *TWO_TABLE_IO,
    ),
    "join": ComponentInfo(
        "join", "Слияние", "multi",
        "7197af14-a6cc-479c-acc6-9867bc970205", "TBGJoinDataEngine", *TWO_TABLE_IO,
    ),
    "enrich": ComponentInfo(
        "enrich", "Дополнение данных", "multi",
        "0370e80a-78e1-4ede-b71b-930497994b44", "TBGEnrichDataEngine", *TWO_TABLE_IO,
    ),
    # remaining Transformation
    "colunion": ComponentInfo(
        "colunion", "Соединение", "multi",
        "43c697b8-a02f-4ad3-b0e4-d8cdfee83ae5", "TBGColUnionDataEngine",
        {"main": P_MAIN, "joined": P_COLUNION_JOINED},
        {"data": P_DS_OUT},
    ),
    "collapse_columns": ComponentInfo(
        "collapse_columns", "Свёртка столбцов", "transform",
        "247b449c-c2c9-495a-b539-7f8ab78ef5bf", "TBGColumnFlippingEngine", *TRANSFORM_IO,
    ),
    "crosstab": ComponentInfo(
        "crosstab", "Кросс-таблица", "transform",
        "418295a8-c71e-48e5-89fa-abd1de8b3f9d", "TBGCrossTabEngine", *TRANSFORM_IO,
    ),
    "sampling": ComponentInfo(
        "sampling", "Сэмплинг", "preprocess",
        "c1f70531-6c5e-42f1-a249-53a7ff269e26", "TBGSamplingEngine", *TRANSFORM_IO,
    ),
    # Export
    "export_text": ComponentInfo(
        "export_text", "Экспорт в текстовый файл", "export",
        "767b14f8-3852-4463-9ede-7345c4ddb183", "TBGExportTextFile",
        {"data": P_DS_IN},
        {},
        options=("file_name",),
    ),
    "export_excel": ComponentInfo(
        "export_excel", "Экспорт в Excel", "export",
        "45694995-9a46-4b18-a87a-bfbfa5a74eed", "TBGExportExcelFile",
        {"data": P_DS_IN},
        {},
        options=("file_name",),
    ),
    # Variables
    "calc_variables": ComponentInfo(
        "calc_variables", "Калькулятор (переменные)", "variables",
        "3cff62aa-e3b0-4505-b2f0-90bb23b87875", "TBGCalcVariables",
        {"variables": P_VARS},
        {"variables": P_VARS_OUT},
    ),
    "vars_to_table": ComponentInfo(
        "vars_to_table", "Переменные в таблицу", "variables",
        "b00d1d89-0386-4fdd-a404-f7ef26ffcd25", "TBGVariablesToDataEngine",
        {"variables": P_VARS},
        {"data": P_DS_OUT},
    ),
    "table_to_vars": ComponentInfo(
        "table_to_vars", "Таблица в переменные", "variables",
        "c0c06e4e-da43-4f30-b2dd-d95ade0e5970", "TBGCustomModelComponentEngine",
        {"data": P_DS_IN},
        {"variables": P_VARS_OUT},
    ),
    "join_variables": ComponentInfo(
        "join_variables", "Соединение (переменные)", "variables",
        "b4432322-a745-46b0-93cb-83ac194d8adb", "TBGCustomModelComponentEngine",
        {"variables": P_VARS, "joined": P_JOINED_VARS},
        {"variables": P_VARS_OUT},
    ),
    # G1 transform
    "ungroup": ComponentInfo(
        "ungroup", "Разгруппировка", "transform",
        "e7a4849d-3f92-4636-8efc-cae078129e65", "TBGUngroupDataEngine",
        {"data": P_DS_IN, "support": P_SUPPORT},
        {"data": P_UNGROUP_OUT, "stats": P_UNGROUP_STATS},
    ),
    "sliding_window": ComponentInfo(
        "sliding_window", "Скользящее окно", "transform",
        "4b7b4a8c-0c25-4496-94aa-216fc9e252de", "TBGSlidingWindowEngine",
        *TRANSFORM_IO,
    ),
    # G2 variables
    "replace_variables": ComponentInfo(
        "replace_variables", "Замена (переменные)", "variables",
        "f2c44372-4b7c-41ae-99f5-a3d52d418d90", "TBGCustomModelComponentEngine",
        {"variables": P_VARS},
        {"variables": P_VARS_OUT},
    ),
    # G3 preprocess
    "imputation": ComponentInfo(
        "imputation", "Заполнение пропусков", "preprocess",
        "77ecdc2c-735e-4f23-a95e-c510320308b3", "TBGDataRecoveryEngine", *TRANSFORM_IO,
    ),
    "quantize": ComponentInfo(
        "quantize", "Квантование", "preprocess",
        "a0c05046-e72b-4d8f-8689-1385fa7f14d6", "TBGBinningEngine",
        {"data": P_DS_IN, "ranges": P_RANGES_IN},
        {"data": P_DS_OUT, "ranges": P_RANGES_OUT},
    ),
    "final_classes": ComponentInfo(
        "final_classes", "Конечные классы", "preprocess",
        "5c25727f-f53f-44b3-89cc-9570afe0f294", "TBGCoarseClassesEngine",
        {"data": P_DS_IN},
        {"data": P_DS_OUT, "class_params": P_CLASS_PARAMS, "binning_params": P_BINNING_PARAMS},
    ),
    "partition": ComponentInfo(
        "partition", "Разбиение на множества", "preprocess",
        "b2161dca-d25a-440e-8833-813d4af7c5f6", "TBGPartitionEngine",
        {"data": P_DS_IN},
        {"common": P_PART_COMMON, "teach": P_PART_TEACH, "test": P_PART_TEST},
    ),
    "outliers": ComponentInfo(
        "outliers", "Редактирование выбросов", "preprocess",
        "6c638720-bbff-4d42-8c18-eb14f3e3cca6", "TBGElimOutlierEngine",
        {"data": P_DS_IN},
        {"data": P_OUT_DATA, "outliers": P_OUT_OUTLIERS, "extreme": P_OUT_EXTR},
    ),
    "smoothing": ComponentInfo(
        "smoothing", "Сглаживание", "preprocess",
        "73aad18e-9b22-4667-9feb-94ee1cae948e", "TBGCustomModelComponentEngine", *TRANSFORM_IO,
    ),
    # G4 import
    "import_xml": ComponentInfo(
        "import_xml", "XML файл", "import",
        "f678ea95-0484-46a4-ab42-e03739a40cc6", "TBGImportXML",
        {},
        {"data": P_DATASET},
        options=("file_name",),
    ),
    "import_db": ComponentInfo(
        "import_db", "База данных", "import",
        "e8491d9e-c797-4acf-beb2-220bd39331e7", "TBGDBImport",
        {"connection": P_CONNECTION},
        {"data": P_DATASET, "status": P_RESULT_STATUS},
    ),
    "import_1c": ComponentInfo(
        "import_1c", "1С:Предприятие 8 Запрос", "import",
        "0eea96bc-66b8-475f-a7bb-6fc572577392", "TBG1Cv8QueryImport",
        {"connection": P_CONNECTION},
        {"data": P_DATASET},
    ),
    "import_warehouse": ComponentInfo(
        "import_warehouse", "Deductor Warehouse", "import",
        "e9c33e31-d53c-43d6-9ea6-568a830a02d4", "TBGDWExtract",
        {"connection": P_CONNECTION},
        {"data": P_DATASET},
    ),
    # G5 export
    "export_xml": ComponentInfo(
        "export_xml", "Экспорт в XML", "export",
        "5036451c-e1fc-4bb5-aa32-bf9302af7c7d", "TBGExportXML",
        {"connection": P_CONNECTION, "data": P_DS_IN, "xsd": P_XSD},
        {},
        options=("file_name",),
    ),
    "export_native": ComponentInfo(
        "export_native", "Экспорт Loginom Data", "export",
        "70fd0efe-6caa-4151-95e0-1868586e32c9", "TBGExportNative",
        {"connection": P_CONNECTION, "data": P_DS_IN},
        {},
        options=("file_name",),
    ),
    "export_db": ComponentInfo(
        "export_db", "Экспорт в базу данных", "export",
        "44bdaed5-66f9-4fe6-b7db-b93febb77b3a", "TBGDBExport",
        {"connection": P_CONNECTION, "data": P_DS_IN},
        {"status": P_RESULT_STATUS},
    ),
    "export_warehouse": ComponentInfo(
        "export_warehouse", "Экспорт Deductor Warehouse", "export",
        "e6358791-8f62-4de2-b6e3-5da388597806", "TBGDWLoad",
        {"connection": P_CONNECTION, "data": P_DS_IN},
        {},
    ),
}

# --- G6: Control / Research / Data Mining / Data Tree / Integration ---
# Port GUIDs and vendors from Cursor_G6.lgp (blob-backed builders).
_G6 = [
    ("run_node", "Выполнение узла", "control", "f2b7b8c5-ac4b-403f-a99e-d64fb4ae0d10", "TBGExecNodeComponent", {}, {}),
    ("submodel", "Подмодель", "control", "a38d1b44-ce57-4f4c-9357-2adb8697d6f3", "TBGModelGenericComponentEngine", {}, {}),
    ("reference_node", "Узел-ссылка", "control", "f92b7fc7-d460-4881-9f20-fb75d6c8451f", "TBGReferenceNodeComponentEngine", {}, {}),
    ("condition", "Условие", "control", "1170d1a2-472b-4edc-9a87-68ff7805f7b6", "TBGConditionComponentEngine", {}, {}),
    ("loop", "Цикл", "control", "9875bc6a-17a2-465f-b37a-7b300ac52324", "TBGLoopComponent", {}, {}),
    ("autocorr", "Автокорреляция", "research", "b1951e4d-5139-454b-930f-942b1c2e64b3", "TBGAutoCorrelationEngine", {"data": P_DS_IN}, {"data": P_DS_OUT}),
    ("duplicates", "Дубликаты и противоречия", "research", "5a630fc3-7f1d-4e74-94d3-89578576dad5", "TBGDuplicatesEngine", {"data": P_DS_IN}, {"data": P_DS_OUT}),
    ("corr_analysis", "Корреляционный анализ", "research", "1a0ef37e-bdb3-4cf1-908e-79b9b0763a6d", "TBGCorrAnalysisEngine", {"data": P_DS_IN}, {"data": P_DS_OUT}),
    ("factor_analysis", "Факторный анализ", "research", "a026e29f-e2ac-473f-a792-47031a204125", "TBGFactorAnalysisEngine", {"data": P_DS_IN}, {"factors": "a5c95dba-f032-3202-8c1b-fb2c293cb5d8", "loadings": "87d1eb64-e7c7-3310-84d8-9172e0c68551"}),
    ("assoc_rules", "Ассоциативные правила", "datamining", "5596f9c0-30c4-49dc-9b21-21556e2a8c6c", "TBGAssnRulesEngine", {"data": P_DS_IN, "suppl": "024e4642-bc15-39a7-9c2d-f6128a179775"}, {"itemsets": "0cad0601-dd8b-3f06-a1a1-5793d9bda0c4", "rules": "724e53c6-85ad-3e71-941e-35146f815711", "apply": "edb71a8b-7004-3bcb-9306-b7ddfaab5115"}),
    ("cluster", "Кластеризация", "datamining", "29c32fa3-f2a0-41b4-a439-6a9a90f8476d", "TBGClusterizationEngine", {"data": P_DS_IN}, {"clusters": "8b9b1aee-4f1b-3256-9f46-6730111087ce", "centers": "36b1f744-de0b-3602-b083-429bcaa2fc17"}),
    ("clope", "Кластеризация транзакций", "datamining", "d412db74-3b02-4dd2-a462-5bf27ebf1b1d", "TBGClopeEngine", {"data": P_DS_IN, "suppl": "024e4642-bc15-39a7-9c2d-f6128a179775"}, {"clusters": "8b9b1aee-4f1b-3256-9f46-6730111087ce", "parameters": "f7ecdcc7-4e51-34d7-8525-10bd77f9dd5b"}),
    ("lin_regression", "Линейная регрессия", "datamining", "fb5960cc-c381-40c9-bb2f-65e7c72e4b29", "TBGLinRegressionEngine", {"data": P_DS_IN}, {"predicted": "c1450f24-33a7-30a5-b26e-44f2cfa7d2c4", "coefficients": "8983fd58-6c41-38b3-95e8-0322761b7941", "summary": "5dc21ddc-1e50-38a8-8741-167f4cb00cdb"}),
    ("log_regression", "Логистическая регрессия", "datamining", "b932b077-1ddb-4d8a-9f3a-514d72b9c094", "TBGLogRegressionEngine", {"data": P_DS_IN}, {"predicted": "c1450f24-33a7-30a5-b26e-44f2cfa7d2c4", "coefficients": "8983fd58-6c41-38b3-95e8-0322761b7941", "summary": "5dc21ddc-1e50-38a8-8741-167f4cb00cdb"}),
    ("nn_classify", "Нейросеть (классификация)", "datamining", "70402979-7c84-456a-97b8-083a5de7543c", "TBGClassifierNeuralNetEngine", {"data": P_DS_IN}, {"output": "afaa7823-c44b-3e6f-8fb9-d1852069c4f7", "summary": "5dc21ddc-1e50-38a8-8741-167f4cb00cdb"}),
    ("nn_regress", "Нейросеть (регрессия)", "datamining", "fa5d493c-b3d9-4023-b23f-c9f18e96470f", "TBGRegressionNeuralNetEngine", {"data": P_DS_IN}, {"output": "afaa7823-c44b-3e6f-8fb9-d1852069c4f7", "summary": "5dc21ddc-1e50-38a8-8741-167f4cb00cdb"}),
    ("sonn", "Самоорганизующаяся сеть", "datamining", "43091feb-0e50-4c8b-a913-17d59ff1b1aa", "TBGSONNEngine", {"data": P_DS_IN}, {"clusters": "82094fac-057d-3f85-b92a-9b9d4d3611a1", "centers": "36b1f744-de0b-3602-b083-429bcaa2fc17"}),
    ("arimax", "ARIMAX", "datamining", "92150a53-40b0-456c-a445-4f0c52388883", "TBGForecastEngine", {"data": P_DS_IN}, {"predicted": "c1450f24-33a7-30a5-b26e-44f2cfa7d2c4", "coefficients": "8983fd58-6c41-38b3-95e8-0322761b7941", "summary": "5dc21ddc-1e50-38a8-8741-167f4cb00cdb"}),
    ("em_cluster", "EM Кластеризация", "datamining", "c8606a85-1c45-4636-9e92-f1e4d867bc6d", "TBGEMEngine", {"data": P_DS_IN}, {"clusters": "8b9b1aee-4f1b-3256-9f46-6730111087ce", "centers": "36b1f744-de0b-3602-b083-429bcaa2fc17"}),
    ("tree_to_table", "Дерево в таблицу", "datatree", "94fef1d2-c326-437c-a8a4-7100dadc89a0", "TBGTreeToDataEngine", {"tree": "a739e211-c6da-3491-a88d-16770536d7e9"}, {"data": P_DS_OUT}),
    ("tree_to_json", "Дерево в JSON", "datatree", "8093578d-8f23-4795-aaae-2613547069af", "TBGTreeToJSONEngine", {"tree": "a739e211-c6da-3491-a88d-16770536d7e9"}, {"data": P_DS_OUT}),
    ("calc_tree", "Калькулятор (дерево)", "datatree", "4b18b749-fe66-43de-95fb-9334a5a7a7d5", "TBGCalcTree", {"tree": "a739e211-c6da-3491-a88d-16770536d7e9", "variables": P_VARS}, {"tree": "f78f5144-f8a0-30a4-8323-ed7b6402665f"}),
    ("union_tree", "Объединение (дер.): конкатенация", "datatree", "f3990232-6ff5-409f-aa48-0571f9fe9af1", "TBGUnionTreeEngine", {"main": "aaf70706-66b9-3814-9970-c9b68a08082a", "joined": "4e43519e-05d2-3c6a-a1ab-1ca9e7d9f24e"}, {"tree": "f78f5144-f8a0-30a4-8323-ed7b6402665f"}),
    ("join_tree", "Слияние (дерево)", "datatree", "64329eec-dfa9-4a66-8cfe-4be36b6e4f51", "TBGJoinTreeEngine", {"main": "aaf70706-66b9-3814-9970-c9b68a08082a", "joined": "4e43519e-05d2-3c6a-a1ab-1ca9e7d9f24e"}, {"tree": "f78f5144-f8a0-30a4-8323-ed7b6402665f"}),
    ("table_to_tree", "Таблица в дерево", "datatree", "e1a84506-f70e-470e-a662-91fa62e23137", "TBGDataToTreeEngine", {"data": P_DS_IN}, {"tree": "f78f5144-f8a0-30a4-8323-ed7b6402665f"}),
    ("json_to_tree", "JSON в дерево", "datatree", "9a2a45c7-ebe1-4743-a0be-217beceedcc2", "TBGJSONToTreeEngine", {"data": P_DS_IN}, {"tree": "f78f5144-f8a0-30a4-8323-ed7b6402665f"}),
    ("exec_cmd", "Программа", "integration", "1ea6e840-6533-423e-b634-3d53dd9ce35e", "TBGExecCmdEngine", {"variables": P_VARS}, {"variables": P_VARS_OUT}),
    ("rest_client", "REST-запрос", "integration", "bfbd85ed-a8ee-4a28-aac5-83851227814b", "TBGRESTClient", {"rest_connection": "3d4165ea-4add-31e7-b7f2-c30c3eaa3a8d", "control": "455b65c3-0587-3a9c-b47e-9b0d285bff3c", "request": "c6bf2c64-379d-3ca2-87cd-17267892d66a"}, {"data": P_DATASET, "additional": "922db711-38ca-3257-95b2-7114499cdf84"}),
    ("sql_script", "SQL-скрипт", "integration", "98be9218-7c0d-4e39-a3f9-26b6bb9b8818", "TBGSQLScriptEngine", {"connection": P_CONNECTION, "data": P_DS_IN, "control": "455b65c3-0587-3a9c-b47e-9b0d285bff3c"}, {"data": P_DATASET}),
]
for key, title, cat, vendor, engine, inputs, outputs in _G6:
    COMPONENTS[key] = ComponentInfo(key, title, cat, vendor, engine, inputs, outputs)


def list_components() -> list[dict]:
    return [
        {
            "key": c.key,
            "title": c.title,
            "category": c.category,
            "engine": c.engine,
            "inputs": list(c.inputs.keys()),
            "outputs": list(c.outputs.keys()),
            "options": list(c.options),
        }
        for c in COMPONENTS.values()
    ]
