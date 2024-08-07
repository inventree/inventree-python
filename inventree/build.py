# -*- coding: utf-8 -*-

import inventree.base
import inventree.report


class Build(
    inventree.base.AttachmentMixin,
    inventree.base.StatusMixin,
    inventree.base.MetadataMixin,
    inventree.report.ReportPrintingMixin,
    inventree.base.InventreeObject,
):
    """ Class representing the Build database model """

    URL = 'build'
    MODEL_TYPE = 'build'

    def issue(self):
        """Mark this build as 'issued'."""
        return self._statusupdate(status='issue')
    
    def hold(self):
        """Mark this build as 'on hold'."""
        return self._statusupdate(status='hold')

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
