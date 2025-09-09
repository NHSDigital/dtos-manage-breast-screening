# Manage Breast Screening Notifications

## Notifications App

Notifications is a Django application responsible for sending notifications to clients of the wider Manage Breast Screening project.

The application is composed of a set of Django Admin commands which are run on a schedule.
The commands currently process a feed of data from the active NBSS system.
The commands store and then send appointment notifications via NHS Notify.

Storage is handled via Azure blob containers, Azure storage queues and Postgresql.

Appointment notifications are sent 4 weeks prior to the appointment date.
Any appointment data processed within 4 weeks of the appointment date will also be eligible for notification on the next scheduled batch.
