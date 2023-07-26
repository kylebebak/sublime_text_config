from __future__ import annotations, division

import tempfile

import sublime
import sublime_plugin

schema = """{
  "$schema": "https://json-schema.org/draft-07/schema",
  "type": "object",
  "properties": {},
  "required": []
}
"""

data = """{
  "$schema": "./schema.json"
}
"""


class JsonSchemaTestCommand(sublime_plugin.TextCommand):
    """
    - [LSP-json](https://github.com/sublimelsp/LSP-json) uses this
      [language server](https://github.com/microsoft/vscode-json-languageservice)
    - This language server hasn't implemented support for
      [JSON Schema drafts](https://json-schema.org/specification-links.html) beyond
      [07](http://json-schema.org/draft-07/schema)
    - So, [no bundling yet](https://json-schema.org/understanding-json-schema/structuring.html#bundling)
    - Remember to restart JSON-lsp so data file picks up schema file changes
    """
    view: sublime.View

    def run(self, edit):
        td = tempfile.gettempdir()

        window = self.view.window()
        if not window:
            return

        schema_file = f"{td}/schema.json"
        with open(schema_file, "w+") as f:
            f.write(schema)

        data_file = f"{td}/data.json"
        with open(data_file, "w+") as f:
            f.write(data)

        window.open_file(schema_file)
        window.open_file(data_file)
