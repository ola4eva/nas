import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting pre-migration for next_of_kin relationship field.")
    # Add a temporary column to store the old selection value
    cr.execute(
        "ALTER TABLE naseni_hr_next_of_kin ADD COLUMN relationship_selection_tmp VARCHAR;"
    )
    # Copy the old selection value into the temp column
    cr.execute(
        "UPDATE naseni_hr_next_of_kin SET relationship_selection_tmp = relationship;"
    )
    _logger.info(
        "Pre-migration completed: relationship_selection_tmp column created and populated."
    )
