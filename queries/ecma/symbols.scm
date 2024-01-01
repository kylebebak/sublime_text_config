; Note: there is no "ecma" language, this is for extending only

(arguments (arrow_function (identifier) @definition.var @breadcrumb.1))
(arguments (arrow_function (formal_parameters) @definition.var @breadcrumb.1))

(function_declaration (identifier) @definition.function @breadcrumb.1)
(variable_declarator (identifier) @definition.function @breadcrumb.1 (arrow_function))
(method_definition (property_identifier) @definition.function @breadcrumb.1)
(pair (property_identifier) @definition.function @breadcrumb.1 (arrow_function))

(for_in_statement (identifier) @definition.loop)

(variable_declarator
  [
    ((identifier) @definition.object @breadcrumb.1 (object))
    ((identifier) @definition.var [
      (number) (string) (template_string) (null) (undefined) (new_expression) (call_expression) (array) (member_expression)
    ])
    (object_pattern) @definition.var
    (array_pattern) @definition.var
  ]
)
