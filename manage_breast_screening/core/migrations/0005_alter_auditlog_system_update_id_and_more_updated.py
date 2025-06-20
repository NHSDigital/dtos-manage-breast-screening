# Generated by Django 5.2.1 on 2025-06-16 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0004_alter_auditlog_snapshot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='system_update_id',
            field=models.CharField(db_index=True, null=True),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['content_type_id', 'object_id', 'created_at'], name='core_auditl_content_e3f5a7_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['system_update_id', 'created_at'], name='core_auditl_system__cabccb_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['actor_id', 'created_at'], name='core_auditl_actor_i_41600a_idx'),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='system_update_id',
            field=models.CharField(null=True),
        ),
    ]
