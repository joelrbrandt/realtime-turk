from django.db import models

class Assignment(models.Model):
    # pk = models.IntegerField(primary_key=True)
    assignment_id = models.CharField(primary_key=True, max_length=255)
    worker_id = models.CharField(max_length=255, db_index=True)
    hit_id = models.ForeignKey('Hit')
    task_id = models.IntegerField(null=True, blank=True)
    accept_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    return_time = models.DecimalField(decimal_places=3, null=True, max_digits=19, blank=True)
    show_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    go_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    submit_time = models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)

    def __unicode__(self):
        return self.assignment_id


class Hit(models.Model):
    hit_id =                models.CharField(max_length=255, primary_key=True)
    hit_type_id =           models.CharField(max_length=255, blank=True)
    proto =                 models.ForeignKey('ProtoHit')
    creation_time =         models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    title =                 models.TextField(blank=True)
    description =           models.TextField(blank=True)
    keywords =              models.TextField(blank=True)
    url =                   models.CharField(max_length=1023)
    reward =                models.DecimalField(max_digits=6, decimal_places=2)
    assignment_duration =   models.IntegerField()
    lifetime =              models.IntegerField()
    max_assignments =       models.IntegerField()
    auto_approval_delay =   models.IntegerField(null=True, blank=True)
    approval_rating =       models.IntegerField(default=0)
    worker_locale =         models.CharField(max_length=255, blank=True)
    retainertime =          models.IntegerField()

    def __unicode__(self):
        return self.hit_id

class ProtoHit(models.Model):
    hit_type_id = models.CharField(max_length=255, blank=True)
    title = models.TextField(blank=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    url = models.CharField(max_length=1023)
    reward = models.DecimalField(max_digits=6, decimal_places=2)
    assignment_duration = models.IntegerField()
    lifetime = models.IntegerField()
    max_assignments = models.IntegerField()
    auto_approval_delay = models.IntegerField(null=True, blank=True, default=86400)
    approval_rating = models.IntegerField(default=0)
    worker_locale = models.CharField(max_length=255, blank=True)
    retainertime = models.IntegerField()
    done = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.hit_type_id + u'::' + unicode(self.title)

class WorkRequest(models.Model):
    proto = models.ForeignKey('ProtoHit')
    foreign_id = models.IntegerField(default=0)
    done = models.BooleanField(default=False)
    payload = models.TextField(blank=True)
    
    def __unicode__(self):
        status = 'Complete - ' if self.done else 'Incomplete - '
        return unicode(status) + u'foreign work: ' + unicode(self.foreign_id)
    

class Event(models.Model):
    #pk = models.IntegerField(primary_key=True)
    assignment = models.ForeignKey('Assignment')
    detail = models.TextField()
    client_time = models.DecimalField(max_digits=19, decimal_places=3)
    ip = models.CharField(max_length=384)
    event_type = models.CharField(max_length=60)
    server_time = models.DecimalField(max_digits=19, decimal_places=3, db_index=True)
    user_agent = models.CharField(max_length=600)

    def __unicode__(self):
        return unicode(self.assignment) + u': ' + self.event_type


class Notification(models.Model):
    #pk = models.BigIntegerField(primary_key=True)
    server_time = models.DecimalField(max_digits=19, decimal_places=3)
    #hit_type_id = models.CharField(max_length=384)
    hit = models.ForeignKey('Hit')
    assignmentid = models.ForeignKey('Assignment', null=True, blank=True)
    eventtype = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.hit) + u' ' + unicode(self.assignmentid) + u': ' + self.eventtype

class APIKey(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    revoked = models.BooleanField()
    
    def __unicode__(self):
        return unicode('Inactive' if self.revoked else 'Active') + ' :: ' + unicode(self.key)
    
    def active(self):
        return not self.revoked
        
    @staticmethod
    def check(key):
        keys = APIKey.objects.filter(key = key)
        return len(keys) > 0 and keys[0].active()
