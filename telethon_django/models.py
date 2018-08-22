from django.db import models


class Version(models.Model):
    version = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return "Version('{}')".format(self.version)


class Session(models.Model):
    session_id = models.CharField(max_length=255, primary_key=True)
    dc_id = models.IntegerField()
    server_address = models.CharField(max_length=255)
    port = models.IntegerField()
    auth_key = models.BinaryField()

    def __str__(self):
        return "Session('{}', {}, '{}', {}, {})".format(self.session_id, self.dc_id,
                                                        self.server_address, self.port, self.auth_key)


class Entity(models.Model):
    id = models.BigIntegerField(primary_key=True)
    hash = models.BigIntegerField(null=False)
    username = models.CharField(max_length=32)
    phone = models.BigIntegerField()
    name = models.CharField(max_length=255)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return "Entity('{}', {}, {}, '{}', '{}', '{}')".format(self.session_id, self.id,
                                                               self.hash, self.username,
                                                               self.phone, self.name)


class SentFile(models.Model):
    session = models.OneToOneField(Session, primary_key=True, on_delete=models.CASCADE)
    md5_digest = models.BinaryField()
    file_size = models.IntegerField()
    type = models.IntegerField()
    id = models.BigIntegerField()
    hash = models.BigIntegerField()

    def __str__(self):
        return "SentFile('{}', {}, {}, {}, {}, {})".format(self.session_id,
                                                           self.md5_digest, self.file_size,
                                                           self.type, self.id, self.hash)


class UpdateState(models.Model):
    session = models.OneToOneField(Session, primary_key=True, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    pts = models.BigIntegerField()
    qts = models.BigIntegerField()
    date = models.BigIntegerField()
    seq = models.BigIntegerField()
    unread_count = models.IntegerField()
