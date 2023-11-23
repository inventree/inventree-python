# -*- coding: utf-8 -*-

import inventree.base
import inventree.report


class Build(
    inventree.base.InventreeObject,
    inventree.base.StatusMixin,
    inventree.base.MetadataMixin,
    inventree.report.ReportPrintingMixin,
):
    """ Class representing the Build database model """

    URL = 'build'

    # Setup for Report mixin
    REPORTNAME = 'build'
    REPORTITEM = 'build'

    def getAttachments(self):
        return BuildAttachment.list(self._api, build=self.pk)

    def uploadAttachment(self, attachment, comment=''):
        return BuildAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            build=self.pk
        )

    def complete(
        self,
        accept_overallocated='reject',
        accept_unallocated=False,
        accept_incomplete=False,
    ):
        """Finish a build order. Takes the following flags:
        - accept_overallocated
        - accept_unallocated
        - accept_incomplete
        """
        return self._statusupdate(
            status='finish',
            data={
                'accept_overallocated': accept_overallocated,
                'accept_unallocated': accept_unallocated,
                'accept_incomplete': accept_incomplete,
            }
        )

    def finish(self, *args, **kwargs):
        """Alias for complete"""
        return self.complete(*args, **kwargs)


class BuildAttachment(inventree.base.Attachment):
    """Class representing an attachment against a Build object"""

    URL = 'build/attachment'
    REQUIRED_KWARGS = ['build']
