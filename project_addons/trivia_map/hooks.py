def uninstall_hook(cr, registry):
    cr.execute(
        "UPDATE ir_act_window "
        "SET view_mode=replace(view_mode, ',here_map', '')"
        "WHERE view_mode LIKE '%,here_map%';"
    )
    cr.execute(
        "UPDATE ir_act_window "
        "SET view_mode=replace(view_mode, 'here_map,', '')"
        "WHERE view_mode LIKE '%here_map,%';"
    )
    cr.execute("DELETE FROM ir_act_window WHERE view_mode = 'here_map';")