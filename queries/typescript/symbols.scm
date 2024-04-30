; inherits: ecma

(class_declaration (type_identifier) @definition.class @breadcrumb.1)

(type_alias_declaration (type_identifier) @definition.type)
(interface_declaration (type_identifier) @definition.interface)

(call_expression function: (identifier) @definition.call)
(call_expression function: (member_expression property: (property_identifier) @definition.call))

(variable_declarator
  [
    ((identifier) @definition.object @breadcrumb.1 (as_expression (object)))
    ((identifier) @definition.var (as_expression [
      (number) (string) (template_string) (null) (undefined) (new_expression) (call_expression) (array) (member_expression)
    ]))
  ]
)

; Imports
(import_clause (identifier) @definition.import)
(import_clause (namespace_import (identifier) @definition.import))
(import_clause (named_imports (import_specifier (identifier) @definition.import .)))
