; inherits: ecma

(class_declaration (type_identifier) @definition.class.depth.1)

(type_alias_declaration (type_identifier) @definition.type)
(interface_declaration (type_identifier) @definition.interface)

(variable_declarator
  [
    ((identifier) @definition.object.depth.1 (as_expression (object)))
    ((identifier) @definition.var (as_expression [
      (number) (string) (template_string) (null) (undefined) (new_expression) (call_expression) (array) (member_expression)
    ]))
  ]
)
