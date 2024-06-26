; Variables
(expression_statement (assignment left: (identifier) @definition.var))
(expression_statement (assignment left: (pattern_list (identifier) @definition.var)))
(expression_statement (assignment left: (tuple_pattern) @definition.var))
((as_pattern_target) @definition.var)

(call (identifier) @definition.call)
(call function: (attribute attribute: (identifier) @definition.call))

(for_statement left: (identifier) @definition.loop @breadcrumb.1)
(for_statement left: (pattern_list) @definition.loop @breadcrumb.1)
(for_statement left: (tuple_pattern) @definition.loop @breadcrumb.1)

; Walrus operator
(named_expression (identifier) @definition.var)

; Classes and functions
(class_definition name: (identifier) @definition.class @breadcrumb.1)

(function_definition name: (identifier) @definition.function @breadcrumb.1)

(("if") @definition.if @breadcrumb.1)
(("with") @definition.block @breadcrumb.1)

; Imports
(import_from_statement ("import" (dotted_name) @definition.import))
(import_from_statement (aliased_import (identifier) @definition.import))
(import_statement (dotted_name) @definition.import)
(import_statement (aliased_import (identifier) @definition.import))
