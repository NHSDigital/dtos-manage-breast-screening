SELECT  appt.nhs_number AS "NHS number",
        TO_CHAR(appt.starts_at, 'yyyy-mm-dd') AS "Appointment date",
        cl.code AS "Clinic code",
        CASE
          WHEN appt.episode_type = 'F' THEN 'Routine first call'
          WHEN appt.episode_type = 'G' THEN 'GP Referral'
          WHEN appt.episode_type = 'H' THEN 'Very high risk'
          WHEN appt.episode_type = 'N' THEN 'Early recall'
          WHEN appt.episode_type = 'R' THEN 'Routine recall'
          WHEN appt.episode_type = 'S' THEN 'Self referral'
          WHEN appt.episode_type = 'T' THEN 'VHR short-term recall'
        END AS "Episode type",
        CASE
          WHEN msg_sts.id IS NULL THEN TO_CHAR(msg.sent_at, 'yyyy-mm-dd')
          WHEN msg_sts.id IS NOT NULL THEN TO_CHAR(msg_sts.status_updated_at, 'yyyy-mm-dd')
          ELSE TO_CHAR(appt.created_at, 'yyyy-mm-dd')
        END AS "Failed date",
        CASE
          WHEN CAST(appt.number AS INTEGER) > 1 THEN 'invitation not sent as not a 1st time appointment'
          WHEN appt.episode_type IN ('H', 'T', 'N') THEN 'invitation not sent as episode type is not supported'
          WHEN msg_fld.nhs_notify_errors IS NOT NULL THEN (
            array_to_string(
              ARRAY(
                SELECT errs ->> 'title'
                FROM jsonb_array_elements(msg_fld.nhs_notify_errors) AS errs
              ), ', '
            )
          )
          WHEN msg_sts.description IS NOT NULL THEN msg_sts.description
        END AS "Reason"
FROM    notifications_appointment appt
JOIN    notifications_clinic cl ON appt.clinic_id = cl.id
JOIN    notifications_message msg ON msg.appointment_id = appt.id
AND     msg.status IN ('sending', 'delivered', 'failed')
LEFT OUTER JOIN notifications_message msg_fld ON msg_fld.appointment_id = appt.id
AND     msg_fld.status = 'failed'
LEFT OUTER JOIN notifications_messagestatus msg_sts ON msg_sts.message_id = msg.id
AND     msg_sts.status = 'failed'
WHERE   appt.starts_at::date = %s
AND   (
  msg_fld.nhs_notify_errors @> ANY(ARRAY[
    '[{"code":"CM_INVALID_NHS_NUMBER"}]',
    '[{"code":"CM_INVALID_VALUE"}]',
    '[{"code":"CM_MISSING_VALUE"}]',
    '[{"code":"CM_NULL_VALUE"}]'
  ]::jsonb[]) OR
  msg_sts.description IS NOT NULL OR
  CAST(appt.number AS INTEGER) > 1 OR
  appt.episode_type IN ('H', 'N', 'T')
)
