; Variables
(expression_statement (assignment left: (identifier) @definition.var))
(expression_statement (assignment left: (pattern_list) @definition.var))
(expression_statement (assignment left: (tuple_pattern) @definition.var))

(for_statement left: (identifier) @definition.var.depth.1)
(for_statement left: (pattern_list) @definition.var.depth.1)
(for_statement left: (tuple_pattern) @definition.var.depth.1)

; Walrus operator
(named_expression (identifier) @definition.var)

; Classes and functions
(class_definition name: (identifier) @definition.type.depth.1)

(function_definition name: (identifier) @definition.function.depth.1)
