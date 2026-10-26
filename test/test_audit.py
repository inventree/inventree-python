"""Unit tests for the AuditLog model"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.base import AuditLog  # noqa: E402
from inventree.company import Company  # noqa: E402
from inventree.part import Part  # noqa: E402
from inventree.project_code import ProjectCode  # noqa: E402
from inventree.stock import StockItem, StockItemTracking  # noqa: E402


class AuditLogTest(InvenTreeTestCase):
    """Tests for the AuditLog model."""

    def test_api_version(self):
        """Test that the AuditLog model is unavailable for older API versions."""

        if self.api.api_version >= AuditLog.MIN_API_VERSION:
            return

        with self.assertRaises(NotImplementedError):
            AuditLog.list(self.api)

    def test_audit_list(self):
        """Test that we can list audit log entries."""

        if self.api.api_version < AuditLog.MIN_API_VERSION:
            return

        entries = AuditLog.list(self.api, limit=10)

        self.assertGreater(len(entries), 0)

        for entry in entries:
            self.assertIsNotNone(entry.pk)
            self.assertIsNotNone(entry.timestamp)
            self.assertIsNotNone(entry.action)

        # Reload an individual entry from the detail endpoint
        entry = AuditLog(self.api, pk=entries[0].pk)
        self.assertEqual(entry.timestamp, entries[0].timestamp)

    def test_model_audit_log(self):
        """Test that the audit log is available for audited model instances."""

        if self.api.api_version < AuditLog.MIN_API_VERSION:
            return

        # Make a change to an audited model, to ensure there is an audit entry
        if codes := ProjectCode.list(self.api, limit=1):
            code = codes[0]
        else:
            code = ProjectCode.create(self.api, {
                'code': 'AUDIT',
                'description': 'Audit log test',
            })

        n = len(code.getAuditLog())

        code.save(data={'description': f'Audit log test {n}'})

        entries = code.getAuditLog()
        self.assertGreater(len(entries), n)

        # Check the audit log for a selection of model types
        for instance in [
            code,
            Part.list(self.api, limit=1)[0],
            Company.list(self.api, limit=1)[0],
        ]:
            suffix = f'.{instance.getModelType()}'

            # Entries for this model instance only
            own = instance.getAuditLog(include_children=False)

            for entry in own:
                self.assertIsInstance(entry, AuditLog)
                self.assertTrue(entry.model_type.endswith(suffix))
                self.assertEqual(str(entry.object_pk), str(instance.pk))

            # By default, entries for child objects are also included
            entries = instance.getAuditLog()

            self.assertGreaterEqual(len(entries), len(own))

            for entry in entries:
                self.assertIsInstance(entry, AuditLog)

                if entry.model_type.endswith(suffix) and str(entry.object_pk) == str(instance.pk):
                    continue

                # Otherwise, this must be an entry for a child object
                self.assertTrue(entry.parent_model_type.endswith(suffix))
                self.assertEqual(str(entry.parent_object_pk), str(instance.pk))

    def test_stock_item_history(self):
        """Test that stock item history is available via the audit log."""

        # Stock item history is recorded in the audit log from API version 566
        if self.api.api_version <= StockItemTracking.MAX_API_VERSION:
            return

        item = StockItem.list(self.api, in_stock=True, limit=1)[0]

        n = len(item.getAuditLog())

        item.addStock(10, notes='Audit log test')
        item.removeStock(10)

        entries = item.getAuditLog()

        self.assertGreater(len(entries), n)

        for entry in entries:
            self.assertIsInstance(entry, AuditLog)
            self.assertEqual(entry.model_type, 'stock.stockitem')
            self.assertEqual(str(entry.object_pk), str(item.pk))

        # Legacy tracking entries are provided via the audit log
        self.assertEqual(
            [e.pk for e in item.getTrackingEntries()],
            [e.pk for e in entries],
        )

        # Filter by event type
        events = AuditLog.listForModel(
            self.api, 'stockitem',
            model_id=item.pk,
            event_type=entries[0].event_type,
        )

        self.assertGreater(len(events), 0)

        for event in events:
            self.assertEqual(event.event_type, entries[0].event_type)

        # The legacy tracking endpoint is no longer available
        with self.assertRaises(NotImplementedError):
            StockItemTracking.list(self.api, item=item.pk)
