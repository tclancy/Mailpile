## Dear hackers!
##
## It would be great to have more mailbox classes.  They should be derived
## from or implement the same interfaces as Python's native mailboxes, with
## the additional constraint that they support pickling and unpickling using
## cPickle.  The mailbox class is also responsible for generating and parsing
## a "pointer" which should be a short as possible while still encoding the
## info required to locate this message and this message only within the
## larger mailbox.

from urllib import quote, unquote
from gettext import gettext as _


__all__ = ['mbox', 'maildir', 'gmvault', 'imap', 'macmail', 'wervd',
           'MBX_ID_LEN',
           'NoSuchMailboxError', 'IsMailbox', 'OpenMailbox']

MAILBOX_CLASSES = []

MBX_ID_LEN = 4  # 4x36 == 1.6 million mailboxes


class NoSuchMailboxError(OSError):
    pass


def register(prio, cls):
    global MAILBOX_CLASSES
    MAILBOX_CLASSES.append((prio, cls))
    MAILBOX_CLASSES.sort()


def IsMailbox(fn, config):
    for pri, mbox_cls in MAILBOX_CLASSES:
        try:
            if mbox_cls.parse_path(config, fn):
                return True
        except KeyboardInterrupt:
            raise
        except:
            pass
    return False


def OpenMailbox(fn, config, create=False):
    for pri, mbox_cls in MAILBOX_CLASSES:
        try:
            return mbox_cls(*mbox_cls.parse_path(config, fn, create=create))
        except KeyboardInterrupt:
            raise
        except:
            pass
    raise ValueError('Not a mailbox: %s' % fn)


def UnorderedPicklable(parent, editable=False):
    """A factory for generating unordered, picklable mailbox classes."""

    class UnorderedPicklableMailbox(parent):
        def __init__(self, *args, **kwargs):
            parent.__init__(self, *args, **kwargs)
            self.editable = editable
            self._save_to = None
            self._encryption_key_func = lambda: None

        def __setstate__(self, data):
            self.__dict__.update(data)
            self._save_to = None
            self._encryption_key_func = lambda: None
            self.update_toc()

        def __getstate__(self):
            odict = self.__dict__.copy()
            # Pickle can't handle function objects.
            for dk in ('_save_to', '_encryption_key_func',
                       '_file', '_lock', 'parsed'):
                if dk in odict:
                    del odict[dk]
            return odict

        def save(self, session=None, to=None, pickler=None):
            if to and pickler:
                self._save_to = (pickler, to)
            if self._save_to and len(self) > 0:
                pickler, fn = self._save_to
                if session:
                    session.ui.mark(_('Saving %s state to %s') % (self, fn))
                pickler(self, fn)

        def update_toc(self):
            self._refresh()

        def get_msg_ptr(self, mboxid, toc_id):
            return '%s%s' % (mboxid, quote(toc_id))

        def get_file_by_ptr(self, msg_ptr):
            return self.get_file(unquote(msg_ptr[MBX_ID_LEN:]))

        def get_msg_size(self, toc_id):
            fd = self.get_file(toc_id)
            fd.seek(0, 2)
            return fd.tell()

    return UnorderedPicklableMailbox
