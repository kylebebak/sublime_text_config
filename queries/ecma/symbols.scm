; Note: there is no "ecma" language, this is for extending only

(function_declaration (identifier) @definition.function.bc.1)
(variable_declarator (identifier) @definition.function.bc.1 (arrow_function))
(method_definition (property_identifier) @definition.function.bc.1)
(pair (property_identifier) @definition.function.bc.1 (arrow_function))

(for_in_statement (identifier) @definition.var)

(variable_declarator
  [
    ((identifier) @definition.object.bc.1 (object))
    ((identifier) @definition.var [
      (number) (string) (template_string) (null) (undefined) (new_expression) (call_expression) (array) (member_expression)
    ])
    (object_pattern) @definition.var
    (array_pattern) @definition.var
  ]
)
