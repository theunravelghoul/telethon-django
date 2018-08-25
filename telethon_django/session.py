import datetime

from telethon import utils
from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.sessions.memory import _SentFileType
from telethon.tl.types import updates, PeerUser, PeerChat, PeerChannel, InputDocument, InputPhoto

from telethon_django import models


class DjangoSession(MemorySession):
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self._load_session()

    def _load_session(self):
        session = models.Session.objects.filter(session_id=self.session_id).first()
        if session:
            self._dc_id = session.dc_id
            self._server_address = session.server_address
            self._port = session.port
            self._auth_key = AuthKey(session.auth_key.tobytes())

    def clone(self, to_instance=None):
        return super().clone(MemorySession())

    def set_dc(self, dc_id, server_address, port):
        super().set_dc(dc_id, server_address, port)
        self._update_session_table()

        session = models.Session.objects.filter(session_id=self.session_id).first()
        if session and session.auth_key:
            self._auth_key = AuthKey(data=session.auth_key.tobytes())
        else:
            self._auth_key = None

    def _update_session_table(self):
        models.Session.objects.filter(session_id=self.session_id).delete()
        session = models.Session.objects.create(session_id=self.session_id, dc_id=self._dc_id,
                                                server_address=self._server_address, port=self._port,
                                                auth_key=self._auth_key.key if self.auth_key else b'')
        session.save()

    def get_update_state(self, entity_id):
        row = models.UpdateState.objects.filter(session_id=self.session_id, entity_id=entity_id).first()
        if row:
            row.date = datetime.datetime.utcfromtimestamp(row.date)
            return updates.State(row.pts, row.qts, row.date, row.seq, row.unread_count)

    def set_update_state(self, entity_id, state):
        if state:
            updated_state, created = models.UpdateState.objects.get_or_create(session_id=self.session_id,
                                                                              entity_id=entity_id,
                                                                              pts=state.pts, qts=state.qts,
                                                                              date=state.date.timestamp(),
                                                                              seq=state.seq,
                                                                              unread_count=state.unread_count)
            updated_state.save()

    @MemorySession.auth_key.setter
    def auth_key(self, value):
        self._auth_key = value
        self._update_session_table()

    def close(self):
        pass

    def save(self):
        self._update_session_table()

    def delete(self):
        models.Session.objects.filter(session_id=self.session_id).delete()

    def _entity_values_to_row(self, id, hash, username, phone, name):
        return models.Entity(session_id=self.session_id, id=id, hash=hash,
                             username=username, phone=phone, name=name)

    def get_entity_rows_by_phone(self, key):
        row = models.Entity.objects.filter(phone=key).first()
        return (row.id, row.hash) if row else None

    def get_entity_rows_by_username(self, key):
        row = models.Entity.objects.filter(username=key).first()
        return (row.id, row.hash) if row else None

    def get_entity_rows_by_name(self, key):
        row = models.Entity.objects.filter(name=key).first()
        return (row.id, row.hash) if row else None

    def get_entity_rows_by_id(self, key, exact=True):
        if exact:
            row = models.Entity.objects.filter(id=key).first()
        else:
            ids = (
                utils.get_peer_id(PeerUser(key)),
                utils.get_peer_id(PeerChat(key)),
                utils.get_peer_id(PeerChannel(key))
            )
            row = models.Entity.objects.filter(id__in=ids).first()

        return (row.id, row.hash) if row else None

    def process_entities(self, tlo):
        rows = self._entities_to_rows(tlo)
        if not rows:
            return

        for row in rows:
            row.save()

    def cache_file(self, md5_digest, file_size, instance):
        if not isinstance(instance, (InputDocument, InputPhoto)):
            raise TypeError("Cannot cache {} instance".format(type(instance)))
        senf_file = models.SentFile(session_id=self.session_id, md5_digest=md5_digest,
                                    type=_SentFileType.from_type(type(instance)).value,
                                    id=instance.id, hash=instance.access_hash)
        senf_file.save()
        self.save()

    def get_file(self, md5_digest, file_size, cls):
        row = models.SentFile.objects.filter(md5_digest=md5_digest, file_size=file_size,
                                             type=_SentFileType.from_type(cls).value).first()
        return (row.id, row.hash) if row else None
