# Loginom Builder MCP

Портативный **stdio MCP-сервер** на Python: создание и настройка пакетов Loginom `.lgp` — узлы, связи, фильтры, слияние, калькулятор, параметры импорта, визуализаторы.

Работает как **самодостаточная папка**. Подключается к любому MCP-хосту со stdio (Cursor, Claude Desktop, VS Code Copilot MCP, Continue и др.). Для сборки и просмотра `.lgp` нужен только Python — **не** обязательны Windows и установленный Loginom.

## Contributing / AI agents

Недостающие инструменты (см. [ROADMAP.md](ROADMAP.md)) можно реализовать и прислать **Pull Request** — мейнтейнер ревьюит и мержит.

- Люди: [CONTRIBUTING.md](CONTRIBUTING.md)
- ИИ-агенты (обязательно): [AGENTS.md](AGENTS.md)
- MCP resources: `loginom://docs/agents`, `loginom://docs/contributing`, `loginom://docs/roadmap`, `loginom://docs/visualizers`

## Public vs private

| В этом репозитории (public) | Не коммитить / держать локально |
|-----------------------------|----------------------------------|
| Код MCP, `vendor/`, `g6_blobs`, docs | `.staging/`, `out/`, учебные `.lgp` |
| `*.example` конфиги | Личный `mcp.json` с абсолютными путями |
| MIT license | Датасеты курса, домашние работы |

## Требования

- Python 3.10+ в `PATH` (`python3 --version` или `python --version`)

Опционально (только Windows):

- Loginom Community и переменная `LOGINOM_EXE` для UI-проверки в `verify_package` (проверка структуры ZIP/XML/BGB работает и без этого)

## Установка

1. Скопируйте всю папку `loginom_mcp` в любое место.
2. Установите зависимости:

```bash
cd /path/to/loginom_mcp
python3 -m pip install -r requirements.txt
# В Windows часто: python -m pip install -r requirements.txt
```

3. Зарегистрируйте сервер в конфиге MCP-клиента. Подставьте **свои** абсолютные пути к `server.py` и каталогу вывода.

#### Cursor

**Windows** — файл `%USERPROFILE%\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "loginom_builder": {
      "command": "python",
      "args": ["C:\\Users\\YOU\\tools\\loginom_mcp\\server.py"],
      "env": {
        "LOGINOM_MCP_OUT": "C:\\Users\\YOU\\lgp_out"
      }
    }
  }
}
```

**macOS / Linux** — файл `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "loginom_builder": {
      "command": "python3",
      "args": ["/Users/YOU/tools/loginom_mcp/server.py"],
      "env": {
        "LOGINOM_MCP_OUT": "/Users/YOU/lgp_out"
      }
    }
  }
}
```

На Linux путь к папке может быть, например, `/home/YOU/tools/loginom_mcp/server.py`. Перезапустите MCP в Cursor (или Cursor целиком) и проверьте `list_loginom_components`.

#### Claude Desktop

Удобно открыть конфиг: **Settings → Developer → Edit Config**.

**Windows** — `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "loginom_builder": {
      "command": "python",
      "args": ["C:\\Users\\YOU\\tools\\loginom_mcp\\server.py"],
      "env": {
        "LOGINOM_MCP_OUT": "C:\\Users\\YOU\\lgp_out"
      }
    }
  }
}
```

**macOS** — `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "loginom_builder": {
      "command": "python3",
      "args": ["/Users/YOU/tools/loginom_mcp/server.py"],
      "env": {
        "LOGINOM_MCP_OUT": "/Users/YOU/lgp_out"
      }
    }
  }
}
```

**Linux** — `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "loginom_builder": {
      "command": "python3",
      "args": ["/home/YOU/tools/loginom_mcp/server.py"],
      "env": {
        "LOGINOM_MCP_OUT": "/home/YOU/lgp_out"
      }
    }
  }
}
```

Полностью закройте Claude Desktop и откройте снова (на macOS — Cmd+Q, не только закрытие окна). Проверьте, что появились инструменты MCP.

#### OpenCode

Ключ — `mcp` (не `mcpServers`). У локального сервера: `"type": "local"`, `command` — **один массив**, переменные — в `environment`.

Конфиг: проектный `opencode.json` / `opencode.jsonc` **или** глобальный:

| ОС | Глобальный конфиг (типично) |
|----|-----------------------------|
| Windows | `%USERPROFILE%\.config\opencode\opencode.json` |
| macOS / Linux | `~/.config/opencode/opencode.json` |

**Windows:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "loginom_builder": {
      "type": "local",
      "command": ["python", "C:\\Users\\YOU\\tools\\loginom_mcp\\server.py"],
      "enabled": true,
      "environment": {
        "LOGINOM_MCP_OUT": "C:\\Users\\YOU\\lgp_out"
      }
    }
  }
}
```

**macOS:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "loginom_builder": {
      "type": "local",
      "command": ["python3", "/Users/YOU/tools/loginom_mcp/server.py"],
      "enabled": true,
      "environment": {
        "LOGINOM_MCP_OUT": "/Users/YOU/lgp_out"
      }
    }
  }
}
```

**Linux:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "loginom_builder": {
      "type": "local",
      "command": ["python3", "/home/YOU/tools/loginom_mcp/server.py"],
      "enabled": true,
      "environment": {
        "LOGINOM_MCP_OUT": "/home/YOU/lgp_out"
      }
    }
  }
}
```

Проверка: `opencode mcp list` (или перезапуск OpenCode). При необходимости: `opencode mcp debug`.

4. Убедитесь, что доступен инструмент `list_loginom_components`.

Примеры файлов: `mcp.json.example` (Cursor / Claude Desktop), `opencode.json.example` (OpenCode).
### Переменные окружения

| Переменная | Назначение |
|----------|------------|
| `LOGINOM_MCP_OUT` | Каталог по умолчанию для `create_package`, если не задан `output_dir` (по умолчанию: `loginom_mcp/out`) |
| `LOGINOM_EXE` | Необязательный путь к бинарнику Loginom для UI-проверки в Windows |

## Что внутри

- Инструменты MCP: `create_package`, `add_node`, `configure_node`, `link_nodes`, `add_visualizer`, `save_package`, `inspect_lgp`, `verify_package`, …
- `vendor/` — сборщики BGB/XML + `viz_configure.py` (настроенные visualizers после save)
- `tools/inspect_viz.py` — CLI: virgin vs configured views
- `VISUALIZERS.md` — **настройка** диаграмм / кубов / таблиц после `add_visualizer` (XML + BIN). MCP resource `loginom://docs/visualizers`
- `AGENTS.md` / `CONTRIBUTING.md` / `ROADMAP.md` — вклад и пробелы API

## Визуализаторы

`add_visualizer` вешает на узел только **virgin**-представление (пустые серии/измерения/колонки).  
Инструмента `configure_visualizer` пока нет.

Для готового учебного пакета после `save_package` нужно настроить визуализаторы в `.lgp`:

1. Править `Unit_0/Unit.xml` и синхронно `Unit_0/Unit.bin` (Loginom читает BIN).
2. Диаграмма: `lkLabels` + `FieldName`, непустой `<Series>` (`ctColumns` и т.п.).
3. Куб: `Dimensions` (`cdtRows` / `cdtCols` / `cdtFree`) + факты в `Summaries/Cases`.
4. Таблица: непустой `<ViewColumns>` с нужными полями.
5. Не вызывать повторный `save_package` из той же MCP-сессии — перезапишет virgin.

Полные шаблоны, ordinals BGB и чек-лист: **[VISUALIZERS.md](VISUALIZERS.md)**.

## Замечания

- Раздавайте папку целиком (включая `vendor/g6_blobs` и `VISUALIZERS.md`). Не удаляйте `vendor/`.
- `.staging/` и `out/` — локальные кэши; их можно спокойно удалять.
- `verify_package(open_ui=true)` запускает Loginom только в Windows, если задан или найден `LOGINOM_EXE`; иначе проверяется только структура ZIP/XML/BGB.
- Разделитель полей текстового импорта **не** сохраняется в `.lgp` Loginom; в `import_settings` задают кодировку, разделители даты/чисел, лист Excel и типы столбцов.
