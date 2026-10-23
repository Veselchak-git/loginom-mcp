"""Minimal virgin Unit.xml fragments for supported Loginom nodes."""
from __future__ import annotations

import uuid
from xml.sax.saxutils import escape

from .paths import VENDOR
from .components import (
    P_DATASET,
    P_DS_ELSE,
    P_DS_IN,
    P_DS_OUT,
    P_JOINED,
    P_JOINED_VARS,
    P_COLUNION_JOINED,
    P_MAIN,
    P_VARS,
    P_VARS_OUT,
    P_SUPPORT,
    P_UNGROUP_OUT,
    P_UNGROUP_STATS,
    P_RANGES_IN,
    P_RANGES_OUT,
    P_OUT_DATA,
    P_OUT_OUTLIERS,
    P_OUT_EXTR,
    P_PART_COMMON,
    P_PART_TEACH,
    P_PART_TEST,
    P_XSD,
    P_CLASS_PARAMS,
    P_BINNING_PARAMS,
    P_CONNECTION,
    P_RESULT_STATUS,
    COMPONENTS,
)


def _svc_ports() -> str:
    return """\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="00bd0b43-e4b5-3ac1-b95a-ac1bee14f858" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="ca080ff0-2342-32b0-b480-586f9747bace" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="e98be5ba-c627-3a55-af82-a399dd13c73b" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="58922a98-d1ea-36de-9099-3ce26fe160e2" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>"""


def _svc_ports_sync_only() -> str:
    return """\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="00bd0b43-e4b5-3ac1-b95a-ac1bee14f858" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="ca080ff0-2342-32b0-b480-586f9747bace" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="e98be5ba-c627-3a55-af82-a399dd13c73b" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="58922a98-d1ea-36de-9099-3ce26fe160e2" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>"""


def _ctrl_socket() -> str:
    return """\t\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>"""


def _ds_tune(guid: str, name: str, display: str, *, virgin: bool = False) -> str:
    v = ' Virgin="true"' if virgin else ""
    return f"""\t\t\t\t\t\t<Item Guid="{guid}" Name="{name}" DisplayName="{escape(display)}">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneDataSourceSocket"{v}>
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>"""


def _ds_out(guid: str, name: str, display: str) -> str:
    return f"""\t\t\t\t\t\t<Item Guid="{guid}" Name="{name}" DisplayName="{escape(display)}">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedDataSourceOutputSocket">
\t\t\t\t\t\t\t\t<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>"""


def node_xml(
    component: str,
    node_guid: uuid.UUID,
    display_name: str,
    left: float,
    top: float,
    *,
    file_name: str = "data.csv",
) -> str:
    info = COMPONENTS[component]
    dn = escape(display_name)
    vg = info.vendor
    fn = escape(file_name)

    if component in (
        "import_native",
        "import_text",
        "import_excel",
        "import_xml",
    ):
        engine = {
            "import_native": f'<Engine xsi:type="TBGImportNative" FileName="{fn}"/>',
            "import_text": (
                f'<Engine xsi:type="TBGImportTextFile" FileName="{fn}" '
                'CodePage="65001" DecimalSeparator="." DateFormat="dd.MM.yyyy" '
                'DateSeparator="." ColumnsRequired="false">'
                "<ColumnDefs/></Engine>"
            ),
            "import_excel": f'<Engine xsi:type="TBGImportExcelFileEngine" FileName="{fn}"/>',
            "import_xml": f'<Engine xsi:type="TBGImportXML" FileName="{fn}" CompositeDisplayNameSeparator="|"/>',
        }[component]
        if component == "import_xml":
            return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение"/>
\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные"/>
\t\t\t\t\t<Item Guid="{P_XSD}" Name="XSDConnection" DisplayName="Подключение к источнику XSD-схемы"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных"/>
\t\t\t\t</OutputPorts>
\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="00bd0b43-e4b5-3ac1-b95a-ac1bee14f858" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="ca080ff0-2342-32b0-b480-586f9747bace" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="e98be5ba-c627-3a55-af82-a399dd13c73b" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="58922a98-d1ea-36de-9099-3ce26fe160e2" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>
{_ctrl_socket()}
\t\t\t\t\t\t<Item Guid="{P_XSD}" Name="XSDConnection" DisplayName="Подключение к источнику XSD-схемы">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDataSetOutputSocket">
\t\t\t\t\t\t\t\t<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{engine}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение"/>
\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных"/>
\t\t\t\t</OutputPorts>
\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="00bd0b43-e4b5-3ac1-b95a-ac1bee14f858" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="ca080ff0-2342-32b0-b480-586f9747bace" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="e98be5ba-c627-3a55-af82-a399dd13c73b" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="58922a98-d1ea-36de-9099-3ce26fe160e2" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDataSetOutputSocket">
\t\t\t\t\t\t\t\t<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{engine}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component in ("import_db", "import_1c", "import_warehouse"):
        engines_conn = {
            "import_db": (
                '<Engine xsi:type="TBGDBImport" CommandType="dcmTable" CommandText="">'
                "<Filter/></Engine>"
            ),
            "import_1c": '<Engine xsi:type="TBG1Cv8QueryImport" QueryText=""/>',
            "import_warehouse": (
                '<Engine xsi:type="TBGDWExtract" DWObjectType="wotNone" '
                'DWObjectName="" DWObjectDisplayName="">'
                "<SelectionTree><SelObjs/></SelectionTree></Engine>"
            ),
        }
        status_ports = ""
        status_socks = ""
        if component == "import_db":
            status_ports = f"""
\t\t\t\t\t<Item Guid="{P_RESULT_STATUS}" Name="ResultStatus" DisplayName="Статус выполнения"/>"""
            status_socks = f"""
\t\t\t\t\t\t<Item Guid="{P_RESULT_STATUS}" Name="ResultStatus" DisplayName="Статус выполнения">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedVariablesOutputSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>"""
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение"/>
\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных"/>{status_ports}
\t\t\t\t</OutputPorts>
{_svc_ports_sync_only()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="Подключение">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_DATASET}" Name="DataSet" DisplayName="Набор данных">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDataSetOutputSocket" Virgin="true">
\t\t\t\t\t\t\t\t<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>{status_socks}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{engines_conn[component]}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component.startswith("import_"):
        raise KeyError(component)

    if component in ("union", "join", "enrich"):
        engines = {
            "union": '<Engine xsi:type="TBGUnionDataEngine" DisplayNamePrefix="Объединение"><Links/></Engine>',
            "join": '<Engine xsi:type="TBGJoinDataEngine" DisplayNamePrefix="Соединение"><Links/></Engine>',
            "enrich": '<Engine xsi:type="TBGEnrichDataEngine" DisplayNamePrefix="Дополнение"><Links/></Engine>',
        }
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_MAIN}" Name="MainDataSource" DisplayName="Главная таблица"/>
\t\t\t\t\t<Item Guid="{P_JOINED}" Name="JoinedDataSource" DisplayName="Присоединяемая таблица"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_MAIN, "MainDataSource", "Главная таблица")}
{_ds_tune(P_JOINED, "JoinedDataSource", "Присоединяемая таблица")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{engines[component]}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "filter":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Соответствуют условию"/>
\t\t\t\t\t<Item Guid="{P_DS_ELSE}" Name="DataSourceElse" DisplayName="Не соответствуют условию"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Соответствуют условию")}
{_ds_out(P_DS_ELSE, "DataSourceElse", "Не соответствуют условию")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGFilterDataEngine">
\t\t\t\t\t\t<Filter UseGlobalCaseSensitive="false"/>
\t\t\t\t\t</Engine>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "calculator":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGCalcData"><Expressions/></Engine>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    engines = {
        "sorting": '<Engine xsi:type="TBGSortingEngine"><SortingColumns/></Engine>',
        "reform_columns": '<Engine xsi:type="TBGReformColumnsEngine"/>',
        "datetime": '<Engine xsi:type="TBGDateReformEngine"/>',
        "grouping": '<Engine xsi:type="TBGGroupDataEngine" DimValuesCached="true"/>',
        "replace": '<Engine xsi:type="TBGCustomModelComponentEngine"/>',
        "collapse_columns": '<Engine xsi:type="TBGColumnFlippingEngine"/>',
        "crosstab": '<Engine xsi:type="TBGCrossTabEngine" Trained="false" SlugNames="false"><CountCase/></Engine>',
        "sampling": (
            '<Engine xsi:type="TBGSamplingEngine">'
            '<Random RandSeed="149705745" AlwaysRandomize="true"/>'
            '<Sampling SamplingType="stAbsolute" SamplingRecordCount="500" '
            'GroupSize="50" RowCount="1012"/>'
            "</Engine>"
        ),
        "imputation": '<Engine xsi:type="TBGDataRecoveryEngine" MaxNullsPercent="50"/>',
        "smoothing": '<Engine xsi:type="TBGCustomModelComponentEngine"/>',
        "sliding_window": '<Engine xsi:type="TBGSlidingWindowEngine"/>',
    }
    if component in engines:
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{engines[component]}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "colunion":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_MAIN}" Name="MainDataSource" DisplayName="Главная таблица"/>
\t\t\t\t\t<Item Guid="{P_COLUNION_JOINED}" Name="JoinedDataSource" DisplayName="Присоединяемая таблица 1"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_MAIN, "MainDataSource", "Главная таблица")}
{_ds_tune(P_COLUNION_JOINED, "JoinedDataSource", "Присоединяемая таблица 1")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGColUnionDataEngine" TailsAlignType="atExtendToLongest"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component in ("export_text", "export_excel", "export_xml", "export_native", "export_db", "export_warehouse"):
        if component == "export_text":
            eng = f'<Engine xsi:type="TBGExportTextFile" FileName="{fn}" CodePage="65001" LineEnding="leCRLF" CaptionType="ctUseColumnNames" DecimalSeparator="." DelimiterChar=","/>'
        elif component == "export_excel":
            eng = f'<Engine xsi:type="TBGExportExcelFile" FileName="{fn}" SheetName="Лист1"/>'
        elif component == "export_xml":
            eng = (
                f'<Engine xsi:type="TBGExportXML" FileName="{fn}">'
                "<RequestProcessor/><InputColumnsMapping/></Engine>"
            )
        elif component == "export_native":
            eng = f'<Engine xsi:type="TBGExportNative" FileName="{fn}" Compression="dcLZ4"/>'
        elif component == "export_db":
            eng = (
                '<Engine xsi:type="TBGDBExport" TableName="" ExportType="etAppend">'
                "<ExportColumns/></Engine>"
            )
        else:
            eng = (
                '<Engine xsi:type="TBGDWLoad" DWObjectType="wotNone" '
                'DWObjectName="" DWObjectDisplayName="">'
                '<SelectionTree CreateProcessTable="false" RebuildCube="false">'
                "<SelObjs/></SelectionTree></Engine>"
            )
        conn_dn = (
            "Подключение к файловому хранилищу"
            if component == "export_xml"
            else "Подключение"
        )
        xsd_port = ""
        xsd_sock = ""
        if component == "export_xml":
            xsd_port = f"""
\t\t\t\t\t<Item Guid="{P_XSD}" Name="XSDConnection" DisplayName="Подключение к источнику XSD-схемы"/>"""
            xsd_sock = f"""
\t\t\t\t\t\t<Item Guid="{P_XSD}" Name="XSDConnection" DisplayName="Подключение к источнику XSD-схемы">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>"""
        ctrl_port = ""
        ctrl_sock = ""
        if component != "export_warehouse":
            ctrl_port = """
\t\t\t\t\t<Item Guid="455b65c3-0587-3a9c-b47e-9b0d285bff3c" Name="ControlVariables" DisplayName="Управляющие переменные"/>"""
            ctrl_sock = f"\n{_ctrl_socket()}"
        out_ports = "<OutputPorts/>"
        out_socks = "<OutputSockets/>"
        if component == "export_db":
            out_ports = f"""<OutputPorts>
\t\t\t\t\t<Item Guid="{P_RESULT_STATUS}" Name="ResultStatus" DisplayName="Статус выполнения"/>
\t\t\t\t</OutputPorts>"""
            out_socks = f"""<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_RESULT_STATUS}" Name="ResultStatus" DisplayName="Статус выполнения">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedVariablesOutputSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>"""
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="{conn_dn}"/>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Источник данных"/>{ctrl_port}{xsd_port}
\t\t\t\t</InputPorts>
\t\t\t\t{out_ports}
\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="00bd0b43-e4b5-3ac1-b95a-ac1bee14f858" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="ca080ff0-2342-32b0-b480-586f9747bace" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="e98be5ba-c627-3a55-af82-a399dd13c73b" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="58922a98-d1ea-36de-9099-3ce26fe160e2" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_CONNECTION}" Name="Connection" DisplayName="{conn_dn}">
\t\t\t\t\t\t\t<Socket xsi:type="TBGConnectionInputSocket" Virgin="true"><Constraints/></Socket>
\t\t\t\t\t\t</Item>
{_ds_tune(P_DS_IN, "DataSource", "Источник данных", virgin=True)}{ctrl_sock}{xsd_sock}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t{out_socks}
\t\t\t\t\t{eng}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component in ("calc_variables", "replace_variables"):
        eng = (
            '<Engine xsi:type="TBGCalcVariables"><Expressions/></Engine>'
            if component == "calc_variables"
            else '<Engine xsi:type="TBGCustomModelComponentEngine"/>'
        )
        vars_in_virgin = ' Virgin="true"' if component == "calc_variables" else ""
        vars_out_virgin = "" if component == "calc_variables" else ' Virgin="true"'
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket"{vars_in_virgin}>
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedVariablesOutputSocket"{vars_out_virgin}>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t{eng}
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "vars_to_table":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t</OutputPorts>
{_svc_ports_sync_only()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket">
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedDataSourceOutputSocket">
\t\t\t\t\t\t\t\t<DataSource><ColumnDefs/></DataSource>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGVariablesToDataEngine"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "table_to_vars":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные"/>
\t\t\t\t</OutputPorts>
{_svc_ports_sync_only()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedVariablesOutputSocket">
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGCustomModelComponentEngine"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "join_variables":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные"/>
\t\t\t\t\t<Item Guid="{P_JOINED_VARS}" Name="JoinedVariables" DisplayName="Присоединяемые переменные"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные"/>
\t\t\t\t</OutputPorts>
{_svc_ports_sync_only()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS}" Name="Variables" DisplayName="Входные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t\t<Item Guid="{P_JOINED_VARS}" Name="JoinedVariables" DisplayName="Присоединяемые переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGTuneVariablesSocket" Virgin="true">
\t\t\t\t\t\t\t\t<Constraints/>
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
\t\t\t\t\t\t<Item Guid="{P_VARS_OUT}" Name="Variables" DisplayName="Выходные переменные">
\t\t\t\t\t\t\t<Socket xsi:type="TBGDerivedVariablesOutputSocket">
\t\t\t\t\t\t\t\t<Variables SyncThroughVariables="true"><Elements/></Variables>
\t\t\t\t\t\t\t</Socket>
\t\t\t\t\t\t</Item>
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGCustomModelComponentEngine"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "ungroup":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Разгруппируемые данные"/>
\t\t\t\t\t<Item Guid="{P_SUPPORT}" Name="SupportInputDataSource" DisplayName="Данные для расчета долей"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_UNGROUP_OUT}" Name="UngroupOutput" DisplayName="Выход разгруппировки"/>
\t\t\t\t\t<Item Guid="{P_UNGROUP_STATS}" Name="UngroupStatsDataSource" DisplayName="Показатели качества модели и сезонные индексы"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Разгруппируемые данные")}
{_ds_tune(P_SUPPORT, "SupportInputDataSource", "Данные для расчета долей")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_UNGROUP_OUT, "UngroupOutput", "Выход разгруппировки")}
{_ds_out(P_UNGROUP_STATS, "UngroupStatsDataSource", "Показатели качества модели и сезонные индексы")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGUngroupDataEngine" UngroupMethod="umQuotaIsGiven" RoundFormat="rfDecimalPlaces" MaxDepthPeriodFraction="0"><Links/></Engine>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "quantize":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t\t<Item Guid="{P_RANGES_IN}" Name="Ranges" DisplayName="Внешние диапазоны квантования"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t\t<Item Guid="{P_RANGES_OUT}" Name="Ranges" DisplayName="Диапазоны для квантования"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ds_tune(P_RANGES_IN, "Ranges", "Внешние диапазоны квантования")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
{_ds_out(P_RANGES_OUT, "Ranges", "Диапазоны для квантования")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGBinningEngine"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "outliers":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_OUT_DATA}" Name="OutData" DisplayName="Выходной набор"/>
\t\t\t\t\t<Item Guid="{P_OUT_OUTLIERS}" Name="OutDataOut" DisplayName="Выбросы"/>
\t\t\t\t\t<Item Guid="{P_OUT_EXTR}" Name="OutDataExtr" DisplayName="Экстремальные значения"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_OUT_DATA, "OutData", "Выходной набор")}
{_ds_out(P_OUT_OUTLIERS, "OutDataOut", "Выбросы")}
{_ds_out(P_OUT_EXTR, "OutDataExtr", "Экстремальные значения")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGElimOutlierEngine"/>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "partition":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_PART_COMMON}" Name="OutDataSetCommon" DisplayName="Общий выходной набор"/>
\t\t\t\t\t<Item Guid="{P_PART_TEACH}" Name="OutDataSetTeach" DisplayName="Обучающий выходной набор"/>
\t\t\t\t\t<Item Guid="{P_PART_TEST}" Name="OutDataSetTest" DisplayName="Тестовый выходной набор"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_PART_COMMON, "OutDataSetCommon", "Общий выходной набор")}
{_ds_out(P_PART_TEACH, "OutDataSetTeach", "Обучающий выходной набор")}
{_ds_out(P_PART_TEST, "OutDataSetTest", "Тестовый выходной набор")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGPartitionEngine">
\t\t\t\t\t\t<Random RandSeed="880280492"/>
\t\t\t\t\t\t<Partition TestPriority="false" PartitionMethod="smStratified" RowCount="13668">
\t\t\t\t\t\t\t<SamplingType/>
\t\t\t\t\t\t\t<SamplingRecordCount/>
\t\t\t\t\t\t</Partition>
\t\t\t\t\t</Engine>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    if component == "final_classes":
        return f"""\t\t\t<Item Guid="{node_guid}" DisplayName="{dn}" VendorGuid="{vg}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{P_DS_IN}" Name="DataSource" DisplayName="Входной источник данных"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts>
\t\t\t\t\t<Item Guid="{P_DS_OUT}" Name="DataSource" DisplayName="Выходной набор данных"/>
\t\t\t\t\t<Item Guid="{P_CLASS_PARAMS}" Name="ClassParams" DisplayName="Параметры классов"/>
\t\t\t\t\t<Item Guid="{P_BINNING_PARAMS}" Name="BinningParams" DisplayName="Значимости столбцов"/>
\t\t\t\t</OutputPorts>
{_svc_ports()}
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
{_ds_tune(P_DS_IN, "DataSource", "Входной источник данных")}
{_ctrl_socket()}
\t\t\t\t\t</InputSockets>
\t\t\t\t\t<OutputSockets>
{_ds_out(P_DS_OUT, "DataSource", "Выходной набор данных")}
{_ds_out(P_CLASS_PARAMS, "ClassParams", "Параметры классов")}
{_ds_out(P_BINNING_PARAMS, "BinningParams", "Значимости столбцов")}
\t\t\t\t\t</OutputSockets>
\t\t\t\t\t<Engine xsi:type="TBGCoarseClassesEngine"><Mappers/><Builders/></Engine>
\t\t\t\t</Component>
\t\t\t\t<Position Left="{left:g}" Top="{top:g}"/>
\t\t\t</Item>"""

    # G6: patch virgin XML templates from vendored g6_blobs
    g6_xml = VENDOR / "g6_blobs" / f"{component}.xml"
    if g6_xml.exists():
        import re

        raw = g6_xml.read_text(encoding="utf-8")
        # Item may be written without leading tabs; normalize as a single Item fragment
        raw = re.sub(
            r'Guid="[0-9a-fA-F-]{36}"',
            f'Guid="{node_guid}"',
            raw,
            count=1,
        )
        raw = re.sub(
            r'DisplayName="[^"]*"',
            f'DisplayName="{dn}"',
            raw,
            count=1,
        )
        raw = re.sub(
            r'<Position Left="[^"]*" Top="[^"]*"/>',
            f'<Position Left="{left:g}" Top="{top:g}"/>',
            raw,
            count=1,
        )
        # indent as package Unit node item
        lines = raw.strip().splitlines()
        if lines and not lines[0].startswith("\t"):
            lines = ["\t\t\t" + lines[0]] + [
                ("\t\t\t" + ln if ln.strip() else ln) for ln in lines[1:]
            ]
        return "\n".join(lines)

    raise KeyError(component)


def unit_xml(
    nodes_xml: list[str],
    links: list[dict],
    *,
    model_views_xml: str | None = None,
) -> str:
    nodes_body = "\n".join(nodes_xml) if nodes_xml else ""
    if links:
        link_items = []
        for lk in links:
            link_items.append(
                f"""\t\t\t<Item Guid="{lk['guid']}">
\t\t\t\t<SourcePort NodeGuid="{lk['source_node']}" PortGuid="{lk['source_port']}"/>
\t\t\t\t<TargetPort NodeGuid="{lk['target_node']}" PortGuid="{lk['target_port']}"/>
\t\t\t</Item>"""
            )
        links_body = "\n".join(link_items)
        links_xml = f"\t\t<Links>\n{links_body}\n\t\t</Links>"
    else:
        links_xml = "\t\t<Links/>"
    mv = model_views_xml or "\t<ModelViews><Nodes/><Links/></ModelViews>\n"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Unit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
\t<WorkFlow xsi:type="TBGPackageModelWorkFlow">
\t\t<Nodes>
{nodes_body}
\t\t</Nodes>
{links_xml}
\t\t<ServiceNodes/>
\t\t<ServiceLinks/>
\t\t<Annotations/>
\t</WorkFlow>
{mv}</Unit>
"""
