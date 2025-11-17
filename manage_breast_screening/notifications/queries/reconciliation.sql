SELECT          appt.nhs_number::text AS "NHS number",
                clin.name || ' (' || clin.code || ')' AS "Clinic name and code",
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
                  WHEN appt.status = 'B' THEN 'Booked'
                  WHEN appt.status = 'C' THEN 'Cancelled'
                END AS "Appointment status",
                CASE
                  WHEN let_fld.id IS NOT NULL  THEN 'Failed'
                  WHEN msg.sent_at IS NOT NULL THEN 'Notified'
                  ELSE 'Pending'
                END AS "Notification status",
                TO_CHAR(appt.created_at, 'yyyy-mm-dd HH24:MI') AS "Appointment created at",
                TO_CHAR(appt.starts_at, 'yyyy-mm-dd HH24:MI') AS "Appointment date and time",
                TO_CHAR(appt.cancelled_at, 'yyyy-mm-dd HH24:MI') AS "Appointment cancelled at",
                TO_CHAR(msg.sent_at, 'yyyy-mm-dd HH24:MI') AS "Notification sent at",
                TO_CHAR(nhs_sts.status_updated_at, 'yyyy-mm-dd HH24:MI') AS "NHSApp message read at",
                TO_CHAR(sms_sts.status_updated_at, 'yyyy-mm-dd HH24:MI') AS "SMS delivered at",
                TO_CHAR(let_sts.status_updated_at, 'yyyy-mm-dd HH24:MI') AS "Letter sent at"
FROM            notifications_appointment appt
JOIN            notifications_clinic clin ON clin.id = appt.clinic_id
LEFT JOIN       notifications_message msg ON msg.appointment_id = appt.id
LEFT OUTER JOIN notifications_channelstatus nhs_sts ON nhs_sts.message_id = msg.id
AND             nhs_sts.channel = 'nhsapp'
AND             nhs_sts.status = 'read'
LEFT OUTER JOIN notifications_channelstatus sms_sts ON sms_sts.message_id = msg.id
AND             sms_sts.channel = 'sms'
AND             sms_sts.status = 'delivered'
LEFT OUTER JOIN notifications_channelstatus let_sts ON let_sts.message_id = msg.id
AND             let_sts.channel = 'letter'
AND             let_sts.status = 'received'
LEFT OUTER JOIN notifications_channelstatus let_fld ON let_fld.message_id = msg.id
AND             let_fld.channel = 'letter'
AND             let_fld.status IN (
                    'cancelled', 'virus_scan_failed', 'validation_failed',
                    'technical_failure', 'permanent_failure'
                  )
WHERE           appt.created_at::date > CURRENT_DATE::date - INTERVAL %s
AND             clin.bso_code = %s
ORDER BY        appt.created_at ASC
