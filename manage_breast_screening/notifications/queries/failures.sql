SELECT  appt.nhs_number,
        TO_CHAR(appt.starts_at, 'yyyy-mm-dd') AS appointment_date,
        cl.code AS clinic_code,
        CASE
          WHEN appt.episode_type = 'F' THEN 'Routine first call'
          WHEN appt.episode_type = 'G' THEN 'GP Referral'
          WHEN appt.episode_type = 'H' THEN 'Very high risk'
          WHEN appt.episode_type = 'N' THEN 'Early recall'
          WHEN appt.episode_type = 'R' THEN 'Routine recall'
          WHEN appt.episode_type = 'S' THEN 'Self referral'
        END as episode_type,
        CASE
          WHEN msg_sts.id IS NULL THEN TO_CHAR(msg.sent_at, 'yyyy-mm-dd')
          ELSE TO_CHAR(msg_sts.status_updated_at, 'yyyy-mm-dd')
        END AS failure_date,
        CASE
          WHEN msg_fld.nhs_notify_errors IS NOT NULL THEN msg_fld.nhs_notify_errors->'errors'->0->>'title'
          ELSE msg_sts.description
        END AS failure_reason
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
  msg_fld.nhs_notify_errors->'errors' @> '[{"code":"CM_INVALID_NHS_NUMBER"}]' OR
  msg_fld.nhs_notify_errors->'errors' @> '[{"code":"CM_INVALID_VALUE"}]' OR
  msg_sts.description IS NOT NULL
)
