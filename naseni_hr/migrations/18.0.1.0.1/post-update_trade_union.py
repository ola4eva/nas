# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting post-migration for next_of_kin trade_union field.")

    # 1. Update next_of_kin records to point to the new Many2one record
    cr.execute(
        """
        UPDATE hr_employee
        SET trade_union = trade_union_tmp
        WHERE trade_union_tmp IS NOT NULL
    """
    )

    # 4. Drop the temporary column
    cr.execute(
        "ALTER TABLE hr_employee DROP COLUMN trade_union_tmp;"
    )
    _logger.info(
        "Post-migration completed: trade_union field migrated to Many2one, old selection field and temp column dropped, ir.model.fields reference removed."
    )
