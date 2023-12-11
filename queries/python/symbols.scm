; Variables
(expression_statement (assignment left: (identifier) @definition.var))
(expression_statement (assignment left: (pattern_list) @definition.var))
(expression_statement (assignment left: (tuple_pattern) @definition.var))
((as_pattern_target) @definition.var)

(call (identifier) @definition.call)

(for_statement left: (identifier) @definition.var.bc.1)
(for_statement left: (pattern_list) @definition.var.bc.1)
(for_statement left: (tuple_pattern) @definition.var.bc.1)

; Walrus operator
(named_expression (identifier) @definition.var)

; Classes and functions
(class_definition name: (identifier) @definition.class.bc.1)

(function_definition name: (identifier) @definition.function.bc.1)

((if_statement) @anonymous.bc)
((with_statement) @anonymous.bc)
