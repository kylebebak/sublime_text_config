; Variables
(class_definition (block (expression_statement (assignment left: (identifier) @definition.var))))
(function_definition (block (expression_statement (assignment left: (identifier) @definition.var))))
; Walrus operator
(named_expression (identifier) @definition.var)

(class_definition name: (identifier) @definition.class)

(function_definition name: (identifier) @definition.function)
