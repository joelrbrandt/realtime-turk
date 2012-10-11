from django.db import models

class Assignments(models.Model):
    # pk = models.IntegerField(primary_key=True)
    assignment_id = models.CharField(primary_key=True, max_length=255)
    worker_id = models.CharField(max_length=255, db_index=True)
    hit_id = models.ForeignKey('Hits')
    task_id = models.IntegerField(null=True, blank=True)
    accept_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    return_time = models.DecimalField(decimal_places=3, null=True, max_digits=19, blank=True)
    show_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    go_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    submit_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)

    def __unicode__(self):
        return self.assignment_id


class Hits(models.Model):
    hit_id = models.CharField(max_length=255, primary_key=True)
    hit_type_id = models.CharField(max_length=255, blank=True)
    creation_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    title = models.TextField(blank=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    reward = models.DecimalField(max_digits=6, decimal_places=2)
    assignment_duration = models.IntegerField()
    lifetime = models.IntegerField()
    max_assignments = models.IntegerField()
    auto_approval_delay = models.IntegerField(null=True, blank=True)
    retainertime = models.IntegerField()

    def __unicode__(self):
        return self.hit_id


class Events(models.Model):
    #pk = models.IntegerField(primary_key=True)
    assignment = models.ForeignKey('Assignments')
    detail = models.TextField()
    client_time = models.DecimalField(max_digits=19, decimal_places=3)
    ip = models.CharField(max_length=384)
    event_type = models.CharField(max_length=60)
    server_time = models.DecimalField(max_digits=19, decimal_places=3, db_index=True)
    user_agent = models.CharField(max_length=600)

    def __unicode__(self):
        return unicode(self.assignment) + u': ' + self.event_type


class Notifications(models.Model):
    #pk = models.BigIntegerField(primary_key=True)
    server_time = models.DecimalField(max_digits=19, decimal_places=3)
    #hit_type_id = models.CharField(max_length=384)
    hit = models.ForeignKey('Hits')
    assignmentid = models.ForeignKey('Assignments', null=True, blank=True)
    eventtype = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.hit) + u' ' + unicode(self.assignmentid) + u': ' + self.eventtype
