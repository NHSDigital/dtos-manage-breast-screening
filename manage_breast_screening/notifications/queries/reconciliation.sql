SELECT    clin.code AS "Clinic code",
          appt.episode_type AS "Episode type",
          appt.status AS "Status",
          COUNT(appt.id) AS "Count"
FROM      notifications_appointment appt
JOIN      notifications_clinic clin ON clin.id = appt.clinic_id
WHERE     appt.created_at::date = %s
AND       clin.bso_code = %s
GROUP BY  clin.code, appt.episode_type, appt.status
