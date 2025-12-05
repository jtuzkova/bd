SELECT ex_id, role, pass_id
FROM external_users
WHERE
    login = (%s)
    AND passw = (%s)
;