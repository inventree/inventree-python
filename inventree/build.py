# -*- coding: utf-8 -*-

import inventree.base


class Build(inventree.base.InventreeObject):
    """ Class representing the Build database model """

    URL = 'build'

    def getAttachments(self):
        return BuildAttachment.list(self._api, build=self.pk)
    
    def uploadAttachment(self, attachment, comment=''):
        return BuildAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            build=self.pk
        )


class BuildAttachment(inventree.base.Attachment):
    """Class representing an attachment against a Build object"""

    URL = 'build/attachment'
    REQUIRED_KWARGS = ['build']
