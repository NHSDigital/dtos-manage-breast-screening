SELECT  TO_CHAR(appt.starts_at, 'yyyy-mm-dd') AS appointment_date,
        cl.bso_code AS bso_code,
        cl.code AS clinic_code,
        cl.name AS clinic_name,
        CASE
          WHEN appt.episode_type = 'F' THEN 'Routine first call'
          WHEN appt.episode_type = 'G' THEN 'GP Referral'
          WHEN appt.episode_type = 'H' THEN 'Very high risk'
          WHEN appt.episode_type = 'N' THEN 'Early recall'
          WHEN appt.episode_type = 'R' THEN 'Routine recall'
          WHEN appt.episode_type = 'S' THEN 'Self referral'
        END,
        COUNT(msg_snt.id)     AS notifications_sent,
        COUNT(nhsapp_read.id) AS nhs_app_messages_read,
        COUNT(sms_dlv.id)     AS sms_messages_delivered,
        COUNT(ltr_sent.id)    AS letters_sent,
        COUNT(msg_fld.id)     AS notifications_failed
FROM   notifications_appointment appt
JOIN   notifications_clinic cl ON appt.clinic_id = cl.id
LEFT OUTER JOIN notifications_message msg_snt ON msg_snt.appointment_id = appt.id
AND    msg_snt.status IN ('sending', 'delivered', 'failed')
JOIN   notifications_message msg ON msg.appointment_id = appt.id
LEFT OUTER JOIN notifications_messagestatus msg_fld ON msg_fld.message_id = msg.id
AND    msg_fld.status = 'failed'
LEFT OUTER JOIN notifications_channelstatus nhsapp_read ON nhsapp_read.message_id = msg_snt.id
AND    nhsapp_read.channel = 'nhsapp'
AND    nhsapp_read.status = 'read'
LEFT OUTER JOIN notifications_channelstatus sms_dlv ON sms_dlv.message_id = msg_snt.id
AND    sms_dlv.channel = 'sms'
AND    sms_dlv.status = 'delivered'
LEFT OUTER JOIN notifications_channelstatus ltr_sent ON ltr_sent.message_id = msg_snt.id
AND    ltr_sent.channel = 'letter'
AND    ltr_sent.status = 'received'
WHERE  appt.starts_at > CURRENT_DATE - INTERVAL %s
GROUP BY appointment_date, cl.bso_code, cl.code, cl.name, appt.episode_type
ORDER BY appointment_date DESC
