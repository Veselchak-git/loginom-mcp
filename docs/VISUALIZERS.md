# Настройка визуализаторов Loginom (ModelViews)

> **Важно для агентов:** `add_visualizer` создаёт только **virgin**-визуализатор
> (пустые `Series` / `Dimensions` / `ViewColumns`). Для таблицы, диаграммы,
> куба, статистики, качества и «Дубликаты и противоречия» вызывайте
> `configure_visualizer`, затем `save_package` — он пишет и XML, и BIN.
> Проверка готового файла: `audit_visualizers(path)` или `python tools/audit_viz.py`.

## Жизненный цикл

1. Собрать сценарий: `create_package` → `add_node` → `configure_node` → `link_nodes`.
2. Повесить визуализаторы: `list_visualizers` → `add_visualizer` (пока virgin).
3. `configure_visualizer` — колонки, фильтр, сортировка, куб, статистика, серии, качество,
   профили кластеров (`histogram_scaling`, `indicator`, тепловая карта, фильтры),
   статистика (`show_histogram`, `statistics_in_rows`), ROC (стандартный набор графиков)
   и отчёты линейной/логистической регрессии.
4. `save_package` → `.lgp` уже с настроенными видами (повторный save их сохраняет).
5. `audit_visualizers` — пустые виды, чужие имена полей, нет флагов дубликатов.

Чтобы поправить уже сохранённый файл без сессии: `configure_visualizer(view, path=...)`.
Ручная правка ZIP ниже остаётся запасным путём. После неё не вызывайте
`save_package` из сессии, в которой этой настройки нет — сессия запишет virgin.

## Где лежат визуализаторы

Внутри `.lgp` (ZIP):

| Файл | Роль |
|------|------|
| `Unit_0/Unit.xml` | Читаемая разметка `ModelViews/Nodes` + `ModelViews/Links` |
| `Unit_0/Unit.bin` | BGB-двойник; **обязателен** для Loginom |

Связь: `Links` в `ModelViews` ведут от выходного порта узла сценария
(`Data` / `4ba0e2c2-…`) к входу визуализатора
`DataSource` (`9dc72a3f-56bf-3bfc-84ec-f979daf4da6b`).

VendorGuid (ключ → тип):

| key (MCP) | Engine | VendorGuid |
|-----------|--------|------------|
| `table` | `TBGBrowseView` | `e6ed8484-b292-4534-a136-fd82df5cc01c` |
| `chart` | `TBGChartView` | `423d2c8c-4334-43f2-aad5-2f01e8bf0f87` |
| `cube` | `TBGCubeView` | `85236173-223c-4772-833f-7841c84a7ddf` |
| `statistics` | `TBGStatView` | `121165f9-07d1-4507-9ff4-d64f6333b4ca` |
| `quality` | `TBGQualityView` | `85cb32b2-4a6d-4dca-9b7f-9548585095c1` |

## Диаграмма (`chart` / TBGChartView)

### Признаки virgin

```xml
<Links>
  <Item Name="lkXData" LinkKind="lkXData"/>
  <Item Name="lkLabels" LinkKind="lkLabels"/>
</Links>
<Series/>
```

### Настроенный шаблон (столбцы)

```xml
<Engine xsi:type="TBGChartView">
  <Parameters Rationing="false">
    <BackgroundColor/>
    <Links>
      <Item Name="lkXData" LinkKind="lkXData"/>
      <Item Name="lkLabels" FieldType="dtString" LinkKind="lkLabels"
            FieldName="PART_IDPART_NAME"/>
    </Links>
    <Series>
      <Item Guid="{uuid}" DisplayName="Сумма" Series="ctColumns">
        <Color/>
        <Links>
          <Item Name="lkYData" FieldType="dtFloat" LinkKind="lkYData"
                FieldName="SUM_F_SUM"/>
        </Links>
      </Item>
    </Series>
    <Axes>
      <Item Name="apAbscissa"/>
      <Item Name="apLeftOrdinate" Position="apLeftOrdinate"/>
      <Item Name="apRightOrdinate" Position="apRightOrdinate"/>
    </Axes>
  </Parameters>
</Engine>
```

Правила:

- `lkLabels` + `FieldName` — категории (ось X / подписи).
- В `Series` — мера(ы) через `lkYData` + `FieldName`.
- Типичные `Series`: `ctColumns` (столбцы), `ctArea`, `ctScatter`, …
- Имена полей — **Name** из набора данных узла-источника (не DisplayName).

### BGB (Unit.bin) — ключевые ordinals

| Сущность | XML | BIN (тип `0x09`) |
|----------|-----|------------------|
| LinkKind lkXData | `lkXData` | `1` |
| LinkKind lkYData | `lkYData` | `2` |
| LinkKind lkLabels | `lkLabels` | `6` |
| FieldType/DataType dtFloat | `dtFloat` | `3` |
| FieldType/DataType dtInteger | `dtInteger` | `4` |
| FieldType/DataType dtString | `dtString` | `5` |
| Series ctArea | `ctArea` | `1` |
| Series ctColumns | `ctColumns` | `3` |
| Axis Position left/right | `apLeftOrdinate` / `apRightOrdinate` | `1` / `2` |

Virgin chart engine в билдере: `loginom_mcp.visualizers._engine_blob(VISUALIZERS["chart"])`
(длина ~267 байт). После Guid визуализатора в BIN ищите этот блок и **заменяйте**
целиком настроенным `Engine`+`TBGChartView`.

Структура BGB-объекта:
`name` → (`classname` | байт `0x00` для untyped) → `attrCount` → attrs → `childCount` → children.

## Куб (`cube` / TBGCubeView)

### Признаки virgin (в пакетах MCP часто «плоский»)

```text
Engine TBGCubeView
  Dimensions  (пустой список)
  Summaries   (пустой список)
  Charts      (пустой)
```

В XML билдера также встречается вложенный вариант:

```xml
<Dimensions><Dimensions/></Dimensions>
<Summaries><Cases/></Summaries>
<Charts/>
```

### Настроенный шаблон

```xml
<Engine xsi:type="TBGCubeView" FullExpandedRowsLevel="1">
  <Dimensions>
    <Dimensions>
      <Item Name="God_Mesyats" DisplayName="Год-Месяц" DataType="dtString"
            DimensionType="cdtRows" OrderNumber="0">
        <Filter Usable="true"/>
      </Item>
      <Item Name="PART_IDPART_NAME" DisplayName="Отдел.Наименование"
            DataType="dtString" DimensionType="cdtRows" OrderNumber="1">
        <Filter Usable="true"/>
      </Item>
      <Item Name="TV_IDGR_IDGR_NAME" DisplayName="Группа.Наименование"
            DataType="dtString" DimensionType="cdtCols" OrderNumber="0"/>
    </Dimensions>
  </Dimensions>
  <Summaries>
    <Cases>
      <Item Name="CountCase" DisplayName="Количество" CountCase="true"/>
      <Item Name="SUM_F_SUM" DisplayName="Сумма" DataType="dtFloat">
        <Functions OrderNumber="0">
          <SubFunctions Usable="true" OrderNumber="0"/>
        </Functions>
      </Item>
    </Cases>
  </Summaries>
  <CaseSortItems>
    <Item>
      <CompositeHeader CaseName="SUM_F_SUM" CaseDataType="dtFloat"
                       CaseFunction="cfSum"/>
    </Item>
  </CaseSortItems>
  <Charts>
    <Item Guid="{uuid}" PanelWidth="300" Type="ctColumns"
          SeriesPosition="ccspRows" Title="Кросс-диаграмма сумм">
      <CaseInfos>
        <Item Guid="{uuid}" SourceName="SUM_F_SUM" CaseFunction="cfSum"/>
      </CaseInfos>
    </Item>
  </Charts>
</Engine>
```

На сокете `DataSource` куба полезно заполнить `ColumnDefs`
(`UsageType`: `utGroup` для измерений, `utValue` для фактов).

### DimensionType / CaseFunction (BIN)

| XML | BIN enum8 |
|-----|-----------|
| `cdtCols` | `0` |
| `cdtRows` | `1` |
| `cdtFree` | `2` |
| `cfSum` | `0` |
| Charts `Type` ctSpline | `2` |
| Charts `Type` ctColumns | `3` |
| `SeriesPosition` ccspRows | `1` |

## Таблица (`table` / TBGBrowseView)

### Virgin в сохранённых пакетах MCP

Часто **без** `ViewColumns` (4 child: Filtering, Grouping, Sorting, Options).
В билдере virgin — с пустым `<ViewColumns/>`.

### Настройка колонок и сортировки (топ-N без узлов Sort/RowNum)

Для заданий «топ-N товаров» предпочтительно:

- в сценарии: при необходимости **фильтр периода** + **группировка** по товару;
- **не** добавлять узлы «Сортировка», «Калькулятор RowNum», «Фильтр Номер≤N»;
- в визуализаторе таблицы: `ViewColumns` + `Sorting/SortingColumns` по убыванию объёма.

Первые N строк отсортированной таблицы и есть ответ на топ-N.

```xml
<Engine xsi:type="TBGBrowseView">
  <ViewColumns>
    <Item Name="TV_IDTV_NAME" DisplayName="Товар.Наименование" DataType="dtString"/>
    <Item Name="SUM_F_COUNT" DisplayName="Количество" DataType="dtFloat"/>
    <Item Name="SUM_F_SUM" DisplayName="Сумма" DataType="dtFloat"/>
  </ViewColumns>
  <Filtering/>
  <Grouping/>
  <Sorting>
    <SortingColumns>
      <Item Name="SUM_F_COUNT" SortDirection="sdDesc"/>
    </SortingColumns>
  </Sorting>
  <Options/>
</Engine>
```

BGB: `SortDirection` enum8 — `sdAsc=0`, `sdDesc=1`.

Исключение: накопительный % / «50% объёма» — порядок строк нужен **до** `CumulativeSum`
в калькуляторе, поэтому узел «Сортировка» в сценарии остаётся; в таблице всё равно
задайте колонки (и при желании повторную сортировку).

## Практический алгоритм правки `.lgp`

1. Распаковать ZIP (или читать через `zipfile`).
2. В `Unit.xml` найти `Item Guid="…"` визуализатора → заменить `<Engine …>…</Engine>`.
3. В `Unit.bin` найти Guid визуализатора → объект `Engine` → заменить настроенным BGB.
4. Записать оба файла обратно в `.lgp` (остальные entries не трогать).
5. Не открывать пакет через MCP-сессию с повторным `save_package`.

Хелперы билдера:

- `visualizers.build_visualizer_node` / `_engine_blob` / `_chart_parameters_blob` — virgin;
- `visualizers.visualizer_xml` — virgin XML;
- `vendor/bgb_import_node.py`: `s`, `field_guid`, `field_str`, `field_bool`, `field_int32`,
  `list_of_items`, `encode_bgb_len`.

Enum-атрибут 1 байт: `visualizers.field_enum8(name, value)`.

## Чек-лист «визуализаторы настроены»

- [ ] У каждой диаграммы задания есть `FieldName` на `lkLabels` и непустой `<Series>`.
- [ ] У каждого куба — измерения с `DimensionType` и факты в `Summaries/Cases`.
- [ ] У каждой таблицы задания — непустой `<ViewColumns>`; для топ-N — `Sorting` с `sdDesc`.
- [ ] Те же имена присутствуют в `Unit.bin` (UTF-8 строки).
- [ ] Кросс-диаграмма: либо отдельный `chart`, либо `<Charts>` внутри куба.

## MCP: `configure_visualizer`

```text
configure_visualizer(
  view,
  path=None,
  columns=[...],                 # table / duplicates_view / statistics
  labels_field=..., y_fields=[...], series_type="ctColumns",
  sort=[{name, direction}],      # sdAsc / sdDesc
  filters=[                      # table / duplicates_view; пропуск очищает фильтр
    {name: "Duplicate", relation: "is_true", data_type: "dtBoolean"},
    {name: "Summa", relation: "=", value: 0, data_type: "dtFloat"},
    {row_number: true, relation: "<=", value: 20},
    {name: "Qty", relation: "between", lower: 1, upper: 10, data_type: "dtInteger"}
  ],
  include_duplicate_flags=False,
  dimensions=[{name, axis: "rows"|"cols"|"free"}],
  facts=[{name, data_type, functions: ["sum", "count"]}, {name: "CountCase", count_case: true}],
  case_sort={name, data_type, function: "sum"},
  cube_chart={source, title, width: 300, position: "rows"}
)
```

Фильтр визуализатора пишется в `Filtering/FilterColumns` (XML и BIN).
`is_true` / `is_false` без значения сравнения — так Loginom сохраняет
«Дубликат = истина». Число 0..255 хранится как `vrtByte`, большее целое как
`vrtInt64`, дробное как `vrtDouble`, строка как `vrtString`.
`Grouping` и `Options` остаются пустыми. Список `in` / `not_in` в фильтре
визуализатора не кодируется.

- `quality`: аргументы колонок не нужны — выставляются индикаторы и обязательные
  дети Loginom 7 (`ColumnsStats`, `PreviewDetailing`). Выбор полей на сокете
  узла этим вызовом не меняется.
- `duplicates_view`: `include_duplicate_flags=True` добавляет `Duplicate`,
  `DuplicateGroup`, `Contradiction`, `ContradictionGroup`.
- `cube`: измерения с `DimensionType` и факты. У числового факта по умолчанию
  включены функции 0 и 1 (как в сохранённом кубе со «Сумма»). `CountCase` —
  отдельный факт «Количество» без агрегатов по полю. `cube_chart` — кросс-диаграмма.
- `statistics`: `columns` становятся `StatViewColumns`. Для чисел и дат по
  умолчанию `RoundMode=rmoNearestMath` и 3 знака. Панели индикаторов — как у
  настроенного `TBGStatView`.

`audit_visualizers(path)` возвращает `ok` и список `issues`
(`empty_columns`, `empty_series`, `empty_cube`, `empty_statistics`,
`missing_duplicate_flags`, `unknown_column`, `quality_shape`, `quality_virgin`).
