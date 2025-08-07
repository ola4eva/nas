import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting pre-migration for trade_union relationship field.")
    # Add a temporary column to store the old selection value
    cr.execute(
        "ALTER TABLE hr_employee ADD COLUMN trade_union_tmp VARCHAR;"
    )
    # Copy the old selection value into the temp column
    cr.execute(
        "UPDATE hr_employee SET trade_union_tmp = trade_union;"
    )
    _logger.info(
        "Pre-migration completed: trade_union_tmp column created and populated."
    )
